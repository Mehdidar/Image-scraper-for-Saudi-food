"""
downloader.py
=============
Downloads images from URLs to the local filesystem.
- Validates size (skips tiny icons)
- Infers correct file extension from Content-Type or URL
- Returns the local file path or None on failure
"""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from config import ALLOWED_EXTENSIONS, MIN_IMAGE_SIZE_BYTES
from http_client import fetch
from utils import sanitise_filename, setup_logger

logger = setup_logger()

# Map common MIME types to extensions
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png":  ".png",
    "image/webp": ".webp",
    "image/gif":  ".gif",
    "image/bmp":  ".bmp",
}


def _guess_extension(url: str, content_type: str) -> str:
    """Return the best file extension for an image."""
    # Try Content-Type header first
    mime = content_type.split(";")[0].strip().lower()
    if mime in MIME_TO_EXT:
        return MIME_TO_EXT[mime]
    # Fall back to URL extension
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in ALLOWED_EXTENSIONS else ".jpg"


def download_image(image_url: str, title: str, dest_dir: str) -> Optional[str]:
    """
    Download *image_url* to *dest_dir* with a filename derived from *title*.

    Returns the local file path on success, None on failure.
    """
    resp = fetch(image_url, stream=True)
    if resp is None:
        return None

    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        logger.debug("Skipping non-image Content-Type '%s' for %s", content_type, image_url)
        return None

    # Check size in memory (first chunk is enough for small files)
    data = resp.content
    if len(data) < MIN_IMAGE_SIZE_BYTES:
        logger.debug("Skipping tiny image (%d bytes): %s", len(data), image_url)
        return None

    ext      = _guess_extension(image_url, content_type)
    safe     = sanitise_filename(title)
    filename = f"{safe}{ext}"
    dest     = os.path.join(dest_dir, filename)

    # Avoid overwriting — append counter if needed
    counter = 1
    while os.path.exists(dest):
        dest = os.path.join(dest_dir, f"{safe}_{counter}{ext}")
        counter += 1

    try:
        os.makedirs(dest_dir, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        logger.debug("Saved image → %s", dest)
        return dest
    except OSError as exc:
        logger.error("Could not save image to %s: %s", dest, exc)
        return None
