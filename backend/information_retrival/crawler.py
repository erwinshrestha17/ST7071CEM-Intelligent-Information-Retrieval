# backend/crawler.py

import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # Import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Import configuration from the config module
from .config import START_URL, BASE_URL, PUBLICATIONS_FILE


def crawl_and_extract():
    """
    Crawls the university portal using Selenium, extracting publication data
    and handling pagination to go through all result pages.
    """
    print("Starting crawler with Selenium...")

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    # --- DEBUGGING CHANGES ---
    # 1. Comment out headless mode to make the browser window visible.
    # options.add_argument('--headless')

    # 2. Add some common options to improve stability.
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # --- END DEBUGGING CHANGES ---

    driver = webdriver.Chrome(service=service, options=options)

    publications = []
    visited_pages = set()
    current_url = START_URL

    try:
        while current_url and current_url not in visited_pages:
            print(f"Attempting to crawl: {current_url}")
            driver.get(current_url)
            print(f"Successfully loaded URL. Page title: '{driver.title}'")
            visited_pages.add(current_url)

            # --- DEBUGGING: Added specific exception for the wait ---
            try:
                print("Waiting for element with class 'result-container' to appear...")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "result-container"))
                )
                print("Element 'result-container' found.")
            except TimeoutException:
                print(
                    "!!! Timed out waiting for 'result-container'. The page might have changed or failed to load correctly.")
                print("--- Page Source Snapshot ---")
                print(driver.page_source[:2000])  # Print the first 2000 chars of the page source for inspection
                print("--- End Snapshot ---")
                break  # Exit the loop if the main content isn't found
            # --- END DEBUGGING ---

            time.sleep(2)  # Let dynamic content settle

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            for item in soup.find_all("div", class_="result-container"):
                try:
                    title_tag = item.find("h3", class_="title")
                    authors_tags = item.find_all("a", class_="link person")
                    year_tag = item.find("span", class_="date")

                    if title_tag and authors_tags and year_tag:
                        year_text = year_tag.get_text(strip=True)
                        year_match = re.search(r'\d{4}', year_text)
                        if not year_match:
                            continue

                        pub_data = {
                            "title": title_tag.get_text(strip=True),
                            "publicationUrl": urljoin(BASE_URL, title_tag.find("a")['href']),
                            "authors": [author.get_text(strip=True) for author in authors_tags],
                            "authorProfileUrl": urljoin(BASE_URL, authors_tags[0]['href']),
                            "publicationYear": int(year_match.group())
                        }

                        if pub_data not in publications:
                            publications.append(pub_data)

                except Exception as item_error:
                    print(f"  - Skipping a malformed publication entry. Error: {item_error}")
                    continue

            # --- PAGINATION LOGIC ---
            # Find the 'Next' link to handle pagination.
            # The correct class name on the target site is "nextLink".
            next_page_link = soup.find("a", class_="nextLink")

            if next_page_link and 'href' in next_page_link.attrs:
                # If a next link is found, construct the full URL and set it for the next loop iteration.
                next_url = urljoin(BASE_URL, next_page_link['href'])
                print(f"Found next page: {next_url}")
                current_url = next_url
            else:
                # If no next link is found, we are on the last page. End the loop.
                print("No more pages found. Ending crawl.")
                current_url = None
            # --- END PAGINATION LOGIC ---


    except Exception as e:
        print(f"An unexpected error occurred during crawling: {e}")  # This will give a more readable error
    finally:
        driver.quit()

    print(f"\nCrawling complete. Found {len(publications)} publications.")

    document_store = {str(i): doc for i, doc in enumerate(publications)}
    with open(PUBLICATIONS_FILE, 'w') as f:
        json.dump(document_store, f, indent=4)
    print(f"Publications saved to {PUBLICATIONS_FILE}")


if __name__ == "__main__":
    crawl_and_extract()