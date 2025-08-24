# backend/crawling/indexer.py

import json
import csv
import ast
from collections import defaultdict
import math
from datetime import datetime

# Local module imports
from backend.config import PUBLICATIONS_FILE, INDEX_FILE
from crawler_preprocessing import preprocess_text


def build_index():
    """
    Builds an enhanced inverted index from a CSV file of documents.
    """
    try:
        document_store = []
        with open(PUBLICATIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                document_store.append(row)
    except FileNotFoundError:
        print(f"Error: {PUBLICATIONS_FILE} not found. Ensure the CSV file exists.")
        return

    if not document_store:
        print("Warning: The publications file is empty.")
        return

    print(f"Building enhanced inverted index from {len(document_store)} documents...")

    inverted_index = defaultdict(dict)
    document_metadata = {}

    FIELD_WEIGHTS = {'title': 5.0, 'keywords': 3.0, 'authors': 2.5, 'abstract': 1.0}
    current_year = datetime.now().year

    for doc_id, document in enumerate(document_store):
        doc_id_str = str(doc_id)
        title = document.get('title', '').strip()
        if not title:
            continue

        # Process text from fields
        title_tokens = preprocess_text(title)
        abstract = document.get('abstract', '')
        abstract_tokens = preprocess_text(abstract)

        # Safely parse authors from string to list of names
        try:
            authors_data = ast.literal_eval(document.get('authors', '[]'))
            if authors_data and isinstance(authors_data[0], dict):
                authors = [author.get('name', '') for author in authors_data]
            else:
                authors = authors_data
        except (ValueError, SyntaxError):
            authors = []
        author_tokens = preprocess_text(" ".join(authors))

        # Safely parse keywords
        try:
            keywords_data = ast.literal_eval(document.get('keywords', '[]'))
            keywords = keywords_data if isinstance(keywords_data, list) else []
        except (ValueError, SyntaxError):
            keywords = []
        keyword_tokens = preprocess_text(" ".join(keywords))

        # Calculate weighted term frequencies
        term_frequencies = defaultdict(float)
        for token in title_tokens: term_frequencies[token] += FIELD_WEIGHTS['title']
        for token in keyword_tokens: term_frequencies[token] += FIELD_WEIGHTS['keywords']
        for token in author_tokens: term_frequencies[token] += FIELD_WEIGHTS['authors']
        for token in abstract_tokens: term_frequencies[token] += FIELD_WEIGHTS['abstract']

        pub_year = None
        date_str = document.get('date', '').strip()

        # MODIFICATION: Standardize "Sept" to "Sep" before parsing
        date_str = date_str.replace('Sept', 'Sep')

        if date_str:
            possible_formats = ['%d %b %Y', '%b %Y', '%Y']
            for fmt in possible_formats:
                try:
                    pub_year = datetime.strptime(date_str, fmt).year
                    break
                except ValueError:
                    continue
            if not pub_year:
                print(f"Warning: Could not parse date '{date_str}' for doc_id {doc_id} with any known format.")

        if pub_year and pub_year > 1900:
            years_since = current_year - pub_year
            if 0 <= years_since <= 5:
                boost = 1.0 + (0.2 * (5 - years_since) / 5)
                for token in term_frequencies: term_frequencies[token] *= boost

        # Normalize term frequencies
        doc_length = sum(term_frequencies.values())
        if doc_length > 0:
            for token, tf in term_frequencies.items():
                inverted_index[token][doc_id_str] = tf / doc_length

        # Store metadata for filtering and display
        document_metadata[doc_id_str] = {
            'title': title,
            'url': document.get('publication_link', ''),
            'year': pub_year,
            'authors': authors
        }

    # Calculate IDF for each term
    num_docs = len(document_metadata)
    final_index = {}
    for term, postings in inverted_index.items():
        doc_freq = len(postings)
        idf = math.log(1 + num_docs / (1 + doc_freq))
        final_index[term] = {'idf': idf, 'postings': postings}

    # Save the complete index to a file
    index_data = {
        'index': final_index,
        'metadata': document_metadata,
        'stats': {'total_docs': num_docs, 'total_terms': len(final_index)}
    }
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print("✅ Indexing complete!")
    print(f"   📊 {len(final_index)} unique terms from {num_docs} documents.")
    print(f"   💾 Index saved to {INDEX_FILE}")


if __name__ == "__main__":
    build_index()