import os
import csv
import json
import threading
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify

# Import scraper modules
from scraper import SiteScraper
from config import CSV_FILE
from storage import count_records
from utils import DeduplicationSet

app = Flask(__name__)

STATS_FILE = "output/stats.json"

def get_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"visited_sites": 0, "total_images": 0}

def save_stats(stats):
    os.makedirs("output", exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def update_total_images():
    """Reads the CSV file to find the actual number of extracted images and category breakdown."""
    csv_path = CSV_FILE
    if os.path.exists(csv_path):
        try:
            total = 0
            veg = 0
            non_veg = 0
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += 1
                    cat = row.get("category", "")
                    if cat == "veg":
                        veg += 1
                    elif cat == "non_veg":
                        non_veg += 1
                
            stats = get_stats()
            stats["total_images"] = total
            stats["veg_images"] = veg
            stats["non_veg_images"] = non_veg
            save_stats(stats)
        except Exception:
            pass

is_scraping = False

@app.route("/")
def index():
    # Making  sure total images is up-to-date on initial load
    update_total_images()
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    update_total_images()
    data = get_stats()
    data["is_scraping"] = is_scraping
    return jsonify(data)

def background_scrape(url):
    global is_scraping
    is_scraping = True
    try:
        domain = urlparse(url).netloc
        
        # Update sites visited right away
        stats = get_stats()
        stats["visited_sites"] += 1
        save_stats(stats)
        
        # Generic configuration for a user-submitted URL
        generic_site = {
            "name": domain,
            "base_url": f"https://{domain}",
            "start_urls": [url],
            "max_pages": 100,  # Crawl up to 50 pages deep
            
            # STRICTURE: Ensure we only scrape links belonging to the domain and having a path
            "url_pattern": rf"{domain}/.+",
            
            # STRICTURE: Exclude non-article links, UI links, and pagination
            "url_exclude": r"(?i)/category/|/tag/|/author/|/page/|/about|/contact|/privacy|/policy|/subscribe|/cart|#|share=",
            
            "selectors": {
                # Focus on main content areas to avoid footer/header links
                "article_links": "main a, article a, .post a, .content a, .entry a, #content a, .recipe a",
                
                # Demand an h1 for the title (to avoid picking up sidebar widget titles)
                "title":  ["h1.entry-title", "h1.post-title", "h1", ".recipe-title"],
                
                # Avoid blindly grabbing any 'img' (which picks up logos).
                # The parser will automatically fall back to og:image and twitter:image anyway, 
                # which are usually the correct recipe thumbnails!
                "image":  ["img.wp-post-image", ".post-thumbnail img", "article img", "main img", ".recipe img"],
                
                # Generic fallback selectors for pagination buttons
                "next_page": "a.next, a[rel='next'], a[class*='next'], .nav-next a, .next-page a",
            }
        }
        
        # Initialize components
        url_dedup = DeduplicationSet()
        img_dedup = DeduplicationSet()
        scraper = SiteScraper(generic_site, url_dedup, img_dedup)
        
        # Run a full deep crawl (page by page) instead of just one article
        scraper.run()
        
        # Update total images
        update_total_images()
    finally:
        is_scraping = False

@app.route("/api/scrape", methods=["POST"])
def scrape():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    # Run the scraping task in a background thread to keep UI responsive
    thread = threading.Thread(target=background_scrape, args=(url,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Background extraction initiated successfully"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
