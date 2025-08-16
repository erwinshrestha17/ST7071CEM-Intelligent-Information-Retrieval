# backend/indexer.py

import json
from collections import defaultdict
import nltk

# Use relative imports for local modules
from .preprocessing import preprocess_text
from .config import PUBLICATIONS_FILE, INDEX_FILE


def build_inverted_index():
    """
    Builds an inverted index from crawled documents, weighting titles higher than authors.
    """
    try:
        with open(PUBLICATIONS_FILE, 'r', encoding='utf-8') as f:
            # The file now contains a list of documents
            document_store = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PUBLICATIONS_FILE} not found. Please run the crawler first.")
        # Create empty files if not found, so the API can start
        with open(PUBLICATIONS_FILE, 'w') as f_pub, open(INDEX_FILE, 'w') as f_idx:
            json.dump([], f_pub)
            json.dump({}, f_idx)
        return

    print("Building inverted index...")
    inverted_index = defaultdict(dict)

    # --- CRITICAL FIX ---
    # Loop through the list using enumerate to get both an index (for the doc_id) and the document
    for doc_id, document in enumerate(document_store):
        title_tokens = preprocess_text(document.get('title', ''))
        authors_text = " ".join(document.get('authors', []))
        author_tokens = preprocess_text(authors_text)

        term_frequencies = defaultdict(int)
        for token in title_tokens:
            term_frequencies[token] += 3  # Title weight
        for token in author_tokens:
            term_frequencies[token] += 1  # Author weight

        for token, tf in term_frequencies.items():
            # JSON keys must be strings, so we cast the doc_id
            inverted_index[token][str(doc_id)] = tf

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(inverted_index, f, indent=4)
    print(f"Inverted index with {len(inverted_index)} terms built and saved to {INDEX_FILE}")


if __name__ == "__main__":
    # Ensure NLTK data is available
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except nltk.downloader.DownloadError:
        nltk.download('punkt')
        nltk.download('stopwords')

    build_inverted_index()