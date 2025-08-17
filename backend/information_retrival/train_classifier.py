# backend/information_retrival/train_classifier.py

import json
import pickle
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Use relative imports for local modules
from .preprocessing import preprocess_text
from .config import LABELED_DATA_FILE, CLASSIFIER_FILE

def custom_analyzer(text):
    # ... (rest of the file is identical to your version, no changes needed)
    """Custom analyzer for TfidfVectorizer that uses our preprocessor."""
    return preprocess_text(text)

def train_and_save_classifier():
    """
    Trains the classifier model using labeled data and saves it to a file.
    """
    print("Attempting to train classifier...")
    try:
        with open(LABELED_DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {LABELED_DATA_FILE} not found. Skipping classifier training.")
        return

    titles = [item['title'] for item in data]
    categories = [item['category'] for item in data]

    model_pipeline = make_pipeline(
        TfidfVectorizer(analyzer=custom_analyzer),
        MultinomialNB()
    )

    print(f"Training classifier model on {len(titles)} documents...")
    model_pipeline.fit(titles, categories)
    print("Training complete.")

    with open(CLASSIFIER_FILE, 'wb') as f:
        pickle.dump(model_pipeline, f)

    print(f"Classifier model saved to {CLASSIFIER_FILE}")

if __name__ == "__main__":
    # Ensure NLTK data is available if run standalone
    # This check is now also present inside preprocessing.py
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        nltk.data.find('corpora/omw-1.4')
    except nltk.downloader.DownloadError:
        print("Downloading necessary NLTK data for preprocessing...")
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('omw-1.4')

    train_and_save_classifier()