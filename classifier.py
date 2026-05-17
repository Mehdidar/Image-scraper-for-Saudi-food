"""
classifier.py
=============
Classifies a food item as 'veg' or 'non_veg' based on keyword matching
against the food title (supports both Arabic and English text).
"""

from config import NON_VEG_KEYWORDS, VEG_KEYWORDS


def classify(title: str) -> str:
    """
    Return 'non_veg' or 'veg'.

    Priority: non_veg wins if any non-veg keyword is present.
    Falls back to 'veg' if veg keywords found or no match (benefit of doubt).
    """
    lower = title.lower()

    for kw in NON_VEG_KEYWORDS:
        if kw in lower:
            return "non_veg"

    for kw in VEG_KEYWORDS:
        if kw in lower:
            return "veg"

    # Default: assume vegetarian when uncertain
    return "veg"


def destination_dir(category: str, veg_dir: str, non_veg_dir: str) -> str:
    """Return the correct download directory for a given category."""
    return non_veg_dir if category == "non_veg" else veg_dir
