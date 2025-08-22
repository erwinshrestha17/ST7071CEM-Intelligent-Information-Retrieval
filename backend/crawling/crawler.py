import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin
import json

# --- Import Chrome-specific classes and manager ---
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from backend.crawling.config import USER_AGENT, BASE_URL, POLITE_DELAY, COVENTRY_PUREPORTAL_URL


# --- Configuration ---



# --- Driver Setup (Modified for Chrome) ---
def setup_driver():
    """Sets up a headless Chrome browser instance using Selenium and webdriver_manager."""
    print("Setting up the headless Chrome browser...")
    chrome_options = ChromeOptions()
    # The new standard for headless mode. Use this instead of '--headless'.
    # To see the browser window, remove the '#' from the line below.
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")

    try:
        # Use ChromeDriverManager to automatically handle the driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Driver setup complete.")
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        return None


# --- New function to fetch authors ---
def fetch_authors(soup, base_url):
    authors_data = []
    persons_p = soup.select_one('p.relations.persons')
    if not persons_p:
        return []
    for element in persons_p.contents:
        if isinstance(element, Tag) and element.name == 'a':
            name = element.get_text(strip=True)
            url = urljoin(base_url, str(element.get('href', '')))
            if name:
                authors_data.append({'name': name, 'url': url})
        elif isinstance(element, str):
            potential_names = element.split(',')
            for name_part in potential_names:
                clean_name = name_part.strip(' ,')
                if clean_name:
                    authors_data.append({'name': clean_name, 'url': None})
    return authors_data


# --- Extract abstract content from publication url ---
def fetch_abstract(soup):
    # Find the specific div containing the abstract
    abstract_div = soup.find('div', class_='rendering_researchoutput_abstractportal')
    if abstract_div:
        # The text is within a nested 'textblock' div
        text_block = abstract_div.find('div', class_='textblock')
        if text_block:
            return text_block.get_text(strip=True)
    return ''  # Return empty string if abstract is not found


# --- Scrape details from a single publication page ---
def scrape_publication_details(driver, url, title_from_list):
    """Scrapes authors and abstract from a single publication page."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.container')))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Use the title scraped from the list page
        title = title_from_list
        authors, date, abstract = [], 'N/A', ''

        # Scrape authors
        try:
            authors = fetch_authors(soup, BASE_URL)
        except Exception as e:
            print(f"Could not find authors on {url}: {e}")

        # Scrape abstract
        abstract = fetch_abstract(soup)

        # Scrape date
        date_tag = soup.find('span', class_='date')
        date = date_tag.text.strip() if date_tag else 'N/A'

        return title, authors, date, abstract

    except (TimeoutException, WebDriverException) as e:
        print(f"Error loading page {url}: {e}")
        return title_from_list, [], 'N/A', ''


# --- Crawler Core ---
def crawl_pureportal(driver, start_url):
    """
    Crawls the Pureportal page, fetches publication links and titles, and then scrapes details.
    """
    print(f"Starting crawl from: {start_url}")
    publications_data = []
    try:
        driver.get(start_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-results'))
        )

        publication_details_list = []

        # Step 1: Collect publication links and titles
        while True:
            print(f"Collecting links from current page...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            publication_elements = soup.find_all('li', class_='list-result-item')
            if not publication_elements:
                print("No more publication elements found. Exiting.")
                break

            for pub_elem in publication_elements:
                title_tag = pub_elem.find('a', class_='link')
                if title_tag and title_tag.get('href'):
                    pub_title = title_tag.get_text(strip=True)
                    pub_link = urljoin(BASE_URL, title_tag['href'])
                    publication_details_list.append({'title': pub_title, 'link': pub_link})

            try:
                next_page = soup.find('a', class_='nextLink')
                if isinstance(next_page, Tag) and 'href' in next_page.attrs:
                    print("Moving to next page...")
                    next_page_link = urljoin(BASE_URL, str(next_page['href']))
                    print(f"Next url: {next_page_link}")
                    time.sleep(POLITE_DELAY)
                    driver.get(next_page_link)
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-results'))
                    )
                else:
                    print("No more pages to crawl.")
                    break
            except NoSuchElementException:
                print("No next page button found. Assuming end of results.")
                break

        print(f"Collected {len(publication_details_list)} publication links. Now scraping details...")

        # Step 2: Visit each publication link and scrape details
        for i, pub_info in enumerate(publication_details_list):
            link = pub_info['link']
            title = pub_info['title']
            print(f"Scraping details for publication {i + 1}/{len(publication_details_list)}: {link}")

            title_final, authors, date, abstract = scrape_publication_details(driver, link, title)

            publications_data.append({
                'id': i,  # Assigning a simple ID
                'title': title_final,
                'authors': json.dumps(authors),  # Serialize authors to a string for CSV
                'date': date,
                'abstract': abstract,
                'publication_link': link
            })

            time.sleep(POLITE_DELAY)

        return publications_data

    except TimeoutException:
        print("Page load timed out. Some content might not have been retrieved.")
        return publications_data
    except WebDriverException as e:
        print(f"WebDriver error during crawl: {e}")
        return publications_data
    finally:
        if driver:
            driver.quit()


# --- Main Execution ---
if __name__ == "__main__":
    driver = setup_driver()
    if driver is None:
        exit()

    publications_data = crawl_pureportal(driver, COVENTRY_PUREPORTAL_URL)

    print("\n--- Crawling Complete. Total Publications Found: ---")
    print(len(publications_data))

    df = pd.DataFrame(publications_data)
    df.to_csv("coventry_publications.csv", index=False)
    print("Publications saved to coventry_publications.csv")