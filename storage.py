"""
storage.py
==========
Handles CSV persistence for scraped food data.
- Thread-safe write (single-threaded design, but header guard is safe)
- Writes UTF-8 BOM so Excel opens Arabic text correctly
"""

import csv
import os
from dataclasses import asdict, dataclass
from typing import Optional

from config import CSV_FILE
from utils import setup_logger

logger = setup_logger()

CSV_FIELDS = ["title", "image_url", "image_path", "category", "source_url"]


@dataclass
class FoodRecord:
    title:       str
    image_url:   str
    image_path:  str
    category:    str          # 'veg' or 'non_veg'
    source_url:  str


def init_csv():
    """Create the CSV file with headers if it doesn't exist yet."""
    if not os.path.exists(CSV_FILE):
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
        logger.info("CSV file created at %s", CSV_FILE)


def append_record(record: FoodRecord):
    """Append a single FoodRecord row to the CSV."""
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(asdict(record))


def count_records() -> int:
    """Return the number of data rows currently in the CSV."""
    if not os.path.exists(CSV_FILE):
        return 0
    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in f) - 1)  # subtract header
