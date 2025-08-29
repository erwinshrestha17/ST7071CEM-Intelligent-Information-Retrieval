import json
import csv
import pickle
import numpy as np
import time
import uuid
from typing import List, Optional, DefaultDict
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime
import traceback
from pathlib import Path

# --- Local Module Imports ---
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

try:
    from backend.config import INDEX_FILE, PUBLICATIONS_FILE
    from backend.crawling.crawler_preprocessing import preprocess_text as preprocess_for_search
    from backend.classification.classification_preprocessing import preprocess_text as preprocess_for_classification
    print("✅ Successfully imported local backend modules.")

except ImportError as e:
    print("❌ FATAL ERROR: Could not import local backend modules.")
    print(f"   -> Error details: {e}")
    print(f"   -> Ensure you are running the server from the project's root directory.")
    raise


    def preprocess_for_search(text: str) -> List[str]:
        return text.lower().split()


    def preprocess_for_classification(text: str) -> str:
        return text.lower()

# --- App and CORS Setup ---
app = FastAPI(title="Publication Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
    text: str = Field(..., min_length=3, description="Text to be classified.")


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
    # --- Enhanced Logging Setup ---
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    def log(message: str):
        # Helper to prepend timestamp and request ID to each log line
        print(f"[{datetime.now().isoformat(sep=' ', timespec='milliseconds')}] [Request-ID: {request_id}] {message}")

    log("─" * 50)
    log("🚀 NEW CLASSIFICATION REQUEST RECEIVED 🚀")

    text_snippet = (request.text[:100] + '...') if len(request.text) > 100 else request.text
    log(f"Input text (snippet): '{text_snippet}'")

    if not classifier or not vectorizer:
        log("[ERROR] Classifier or vectorizer not available.")
        raise HTTPException(status_code=503, detail="Classifier is not available.")

    try:
        # 1. Preprocess Text
        step1_start = time.time()
        processed_text = preprocess_for_classification(request.text)
        step1_duration = time.time() - step1_start
        log(f"[STEP 1] Preprocessed text in {step1_duration:.4f} seconds.")

        # 2. Vectorize and Predict
        step2_start = time.time()
        vectorized_text = vectorizer.transform([processed_text])
        predicted_category = classifier.predict(vectorized_text)[0]
        probabilities = classifier.predict_proba(vectorized_text)[0]
        confidence = float(np.max(probabilities))
        step2_duration = time.time() - step2_start
        log(f"[STEP 2] Vectorized and predicted category in {step2_duration:.4f} seconds.")
        log(f"  -> Predicted Category: {predicted_category}")
        log(f"  -> Confidence Score: {confidence:.4f}")

        response = ClassificationResponse(
            predicted_category=predicted_category,
            confidence_score=confidence
        )

        total_duration = time.time() - start_time
        log(f"✅ REQUEST COMPLETE in {total_duration:.4f} seconds.")
        log("─" * 50)

        return response

    except Exception as e:
        total_duration = time.time() - start_time
        log(f"[FATAL] An unexpected error occurred after {total_duration:.4f} seconds: {e}")
        log("─" * 50)
        raise HTTPException(status_code=500, detail=f"Classification error: {e}")


@app.post("/api/search", response_model=SearchResponse)
async def search_publications(request: SearchRequest):
    """
    Searches publications based on a query and returns all matching,
    classified results.
    """
    # --- Enhanced Logging Setup ---
    request_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    start_time = time.time()

    def log(message: str):
        # Helper to prepend timestamp and request ID to each log line
        print(f"[{datetime.now().isoformat(sep=' ', timespec='milliseconds')}] [Request-ID: {request_id}] {message}")

    log("─" * 50)
    log("🚀 NEW SEARCH REQUEST RECEIVED 🚀")
    log(f"Query: '{request.query}'")

    if not index_data or not document_store:
        raise HTTPException(status_code=503, detail="Search index is not available.")

    # 1. Process query and calculate scores
    step1_start = time.time()
    query_tokens = preprocess_for_search(request.query)
    log(f"[STEP 1] Preprocessed Query Tokens: {query_tokens}")
    scores = _calculate_tf_idf_scores(query_tokens)
    step1_duration = time.time() - step1_start
    log(f"[STEP 1] Calculated TF-IDF scores for {len(scores)} documents in {step1_duration:.4f} seconds.")

    if not scores:
        log("[INFO] No documents matched the query. Returning empty response.")
        total_duration = time.time() - start_time
        log(f"✅ REQUEST COMPLETE (No Results) in {total_duration:.4f} seconds.")
        log("─" * 50)
        return SearchResponse(total=0, publications=[])

    # 2. Sort by relevance score
    step2_start = time.time()
    doc_ids = list(scores.keys())
    sorted_doc_ids = sorted(
        doc_ids,
        key=lambda doc_id: scores[doc_id],
        reverse=True
    )
    step2_duration = time.time() - step2_start
    log(f"[STEP 2] Sorted {len(sorted_doc_ids)} document IDs in {step2_duration:.4f} seconds.")
    if sorted_doc_ids:
        top_doc_id = sorted_doc_ids[0]
        log(f"[STEP 2] Top result ID: {top_doc_id} with score: {scores[top_doc_id]:.4f}")

    # 3. Retrieve and classify publications
    step3_start = time.time()
    total_results = len(sorted_doc_ids)
    log(f"[STEP 3] Retrieving and classifying {total_results} documents.")
    results = _get_classified_publications(sorted_doc_ids, scores)
    step3_duration = time.time() - step3_start
    log(f"[STEP 3] Retrieved and classified all documents in {step3_duration:.4f} seconds.")

    if results:
        log("[INFO] Sample of the first result being returned:")
        first_res = results[0]
        log(f"  -> Title: {first_res.get('title', 'N/A')[:70]}...")
        log(f"  -> Category: {first_res.get('category', 'N/A')}")
        log(f"  -> Score: {first_res.get('relevanceScore', 0.0):.4f}")
    else:
        log("[INFO] No full documents could be retrieved despite matching scores.")

    total_duration = time.time() - start_time
    log(f"✅ REQUEST COMPLETE in {total_duration:.4f} seconds.")
    log("─" * 50)

    return SearchResponse(total=total_results, publications=results)