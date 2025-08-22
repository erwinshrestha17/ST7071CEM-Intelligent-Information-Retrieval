# backend/crawling/config.py

from pathlib import Path

# --- Project Root ---
# This assumes the script is run from the project's root directory
# or that this file is two levels down from the root (e.g., backend/crawling/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# --- File Paths ---
PUBLICATIONS_FILE = PROJECT_ROOT / "backend/coventry_publications.csv"
INDEX_FILE = PROJECT_ROOT / "backend/search_index.json"
CLASSIFIER_FILE = PROJECT_ROOT / "title_classifier.pkl"
LABELED_DATA_FILE = PROJECT_ROOT / "labeled_data.json" # Assumed path for labeled data

# --- Crawler Configuration ---

COVENTRY_PUREPORTAL_URL = "https://pureportal.coventry.ac.uk/en/organisations/fbl-school-of-economics-finance-and-accounting/publications"
BASE_URL = "https://pureportal.coventry.ac.uk"
USER_AGENT = "MyCoventryUniversityAcademicCrawler/1.0"
POLITE_DELAY = 5  # polite delay between requests