

import os

# ─────────────────────────────────────────────
# Output paths
# ─────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR      = os.path.join(BASE_DIR, "output")
IMAGE_DIR       = os.path.join(OUTPUT_DIR, "images")
VEG_DIR         = os.path.join(IMAGE_DIR, "veg")
NON_VEG_DIR     = os.path.join(IMAGE_DIR, "non_veg")
CSV_FILE        = os.path.join(OUTPUT_DIR, "food_data.csv")


# Target websites  (add / remove freely)



# ─────────────────────────────────────────────
# HTTP settings
# ─────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT  = 50       # seconds per request
RETRY_ATTEMPTS   = 5
RETRY_BACKOFF    = 2.0       # seconds (doubles each retry)
DELAY_BETWEEN_REQUESTS = 1.5 # polite crawl delay (seconds)

# ─────────────────────────────────────────────
# Image download
# ─────────────────────────────────────────────
MIN_IMAGE_SIZE_BYTES = 2_000   # skip tiny icons / placeholders
ALLOWED_EXTENSIONS   = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILENAME_LENGTH  = 100

# ─────────────────────────────────────────────
# Veg / Non-veg keyword classification
# ─────────────────────────────────────────────
NON_VEG_KEYWORDS = {
    # Arabic
    "لحم", "دجاج", "سمك", "لحوم", "ريش", "كباب", "شاورما",
    "مندي", "ماعز", "خروف", "حمام", "ديك", "جمبري", "روبيان",
    "بيض", "مرق لحم", "دماغ", "كبد", "كبدة",
    # English transliterations / labels
    "chicken", "meat", "beef", "lamb", "fish", "shrimp", "prawn",
    "mutton", "turkey", "tuna", "salmon", "kabab", "shawarma",
    "mandi", "kofta", "biryani with meat", "liver",
}

VEG_KEYWORDS = {
    # Arabic
    "خضار", "خضروات", "فطر", "عدس", "حمص", "فول", "باذنجان",
    "كوسا", "جزر", "بطاطا", "بصل", "ثوم", "سبانخ", "ملوخية",
    "فلفل", "طماطم", "تمر", "فاكهة", "فاكهه", "حلوى", "كيكة",
    "عجين", "خبز", "أرز بدون لحم",
    # English
    "vegetable", "salad", "lentil", "chickpea", "mushroom", "tofu",
    "vegan", "falafel", "hummus", "tabbouleh", "fattoush",
    "eggplant", "zucchini", "potato", "spinach", "tomato",
    "rice", "bread", "cake", "dessert", "sweet", "fruit",
}
