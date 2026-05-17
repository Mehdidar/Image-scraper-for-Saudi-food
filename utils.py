"""
utils.py
========
Shared utility functions used across the scraper.
"""

import hashlib
import logging
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

from config import (
    ALLOWED_EXTENSIONS,
    MAX_FILENAME_LENGTH,
    NON_VEG_DIR,
    OUTPUT_DIR,
    VEG_DIR,
)

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────

def setup_logger(name: str = "ArabicFoodScraper") -> logging.Logger:
    """Configure and return a coloured console + file logger."""
    logger = logging.getLogger(name)
    if logger.handlers:          # already initialised
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(_ColourFormatter())

    # File handler — DEBUG and above
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fh = logging.FileHandler(os.path.join(OUTPUT_DIR, "scraper.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


class _ColourFormatter(logging.Formatter):
    """Terminal colour codes per log level."""
    GREY    = "\033[90m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"

    FORMATS = {
        logging.DEBUG:    GREY   + "%(asctime)s [DBG]  %(message)s" + RESET,
        logging.INFO:     CYAN   + "%(asctime)s [INFO] %(message)s" + RESET,
        logging.WARNING:  YELLOW + "%(asctime)s [WARN] %(message)s" + RESET,
        logging.ERROR:    RED    + "%(asctime)s [ERR]  %(message)s" + RESET,
        logging.CRITICAL: BOLD + RED + "%(asctime)s [CRIT] %(message)s" + RESET,
    }

    def format(self, record):
        fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


# ─────────────────────────────────────────────
# URL helpers
# ─────────────────────────────────────────────

def resolve_url(base: str, href: str) -> Optional[str]:
    """
    Turn any href (absolute, protocol-relative, or relative) into a full URL.
    Returns None if the result isn't a valid http(s) URL.
    """
    if not href or href.startswith("data:"):
        return None
    url = urljoin(base, href.strip())
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    return url


def is_valid_image_url(url: str) -> bool:
    """Return True if the URL looks like a real image (by extension or path)."""
    if not url:
        return False
    path = urlparse(url).path.lower()
    ext  = Path(path).suffix
    if ext in ALLOWED_EXTENSIONS:
        return True
    # Some CDNs serve images without extensions — accept them cautiously
    if any(token in url.lower() for token in ("image", "photo", "img", "thumb", "media")):
        return True
    return False


# ─────────────────────────────────────────────
# Filename / text sanitisation
# ─────────────────────────────────────────────

def sanitise_filename(text: str, max_len: int = MAX_FILENAME_LENGTH) -> str:
    """
    Convert arbitrary Unicode text into a safe ASCII filename component.
    Arabic characters are transliterated naïvely then stripped to alphanumerics.
    """
    # Normalise Unicode (NFC)
    text = unicodedata.normalize("NFC", text)
    # Replace whitespace / separators
    text = re.sub(r"[\s/\\:*?\"<>|]+", "_", text)
    # Remove characters that are not word chars or underscores/hyphens
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    # Collapse multiple underscores
    text = re.sub(r"_+", "_", text).strip("_")
    # Truncate
    return text[:max_len] if text else "unnamed"


def clean_title(raw: str) -> str:
    """Strip whitespace and common boilerplate from scraped titles."""
    text = raw.strip()
    # Remove common Arabic/English noise suffixes
    noise = [
        r"\|.*$", r"–.*$", r"-\s*recipe.*$", r"وصفة.*$", r"طريقة عمل.*",
    ]
    for pattern in noise:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return text or raw.strip()


# ─────────────────────────────────────────────
# Deduplication
# ─────────────────────────────────────────────

class DeduplicationSet:
    """Thread-safe (enough for single-threaded crawl) in-memory seen-URL set."""

    def __init__(self):
        self._seen: set[str] = set()

    def _key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def is_new(self, url: str) -> bool:
        """Return True and mark seen; return False if already seen."""
        key = self._key(url)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def __len__(self):
        return len(self._seen)


# ─────────────────────────────────────────────
# Folder setup
# ─────────────────────────────────────────────

def ensure_output_dirs():
    """Create all required output directories."""
    for d in (VEG_DIR, NON_VEG_DIR):
        os.makedirs(d, exist_ok=True)
