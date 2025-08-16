# backend/crawler.py

import json
import logging
from urllib.parse import urljoin
import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.information_retrival.config import START_URL, BASE_URL, PUBLICATIONS_FILE

# Import configuration from the config module


# Centralize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Selectors for listing pages and detail pages
SELECTORS = {
    "publication_link": "h3.title a",
    "pagination_next": "a.next",
    # --- Selectors for the publication detail page (these are educated guesses) ---
    "detail_title": "div.rendering h1",
    "detail_authors": "p.relations.authors a.link.person",
    "detail_year": "span.date",
    "detail_abstract": "div.textblock"
}


def get_driver():
    """Initializes and returns a configured undetected_chromedriver instance."""
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Can be enabled for production runs
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options)


def extract_publication_details(driver, url):
    """Visits a single publication URL and extracts its details."""
    try:
        driver.get(url)
        # Wait for a key element like the title to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["detail_title"]))
        )
        time.sleep(0.5)  # Small delay to allow dynamic content to load

        title = driver.find_element(By.CSS_SELECTOR, SELECTORS["detail_title"]).text
        authors = [elem.text for elem in driver.find_elements(By.CSS_SELECTOR, SELECTORS["detail_authors"])]

        # Use try-except for optional fields
        try:
            year_text = driver.find_element(By.CSS_SELECTOR, SELECTORS["detail_year"]).text
            # Extract the year (e.g., from "Dec 2023")
            publicationYear = int(year_text.split()[-1])
        except (NoSuchElementException, ValueError, IndexError):
            publicationYear = None

        try:
            abstract = driver.find_element(By.CSS_SELECTOR, SELECTORS["detail_abstract"]).text
        except NoSuchElementException:
            abstract = None

        return {
            "title": title,
            "publicationUrl": url,
            "authors": authors,
            "publicationYear": publicationYear,
            "abstract": abstract,
        }
    except TimeoutException:
        logging.error(f"Timeout while waiting for details on page: {url}")
        return None
    except Exception as e:
        logging.error(f"Failed to extract details from {url}: {e}")
        return None


def crawl_and_extract():
    """
    Performs a two-step crawl:
    1. Collects all unique publication URLs from paginated listing pages.
    2. Visits each collected URL to extract detailed publication information.
    """
    logging.info("--- Initializing browser ---")
    driver = get_driver()
    publication_urls = []
    visited_urls = set()

    try:
        # --- Step 1: Collect all unique publication URLs by navigating pages ---
        logging.info("--- Starting Step 1: Collecting publication URLs ---")
        current_url = START_URL
        while current_url:
            logging.info(f"Scanning listing page: {current_url}")
            driver.get(current_url)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["publication_link"])))

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links_on_page = soup.select(SELECTORS["publication_link"])

            new_links_found = 0
            for link_tag in links_on_page:
                if link_tag.has_attr('href'):
                    full_url = urljoin(BASE_URL, link_tag['href'])
                    if full_url not in visited_urls:
                        publication_urls.append(full_url)
                        visited_urls.add(full_url)
                        new_links_found += 1
            logging.info(f"-> Found {new_links_found} new publication URLs on this page.")

            # More robust pagination logic using a "next" button selector
            try:
                next_page_link = driver.find_element(By.CSS_SELECTOR, SELECTORS["pagination_next"])
                current_url = next_page_link.get_attribute('href')
            except NoSuchElementException:
                logging.info("No 'next' page link found. URL collection finished.")
                current_url = None

        logging.info(f"--- Step 1 complete. Found a total of {len(publication_urls)} unique URLs. ---")

        # --- Step 2: Extract details for each publication ---
        logging.info("--- Starting Step 2: Extracting publication details for each URL ---")
        all_publications = []
        for i, url in enumerate(publication_urls, 1):
            details = extract_publication_details(driver, url)
            if details:
                all_publications.append(details)

            # Log progress periodically
            if i % 25 == 0 or i == len(publication_urls):
                logging.info(f"Processed {i}/{len(publication_urls)} publications.")

        logging.info(
            f"--- Step 2 complete. Successfully extracted details for {len(all_publications)} publications. ---")

    finally:
        logging.info("--- Closing browser ---")
        driver.quit()

    # --- Save results ---
    logging.info(f"Saving {len(all_publications)} complete publication records to file.")
    with open(PUBLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_publications, f, indent=4, ensure_ascii=False)

    logging.info(f"Data successfully saved to {PUBLICATIONS_FILE}")


if __name__ == "__main__":
    crawl_and_extract()