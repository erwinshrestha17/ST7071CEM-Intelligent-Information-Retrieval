# backend/config.py

from pathlib import Path

# --- Project Root ---
# Assumes this file is in the 'backend' directory, one level down from the root.
PROJECT_ROOT = Path(__file__).parent.parent

# --- File Paths ---
PUBLICATIONS_FILE = PROJECT_ROOT / "backend/crawling/coventry_publications.csv"
INDEX_FILE = PROJECT_ROOT / "backend/crawling/search_index.json"

# --- Model & Vectorizer Paths ---
CLASSIFIER_FILE = PROJECT_ROOT / "backend/classification/naive_bayes_classifier.pkl"
VECTORIZER_FILE = PROJECT_ROOT / "backend/classification/tfidf_vectorizer.pkl"

# --- Crawler Configuration ---
COVENTRY_PUREPORTAL_URL = "https://pureportal.coventry.ac.uk/en/organisations/fbl-school-of-economics-finance-and-accounting/publications"
BASE_URL = "https://pureportal.coventry.ac.uk"
USER_AGENT = "MyCoventryUniversityAcademicCrawler/1.0"
POLITE_DELAY = 5  # polite delay between requests