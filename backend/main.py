import json
import csv
import pickle
import numpy as np
from typing import List, Optional, DefaultDict
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime
import traceback
from pathlib import Path
import pprint

# --- Local Module Imports ---
# Make sure you have these files and they are correctly referenced
# For this example, we'll assume placeholder paths if they don't exist.
try:
    from backend.config import INDEX_FILE, PUBLICATIONS_FILE
    from backend.crawling.crawler_preprocessing import preprocess_text as preprocess_for_search
    from backend.classification.classification_preprocessing import preprocess_text as preprocess_for_classification
except ImportError:
    # Define dummy functions and paths if the modules are not found,
    # allowing the server to start for inspection.
    print("Warning: Local modules not found. Using placeholder functions and paths.")
    INDEX_FILE = "index.json"
    PUBLICATIONS_FILE = "publications.csv"


    def preprocess_for_search(text: str) -> List[str]:
        return text.lower().split()


    def preprocess_for_classification(text: str) -> str:
        return text.lower()

# --- App and CORS Setup ---
app = FastAPI(title="Publication Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Adjust for your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global In-Memory Stores ---
index_data: dict = {}
document_metadata: dict = {}
document_store: list = []
classifier = None
vectorizer = None


# --- Startup Event ---
@app.on_event("startup")
async def startup_event_handler():
    """Loads and pre-processes data files into memory on server start."""
    global index_data, document_metadata, document_store, classifier, vectorizer
    print("--- SERVER STARTUP: Loading data... ---")
    try:
        # Load search index
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            full_index = json.load(f)
            index_data = full_index.get('index', {})
            document_metadata = full_index.get('metadata', {})
        print(f"-> Index loaded with {len(index_data)} terms.")

        # Load publications CSV
        with open(PUBLICATIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up author data
                try:
                    authors_str = row.get('authors', '[]')
                    authors_data = json.loads(authors_str)
                    if authors_data and isinstance(authors_data[0], dict):
                        row['authors'] = [author.get('name', '') for author in authors_data]
                    else:
                        row['authors'] = authors_data
                except (json.JSONDecodeError, TypeError):
                    row['authors'] = []

                # Parse and standardize publication year
                pub_year = None
                date_str = row.get('date', '').strip().replace('Sept', 'Sep')
                if date_str:
                    possible_formats = ['%d %b %Y', '%b %Y', '%Y']
                    for fmt in possible_formats:
                        try:
                            pub_year = datetime.strptime(date_str, fmt).year
                            break
                        except ValueError:
                            continue
                row['publicationYear'] = pub_year
                document_store.append(row)
        print(f"-> Publications data loaded with {len(document_store)} documents.")

        # Load the Naive Bayes model files
        CLASSIFIER_FILE = Path("backend/classification/naive_bayes_classifier.pkl")
        VECTORIZER_FILE = Path("backend/classification/tfidf_vectorizer_nb.pkl")

        print(f"-> Loading classifier from: {CLASSIFIER_FILE}")
        with open(CLASSIFIER_FILE, 'rb') as f:
            classifier = pickle.load(f)

        print(f"-> Loading vectorizer from: {VECTORIZER_FILE}")
        with open(VECTORIZER_FILE, 'rb') as f:
            vectorizer = pickle.load(f)

        print("-> Naive Bayes classifier and vectorizer loaded successfully.")

    except FileNotFoundError as e:
        print(f"FATAL ERROR: A required data file was not found: {e}. API may not function.")
    except Exception as e:
        print(f"FATAL ERROR during startup: {e}. API may not function.")
        traceback.print_exc()

    print("--- STARTUP COMPLETE. API is ready. ---")


# --- API Models ---

class SearchRequest(BaseModel):
    query: str


class Publication(BaseModel):
    """Represents a single publication document in the response."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    authors: List[str] = []
    date: Optional[str] = None
    abstract: Optional[str] = None
    publication: Optional[str] = None
    publicationYear: Optional[int] = None
    category: Optional[str] = None
    publicationUrl: Optional[str] = Field(None, alias='publication_link')
    relevanceScore: Optional[float] = None


class SearchResponse(BaseModel):
    total: int
    publications: List[Publication]


class ClassificationRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to be classified.")


class ClassificationResponse(BaseModel):
    predicted_category: str
    confidence_score: float


# --- Helper Functions for Search Logic ---

def _calculate_tf_idf_scores(query_tokens: List[str]) -> DefaultDict[str, float]:
    """Calculates TF-IDF scores for documents based on query tokens."""
    scores = defaultdict(float)
    for token in query_tokens:
        if token in index_data:
            term_info = index_data[token]
            idf = term_info.get('idf', 1.0)
            for doc_id, tf in term_info['postings'].items():
                scores[doc_id] += tf * idf
    return scores


def _filter_doc_ids_by_year(
        doc_ids: List[str],
        min_year: Optional[int],
        max_year: Optional[int]
) -> List[str]:
    """Filters a list of document IDs based on a year range."""
    if not min_year and not max_year:
        return doc_ids

    filtered_ids = []
    for doc_id in doc_ids:
        meta = document_metadata.get(doc_id)
        if not meta or meta.get('year') is None:
            continue

        pub_year = meta['year']
        if (min_year and pub_year < min_year) or (max_year and pub_year > max_year):
            continue

        filtered_ids.append(doc_id)
    return filtered_ids


def _get_classified_publications(
    doc_ids: List[str],
    scores: DefaultDict[str, float]
) -> List[dict]:
    """Retrieves and classifies full publication data for a list of IDs."""
    results = []
    for doc_id in doc_ids:
        try:
            # Create a copy to avoid modifying the global document_store
            doc = document_store[int(doc_id)].copy()
            doc['relevanceScore'] = scores.get(doc_id, 0.0)
            text_to_classify = (doc.get('title', '') + ' ' + doc.get('abstract', '')).strip()

            if classifier and vectorizer and text_to_classify:
                processed_text = preprocess_for_classification(text_to_classify)
                vectorized_text = vectorizer.transform([processed_text])
                predicted_category = classifier.predict(vectorized_text)[0]
                doc['category'] = predicted_category
            else:
                doc['category'] = 'Unclassified'

            results.append(doc)
        except (IndexError, ValueError) as e:
            print(f"Warning: Could not retrieve document for ID '{doc_id}'. Error: {e}")
            continue
    return results


# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "API is running."}


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """Classifies the given text into a predefined category."""
    if not classifier or not vectorizer:
        raise HTTPException(status_code=503, detail="Classifier is not available.")

    try:
        processed_text = preprocess_for_classification(request.text)
        vectorized_text = vectorizer.transform([processed_text])
        predicted_category = classifier.predict(vectorized_text)[0]
        probabilities = classifier.predict_proba(vectorized_text)[0]
        confidence = float(np.max(probabilities))

        return ClassificationResponse(
            predicted_category=predicted_category,
            confidence_score=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {e}")


@app.post("/api/search", response_model=SearchResponse)
async def search_publications(
        request: SearchRequest,
        # MODIFIED: Removed page and page_size parameters
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
):
    """
    Searches publications based on a query, filters by year,
    and returns all matching, classified results.
    """
    print("─" * 50)
    print("🚀 NEW SEARCH REQUEST RECEIVED 🚀")

    print("\n[INPUT] Request Body (SearchRequest):", request)
    print(f"[INPUT] Query Parameters: min_year={min_year}, max_year={max_year}")

    if not index_data or not document_store:
        raise HTTPException(status_code=503, detail="Search index is not available.")

    # 1. Process query and calculate scores
    query_tokens = preprocess_for_search(request.query)
    print("\n[STEP 1] Preprocessed Query Tokens:", query_tokens)
    scores = _calculate_tf_idf_scores(query_tokens)
    print("\n[STEP 1] Calculated TF-IDF Scores (first 5):")
    pprint.pprint(dict(list(scores.items())[:5]))

    if not scores:
        print("\n[INFO] No documents matched the query. Returning empty response.")
        return SearchResponse(total=0, publications=[])

    # 2. Filter results by year
    doc_ids = list(scores.keys())
    print(f"\n[STEP 2] Document IDs before year filtering: {len(doc_ids)} total")
    filtered_doc_ids = _filter_doc_ids_by_year(doc_ids, min_year, max_year)
    print(f"[STEP 2] Document IDs AFTER year filtering: {len(filtered_doc_ids)} total")

    # 3. Sort by relevance score
    sorted_doc_ids = sorted(
        filtered_doc_ids,
        key=lambda doc_id: scores[doc_id],
        reverse=True
    )
    print("\n[STEP 3] Sorted Document IDs (first 10):", sorted_doc_ids[:10])

    # 4. MODIFIED: Pagination is removed. All results will be returned.
    total_results = len(sorted_doc_ids)
    print(f"\n[STEP 4] Found {total_results} total matching results. Returning all.")

    # 5. Retrieve full publication data for ALL sorted IDs and classify
    results = _get_classified_publications(sorted_doc_ids, scores)
    print("\n[STEP 5] Final classified publications being returned (first result):")
    if results:
        pprint.pprint(results[0])
    else:
        print("[STEP 5] No results to return.")

    print("\n✅ REQUEST COMPLETE")
    print("─" * 50)

    return SearchResponse(total=total_results, publications=results)