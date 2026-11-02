Arabic Food Image Scraper

A Python scraper to build an Arabic food image dataset. It crawls target food blogs, downloads recipe images, automatically classifies them as vegetarian or non-vegetarian using keyword matching, and saves everything to a CSV file.

It also comes with a web-based dashboard (Flask app) to monitor scraping progress, start scrapes, and view live statistics.

Project Structure

WEB IMAGE SCRAPER/
├── main.py           # CLI entry point to run scrapers manually
├── app.py            # Flask app for the web dashboard interface
├── scraper.py        # Core crawl and pagination logic
├── parser.py         # BeautifulSoup HTML parsing logic
├── downloader.py     # Image downloading, validation, and saving
├── classifier.py     # Veg / non-veg keyword categorization
├── http_client.py    # Request session, retries, and headers
├── storage.py        # Appends results to a CSV file
├── utils.py          # Helper functions (logging, dedup, filename cleaning)
├── config.py         # Scraper configs, selectors, and keywords
├── requirements.txt  # Python packages
└── output/           # Scraped data, logs, and downloaded images

Getting Started

1. Set up a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate  # on Windows use: .venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Run the application:
   python main.py

Then open http://localhost:5001 in your browser.

If you want to run the crawler via CLI instead of the web dashboard:
- Run all configured sites: python main.py
- Run specific sites only: python main.py --sites Fatafeat Madfoon
- Limit crawled pages per site: python main.py --max-pages 2

 Settings and Customization

All configurations are handled inside config.py:
- Target Sites: You can add new websites to the TARGET_SITES list. Just define their URLs and the HTML CSS selectors they use for recipe links, titles, images, and next-page pagination.
- Keywords: Adjust VEG_KEYWORDS and NON_VEG_KEYWORDS to fine-tune how recipes are categorized. It supports both Arabic and English text.

Features

- Keeps track of visited links and image hashes to avoid duplicate downloads.
- Randomly rotates User-Agent headers and uses a small delay between requests to avoid getting blocked.
- Retries failed requests automatically.
- Sanitizes image filenames, filters out small images (like tracking pixels under 5KB), and falls back to social meta tags (og:image) if a primary article image isn't found.
- Saves data to output/food_data.csv with UTF-8 BOM encoding so Arabic text displays correctly in Excel.

License

Released under the MIT License (see LICENSE).
