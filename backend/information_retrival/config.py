# backend/config.py

from pathlib import Path

# This gives us the project root directory
ROOT_DIR = Path(__file__).parent.parent

# --- File Paths ---
# Use .joinpath() for creating full paths and ensure they are strings for compatibility
PUBLICATIONS_FILE = str(ROOT_DIR.joinpath("publications.json"))
INDEX_FILE = str(ROOT_DIR.joinpath("inverted_index.json"))
LABELED_DATA_FILE = str(ROOT_DIR.joinpath("labeled_data.json"))
CLASSIFIER_FILE = str(ROOT_DIR.joinpath("publication_classifier.pkl"))

# --- Crawler Configuration ---
# This is the starting point for our page-by-page crawler
START_URL = "https://pureportal.coventry.ac.uk/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/"
BASE_URL = "https://pureportal.coventry.ac.uk"