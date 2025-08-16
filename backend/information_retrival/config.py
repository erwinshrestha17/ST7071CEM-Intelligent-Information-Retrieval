# backend/config.py

from pathlib import Path

# This gives us the project root directory (InformationRetrivalAssignment/)
ROOT_DIR = Path(__file__).parent.parent

# --- File Paths ---
PUBLICATIONS_FILE = ROOT_DIR / "publications.json"
INDEX_FILE = ROOT_DIR / "inverted_index.json"
LABELED_DATA_FILE = ROOT_DIR / "labeled_data.json"
CLASSIFIER_FILE = ROOT_DIR / "publication_classifier.pkl"

# --- Crawler Configuration ---
START_URL = "https://pureportal.coventry.ac.uk/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/"
BASE_URL = "https://pureportal.coventry.ac.uk"