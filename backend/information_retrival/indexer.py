# backend/information_retrival/indexer.py

import json
from collections import defaultdict
import math
from datetime import datetime
# Use relative imports for local modules
from .preprocessing import preprocess_text
from .config import PUBLICATIONS_FILE, INDEX_FILE

def build_index():
    # ... (rest of the file is identical to your version, no changes needed)
    """
    Builds an enhanced inverted index with improved error handling and scoring.
    """
    try:
        with open(PUBLICATIONS_FILE, 'r', encoding='utf-8') as f:
            document_store = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PUBLICATIONS_FILE} not found. Running the crawler is required.")
        # Create empty index for graceful degradation
        _create_empty_index()
        return
    except json.JSONDecodeError as e:
        print(f"Error: Publications file is corrupted: {e}")
        return

    if not document_store:
        print("Warning: The publications file is empty.")
        _create_empty_index()
        return

    print(f"Building enhanced inverted index from {len(document_store)} documents...")

    # Statistics tracking
    stats = {
        'docs_with_authors': 0,
        'docs_with_abstracts': 0,
        'docs_with_years': 0,
        'docs_with_keywords': 0,
        'total_terms': 0,
        'avg_doc_length': 0
    }

    inverted_index = defaultdict(dict)
    document_metadata = {}
    all_doc_lengths = []

    # Enhanced field weights
    FIELD_WEIGHTS = {
        'title': 5.0,
        'keywords': 3.0,  # Added high weight for keywords
        'authors': 2.5,
        'abstract': 1.0,
        'year': 0.1
    }

    current_year = datetime.now().year

    for doc_id, document in enumerate(document_store):
        doc_id_str = str(doc_id)

        # Validate document has minimum required fields
        title = document.get('title', '').strip()
        if not title:
            print(f"Warning: Document {doc_id} has no title, skipping")
            continue

        # Process text from different fields
        title_tokens = preprocess_text(title)

        authors = document.get('authors', [])
        if authors:
            stats['docs_with_authors'] += 1
            author_tokens = preprocess_text(" ".join(authors))
        else:
            author_tokens = []

        abstract = document.get('abstract', '')
        if abstract and abstract.strip():
            stats['docs_with_abstracts'] += 1
            abstract_tokens = preprocess_text(abstract)
        else:
            abstract_tokens = []

        keywords = document.get('keywords', [])
        if keywords:
            stats['docs_with_keywords'] += 1
            keyword_tokens = preprocess_text(" ".join(keywords))
        else:
            keyword_tokens = []

        # Calculate weighted term frequencies
        term_frequencies = defaultdict(float)

        # Add terms with field weights
        for token in title_tokens:
            term_frequencies[token] += FIELD_WEIGHTS['title']
        for token in keyword_tokens:
            term_frequencies[token] += FIELD_WEIGHTS['keywords']
        for token in author_tokens:
            term_frequencies[token] += FIELD_WEIGHTS['authors']
        for token in abstract_tokens:
            term_frequencies[token] += FIELD_WEIGHTS['abstract']

        # Apply recency boost
        pub_year = document.get('publicationYear')
        if pub_year and isinstance(pub_year, int) and pub_year > 1900:
            stats['docs_with_years'] += 1
            years_since = current_year - pub_year
            if 0 <= years_since <= 5:
                year_boost = 1.0 + (0.2 * (5 - years_since) / 5)
                for token in term_frequencies:
                    term_frequencies[token] *= year_boost

        # Calculate document length and normalize
        doc_length = sum(term_frequencies.values())
        all_doc_lengths.append(doc_length)

        if doc_length > 0:
            for token, tf in term_frequencies.items():
                normalized_tf = tf / doc_length
                inverted_index[token][doc_id_str] = normalized_tf
        else:
            print(f"Warning: Document {doc_id} has no processable content")

        # Enhanced metadata
        document_metadata[doc_id_str] = {
            'title': title[:150],
            'url': document.get('publicationUrl', ''),
            'year': pub_year,
            'keywords': keywords,
            'doc_len': doc_length,
            'author_count': len(authors),
            'has_abstract': bool(abstract_tokens),
            'crawled_at': document.get('crawled_at'),
            'extraction_quality': document.get('extraction_metadata', {})
        }

    # Calculate final statistics
    if all_doc_lengths:
        stats['avg_doc_length'] = sum(all_doc_lengths) / len(all_doc_lengths)

    num_docs = len(document_metadata)
    final_index = {}

    for term, postings in inverted_index.items():
        doc_freq = len(postings)
        idf = math.log(1 + num_docs / (1 + doc_freq))
        final_index[term] = {'idf': idf, 'df': doc_freq, 'postings': postings}

    stats.update({
        'total_terms': len(final_index),
        'total_docs': num_docs,
        'docs_processed': len(document_metadata),
        'docs_skipped': len(document_store) - len(document_metadata)
    })

    index_data = {
        'index': final_index,
        'metadata': document_metadata,
        'stats': {**stats, 'created_at': datetime.now().isoformat(), 'field_weights': FIELD_WEIGHTS,
                  'indexing_version': '2.1'}
    }

    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        print("✅ Indexing complete!")
        print(f"   📊 {stats['total_terms']} unique terms")
        print(f"   📄 {stats['total_docs']} documents indexed")
        print(f"   🔑 {stats['docs_with_keywords']} docs with keywords")
        print(f"   📝 {stats['docs_with_abstracts']} docs with abstracts")
        print(f"   💾 Index saved to {INDEX_FILE}")

    except Exception as e:
        print(f"❌ Failed to save index: {e}")


def _create_empty_index():
    """Create an empty index file for graceful degradation"""
    empty_index = {
        'index': {}, 'metadata': {},
        'stats': {'total_terms': 0, 'total_docs': 0, 'created_at': datetime.now().isoformat(), 'status': 'empty'}
    }
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(empty_index, f, indent=2)