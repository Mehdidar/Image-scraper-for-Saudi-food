"""
parser.py
=========
HTML parsing helpers built on BeautifulSoup4.
Each function is stateless and operates on a pre-fetched BeautifulSoup object.
"""

import re
from typing import Optional
from urllib.parse import urlparse

# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup, Tag

from utils import resolve_url, setup_logger

logger = setup_logger()


# ─────────────────────────────────────────────
# Page-level parsing
# ─────────────────────────────────────────────

def make_soup(html: str) -> BeautifulSoup:
    """Parse raw HTML with lxml (fastest) falling back to html.parser."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def extract_article_links(
    soup: BeautifulSoup,
    base_url: str,
    css_selector: str,
    url_pattern: str = "",
    url_exclude: str = "",
) -> list[str]:
    """
    Find all anchor tags matching *css_selector* and return a deduplicated
    list of resolved absolute URLs.

    If *url_pattern* is provided (regex string), only URLs matching it are kept.
    If *url_exclude* is provided (regex string), URLs matching it are dropped.
    """
    links: list[str] = []
    seen: set[str] = set()

    pat     = re.compile(url_pattern)   if url_pattern else None
    exclude = re.compile(url_exclude)   if url_exclude else None

    for tag in soup.select(css_selector):
        href = tag.get("href", "")
        full = resolve_url(base_url, href)
        if not full or full in seen:
            continue
        if pat and not pat.search(full):
            continue
        if exclude and exclude.search(full):
            continue
        seen.add(full)
        links.append(full)

    return links


def extract_next_page(soup: BeautifulSoup, base_url: str, css_selector: str) -> Optional[str]:
    """Return the URL of the next pagination page, or None."""
    for selector in css_selector.split(","):
        tag = soup.select_one(selector.strip())
        if tag:
            href = tag.get("href", "")
            nxt  = resolve_url(base_url, href)
            if nxt and nxt != base_url:
                return nxt
    return None


# ─────────────────────────────────────────────
# Article-level parsing
# ─────────────────────────────────────────────

def extract_title(soup: BeautifulSoup, selectors: list[str]) -> Optional[str]:
    """
    Try each CSS selector in order and return the first non-empty text found.
    """
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag:
            text = tag.get_text(separator=" ", strip=True)
            if text:
                return text
    # Absolute fallback: <title> tag
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return None


def extract_image_url(
    soup: BeautifulSoup,
    selectors: list[str],
    page_url: str,
) -> Optional[str]:
    """
    Try each CSS selector for an <img> or element with src/data-src.
    Returns the first valid absolute image URL found.
    """
    candidates: list[str] = []

    for selector in selectors:
        tags = soup.select(selector)
        for tag in tags:
            for attr in ("src", "data-src", "data-lazy-src", "data-original"):
                val = tag.get(attr, "").strip()
                if val:
                    candidates.append(val)

    # Also search Open Graph image meta tag
    og = soup.find("meta", property="og:image")
    if og:
        candidates.insert(0, og.get("content", ""))

    # Twitter card image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw:
        candidates.insert(0, tw.get("content", ""))

    for href in candidates:
        full = resolve_url(page_url, href)
        if full and _looks_like_content_image(full):
            return full

    return None


# ─────────────────────────────────────────────
# Heuristics
# ─────────────────────────────────────────────

_SKIP_PATTERNS = (
    "logo", "icon", "favicon", "banner", "avatar",
    "sprite", "pixel", "placeholder", "spacer", "1x1",
    "ad-", "-ad.", "advertisement",
)


def _looks_like_content_image(url: str) -> bool:
    """Heuristic: return False for known non-content image patterns."""
    lower = url.lower()
    return not any(pat in lower for pat in _SKIP_PATTERNS)
