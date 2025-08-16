# backend/crawler.py

import json
import logging
import re
import time
import random
from urllib.parse import urljoin

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import configuration from the config module
from .config import BASE_URL, START_URL, PUBLICATIONS_FILE

# Centralize logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Selectors for both listing and detail pages
SELECTORS = {
    "publication_link": "h3.title a",
    "pagination_current": "span.currentStep",
    "title": "h1.title",
    "authors": "a.link.person",
    "date": "span.date",
    "details_content": ".rendering_content",
    "abstract_container": "div.rendering_abstract div.textblock"
}


def get_driver():
    """Initializes and returns a configured undetected_chromedriver instance."""
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Keep commented for debugging
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options)


def extract_all_publication_data(url, driver):
    """
    Visits a single publication page and extracts ALL relevant data.
    """
    pub_data = {
        "title": None, "publicationUrl": url, "authors": [],
        "authorProfileUrl": None, "publicationYear": None, "abstract": None
    }
    try:
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["details_content"])))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.select_one(SELECTORS["title"])
        if title_tag:
            pub_data["title"] = title_tag.get_text(strip=True)

        authors_tags = soup.select(SELECTORS["authors"])
        if authors_tags:
            pub_data["authors"] = [a.get_text(strip=True) for a in authors_tags]
            pub_data["authorProfileUrl"] = urljoin(BASE_URL, authors_tags[0]['href'])

        year_tag = soup.select_one(SELECTORS["date"])
        if year_tag:
            year_match = re.search(r'\d{4}', year_tag.get_text(strip=True))
            if year_match:
                pub_data["publicationYear"] = int(year_match.group())

        abstract_tag = soup.select_one(SELECTORS["abstract_container"])
        if abstract_tag:
            pub_data["abstract"] = abstract_tag.get_text(separator="\n", strip=True)

    except TimeoutException:
        logging.warning(f"Timeout waiting for details page to load: {url}")
    except Exception as e:
        logging.error(f"Error extracting details from {url}: {e}")

    return pub_data


def crawl_and_extract():
    """
    Crawls the university portal page-by-page, collects all publication URLs,
    then visits each URL to extract its full data.
    """
    logging.info("--- Initializing browser for crawling process ---")
    driver = get_driver()
    publication_urls = []
    visited_urls = set()

    try:
        # --- Step 1: Collect all unique publication URLs by navigating pages ---
        logging.info("--- Starting Step 1: Collecting publication URLs ---")
        current_url = START_URL
        while current_url:
            logging.info(f"Scanning listing page: {current_url.split('/')[-1] or 'page=0'}")
            driver.get(current_url)

            # Use a short wait for the results to be present
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
            logging.info(f"-> Found {new_links_found} new publication URLs.")

            # Robust pagination logic
            try:
                current_page_element = driver.find_element(By.CSS_SELECTOR, SELECTORS["pagination_current"])
                parent_li = current_page_element.find_element(By.XPATH, "./parent::li")
                next_li = parent_li.find_element(By.XPATH, "./following-sibling::li")
                next_page_link = next_li.find_element(By.TAG_NAME, "a")
                current_url = next_page_link.get_attribute('href')
            except NoSuchElementException:
                logging.info("No more pages found. URL collection finished.")
                current_url = None

        logging.info(f"--- Step 1 complete. Found a total of {len(publication_urls)} URLs. ---")

        # --- Step 2: Extract details for each unique URL ---
        logging.info("--- Starting Step 2: Extracting publication details ---")
        all_publications = []
        for i, url in enumerate(publication_urls):
            logging.info(f"Processing URL {i + 1}/{len(publication_urls)}: {url.split('/')[-1]}")

            sleep_time = random.uniform(2, 5)  # Polite delay
            logging.info(f"  Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

            data = extract_all_publication_data(url, driver)
            if data.get("title"):
                all_publications.append(data)
        logging.info("--- Step 2 complete. ---")

    finally:
        logging.info("--- Closing browser ---")
        driver.quit()

    # --- Save results ---
    logging.info(f"Crawling complete. Writing {len(all_publications)} publications to file.")
    # The output is a list of objects, which is a standard JSON format
    with open(PUBLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_publications, f, indent=4, ensure_ascii=False)

    logging.info(f"Data successfully saved to {PUBLICATIONS_FILE}")


if __name__ == "__main__":
    crawl_and_extract()