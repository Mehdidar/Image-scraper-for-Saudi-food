"""
scraper.py
==========
Core scraping engine.

Flow per site:
  listing page → article links → article page → title + image
                                              → classify → download → CSV
"""

from typing import Optional

from classifier import classify, destination_dir
from config import NON_VEG_DIR, VEG_DIR
from downloader import download_image
from http_client import fetch
from parser import (
    extract_article_links,
    extract_image_url,
    extract_next_page,
    extract_title,
    make_soup,
)
from storage import FoodRecord, append_record
from utils import DeduplicationSet, clean_title, is_valid_image_url, setup_logger

logger = setup_logger()


class SiteScraper:
    """
    Scrapes a single configured website end-to-end.
    Instantiate once per site dict from config.TARGET_SITES.
    """

    def __init__(self, site: dict, url_dedup: DeduplicationSet, img_dedup: DeduplicationSet):
        self.site      = site
        self.name      = site["name"]
        self.base_url  = site["base_url"]
        self.sel       = site["selectors"]
        self.max_pages = site.get("max_pages", 3)
        self.url_dedup = url_dedup
        self.img_dedup = img_dedup
        self.saved     = 0
        self.skipped   = 0
        self.failed    = 0

    # ── Public entry point ──────────────────────────────────────────────

    def run(self) -> dict:
        """Crawl this site and return a summary dict."""
        logger.info("━" * 60)
        logger.info("▶  Starting: %s  (%s)", self.name, self.base_url)
        logger.info("━" * 60)

        for start_url in self.site["start_urls"]:
            self._crawl_listing(start_url)

        summary = {
            "site":    self.name,
            "saved":   self.saved,
            "skipped": self.skipped,
            "failed":  self.failed,
        }
        logger.info(
            "✔  Done: %s | saved=%d  skipped=%d  failed=%d",
            self.name, self.saved, self.skipped, self.failed,
        )
        return summary

    # ── Listing page crawler ────────────────────────────────────────────

    def _crawl_listing(self, start_url: str):
        current_url: Optional[str] = start_url
        page_num = 0
        url_pattern = self.site.get("url_pattern", "")
        url_exclude  = self.site.get("url_exclude", "")

        while current_url and page_num < self.max_pages:
            page_num += 1
            logger.info("[%s] Listing page %d/%d → %s", self.name, page_num, self.max_pages, current_url)

            resp = fetch(current_url)
            if resp is None:
                logger.warning("[%s] Failed to fetch listing page: %s", self.name, current_url)
                break

            soup  = make_soup(resp.text)
            links = extract_article_links(
                soup, self.base_url, self.sel["article_links"],
                url_pattern=url_pattern,
                url_exclude=url_exclude,
            )
            logger.info("[%s] Found %d article links on page %d", self.name, len(links), page_num)

            for link in links:
                self._process_article(link)

            current_url = extract_next_page(soup, self.base_url, self.sel["next_page"])

    # ── Article processor ───────────────────────────────────────────────

    def _process_article(self, article_url: str):
        # Dedup by URL
        if not self.url_dedup.is_new(article_url):
            self.skipped += 1
            logger.debug("Skip (seen URL): %s", article_url)
            return

        resp = fetch(article_url)
        if resp is None:
            self.failed += 1
            return

        soup  = make_soup(resp.text)
        title = self._get_title(soup)
        if not title:
            logger.debug("No title found: %s", article_url)
            self.failed += 1
            return

        image_url = extract_image_url(soup, self.sel["image"], article_url)
        if not image_url or not is_valid_image_url(image_url):
            logger.debug("No valid image found for '%s'", title)
            self.failed += 1
            return

        # Dedup by image URL
        if not self.img_dedup.is_new(image_url):
            self.skipped += 1
            logger.debug("Skip (seen image): %s", image_url)
            return

        category = classify(title)
        dest     = destination_dir(category, VEG_DIR, NON_VEG_DIR)
        img_path = download_image(image_url, title, dest)

        if img_path is None:
            self.failed += 1
            return

        record = FoodRecord(
            title      = title,
            image_url  = image_url,
            image_path = img_path,
            category   = category,
            source_url = article_url,
        )
        append_record(record)
        self.saved += 1

        label = "🥗 VEG" if category == "veg" else "🍖 NON-VEG"
        logger.info("  ✓ [%s] %s  →  %s", label, title[:60], img_path.split("/")[-1])

    # ── Helpers ─────────────────────────────────────────────────────────

    def _get_title(self, soup) -> Optional[str]:
        raw = extract_title(soup, self.sel["title"])
        return clean_title(raw) if raw else None
