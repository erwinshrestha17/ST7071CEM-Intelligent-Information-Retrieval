# backend/information_retrival/crawler.py

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Use relative imports for local modules
from .config import START_URL, BASE_URL, PUBLICATIONS_FILE, PROJECT_ROOT
import json
import logging
from urllib.parse import urljoin
import time
from pathlib import Path
from datetime import datetime
import re
import random

# --- Configuration ---
MAX_RETRIES = 2
MAX_PAGE_RETRIES = 3
CHECKPOINT_FILE = PROJECT_ROOT / "crawl_checkpoint.json"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Selectors (FINAL VERSION) ---
SELECTORS = {
    "cookie_accept_button": "#CybotCookiebotDialogBodyButtonAccept",
    "publication_link": "h3.title a",

    # FINAL FIX for PAGINATION: The correct selector is a link inside a list item with the class "next"
    "pagination_next": "li.next a",

    "detail_title": "div.rendering h1",

    # Author selectors are working well
    "detail_authors": [
        "p.relations.persons",
        "p.relations.authors",
        "a.link.person"
    ],

    "detail_year": ["span.date", ".publication-year"],

    "detail_abstract": ["div.textblock", ".abstract", "div.rendering_researchoutput_abstract"],

    # Keyword selector is correct for pages that have keywords
    "detail_keywords": ["ul.relations.keywords li a"]
}


def get_driver():
    """Initializes a robust undetected_chromedriver instance with a persistent profile."""
    options = uc.ChromeOptions()
    # options.add_argument('--headless=new') # Temporarily disabled for easier debugging
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/536.36')
    profile_path = PROJECT_ROOT / "chrome_profile"
    profile_path.mkdir(exist_ok=True)
    driver = uc.Chrome(options=options, user_data_dir=str(profile_path), use_subprocess=True)
    return driver


def extract_publication_details(driver, url):
    """Extracts details from a single publication page."""
    for attempt in range(MAX_RETRIES):
        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["detail_title"])))
            time.sleep(random.uniform(1.0, 2.0))
            title = driver.find_element(By.CSS_SELECTOR, SELECTORS["detail_title"]).text
            authors, publicationYear, abstract, keywords = [], None, None, []

            # --- Author Extraction ---
            for selector in SELECTORS["detail_authors"]:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    current_authors = [elem.text.strip() for elem in elements if elem.text.strip()]
                    if current_authors:
                        authors = current_authors
                        logging.info(f"Successfully extracted {len(authors)} authors using selector: '{selector}'")
                        break
                except:
                    continue
            if not authors:
                logging.warning(f"Could not extract any authors for URL: {url}")

            # --- Year Extraction ---
            for selector in SELECTORS["detail_year"]:
                try:
                    text = driver.find_element(By.CSS_SELECTOR, selector).text
                    match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
                    if match:
                        publicationYear = int(match.group(1));
                        break
                except:
                    continue

            # --- Abstract Extraction ---
            for selector in SELECTORS["detail_abstract"]:
                try:
                    abstract = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                    if abstract: break
                except:
                    continue

            # --- Keyword Extraction ---
            for selector in SELECTORS["detail_keywords"]:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    keywords = [elem.text.strip() for elem in elements if elem.text.strip()]
                    if keywords: break
                except:
                    continue

            return {"title": title, "publicationUrl": url, "authors": authors, "publicationYear": publicationYear,
                    "abstract": abstract, "keywords": keywords, "crawled_at": datetime.now().isoformat()}
        except Exception as e:
            logging.warning(f"Detail extraction attempt {attempt + 1} failed for {url}: {e}")
            if attempt >= MAX_RETRIES - 1:
                logging.error(f"Failed to extract details from {url} after {MAX_RETRIES} retries.");
                return None
            time.sleep(5)


def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {"visited_urls": set(data.get("visited_urls", [])), "publications": data.get("publications", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"visited_urls": set(), "publications": []}


def save_checkpoint(data):
    data_to_save = {"visited_urls": list(data["visited_urls"]), "publications": data["publications"]}
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, indent=4)
    logging.info(f"Progress saved. {len(data['publications'])} publications processed.")


def crawl_and_extract():
    logging.info("--- Initializing Crawler ---")
    checkpoint = load_checkpoint()
    all_publications = checkpoint["publications"]
    visited_urls = checkpoint["visited_urls"]
    driver = None
    try:
        driver = get_driver()
        current_url = START_URL
        while current_url:
            page_load_success = False
            for attempt in range(MAX_PAGE_RETRIES):
                try:
                    logging.info(f"Navigating to listing page: {current_url} (Attempt {attempt + 1})")
                    driver.get(current_url)

                    # Wait up to 15 seconds for the cookie banner and click if it appears
                    try:
                        logging.info("Checking for cookie consent banner...")
                        cookie_button = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["cookie_accept_button"]))
                        )
                        cookie_button.click()
                        logging.info("Cookie consent banner accepted.")
                        time.sleep(2)  # Give page time to adjust after click
                    except TimeoutException:
                        logging.info("Cookie consent banner not found or already accepted.")
                        pass  # It's okay if the banner isn't there

                    # Now, wait for the main content to be VISIBLE
                    logging.info("Waiting for publication links to become visible...")
                    WebDriverWait(driver, 60).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, SELECTORS["publication_link"]))
                    )

                    logging.info("Publication links are visible. Page loaded successfully.")
                    page_load_success = True
                    break  # Exit retry loop on success

                except TimeoutException:
                    logging.warning(
                        f"Timeout on page {current_url}, attempt {attempt + 1}. Taking screenshot and retrying...",
                        exc_info=False)
                    driver.save_screenshot(f"debug_screenshot_attempt_{attempt + 1}.png")
                    time.sleep(5)
                except Exception as e:
                    logging.error(f"An unexpected error occurred on page {current_url}: {e}")
                    driver.save_screenshot(f"debug_screenshot_error_{attempt + 1}.png")
                    time.sleep(5)

            if not page_load_success:
                logging.error(f"FATAL: Failed to load page {current_url} after {MAX_PAGE_RETRIES} attempts.")
                break

            time.sleep(random.uniform(2.0, 4.0))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links_on_page = [urljoin(BASE_URL, a['href']) for a in soup.select(SELECTORS["publication_link"]) if
                             a.has_attr('href')]
            new_links = [url for url in links_on_page if url not in visited_urls]
            logging.info(f"Found {len(links_on_page)} links, {len(new_links)} are new.")
            if new_links:
                for i, url in enumerate(new_links):
                    logging.info(
                        f"Processing new URL {i + 1}/{len(new_links)} ({len(all_publications) + 1} total): {url}")
                    details = extract_publication_details(driver, url)
                    if details:
                        all_publications.append(details)
                        visited_urls.add(url)
                save_checkpoint({"visited_urls": visited_urls, "publications": all_publications})

            # --- *** THE DEFINITIVE PAGINATION FIX V2 (JAVASCRIPT CLICK) *** ---
            try:
                logging.info("Looking for the 'Next' page link...")
                url_before_click = driver.current_url

                # First, wait for the element to at least be PRESENT in the HTML
                next_page_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["pagination_next"]))
                )
                logging.info("'Next' button found in the DOM.")

                # Now, use JavaScript to force the click. This is more reliable.
                logging.info("Executing click via JavaScript...")
                driver.execute_script("arguments[0].click();", next_page_button)

                logging.info("JavaScript click executed. Waiting for page URL to change...")

                # Wait up to 15 seconds for the URL to change, which confirms navigation
                WebDriverWait(driver, 15).until(EC.url_changes(url_before_click))

                current_url = driver.current_url
                logging.info(f"Successfully navigated to new page: {current_url}")

            except TimeoutException:
                logging.info("Pagination link not found or URL did not change after click. Assuming end of results.")
                driver.save_screenshot("debug_end_of_pagination.png")
                current_url = None
            except Exception as e:
                logging.error(f"An unexpected error occurred during pagination: {e}")
                driver.save_screenshot("debug_pagination_error.png")
                current_url = None
            # --- *** END OF FIX *** ---

        logging.info("Crawl of listing pages has finished.")
    finally:
        logging.info("--- Shutting Down ---")
        if driver: driver.quit()
        with open(PUBLICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_publications, f, indent=4, ensure_ascii=False)
        logging.info(f"Crawl finished. A total of {len(all_publications)} publications saved to {PUBLICATIONS_FILE}")


if __name__ == "__main__":
    crawl_and_extract()