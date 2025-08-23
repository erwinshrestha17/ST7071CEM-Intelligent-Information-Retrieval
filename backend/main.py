# backend/main.py

import json
import csv
import pickle
import numpy as np
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime
import traceback
from pathlib import Path  # Import Path for robust path handling

# Local module imports
# MODIFICATION: Removed unused config imports for classifier files
from backend.config import INDEX_FILE, PUBLICATIONS_FILE
from backend.crawling.crawler_preprocessing import preprocess_text as preprocess_for_search
from backend.classification.classification_preprocessing import preprocess_text as preprocess_for_classification

# --- App and CORS Setup ---
app = FastAPI(title="Publication Search API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Global In-Memory Stores ---
index_data: dict = {}
document_metadata: dict = {}
document_store: list = []
classifier = None
vectorizer = None


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

        # --- MODIFICATION: Load the CORRECT Naive Bayes model files ---
        # The paths are relative to the project root where uvicorn is running.
        CLASSIFIER_FILE = Path("backend/classification/naive_bayes_classifier.pkl")
        VECTORIZER_FILE = Path("backend/classification/tfidf_vectorizer_nb.pkl")

        print(f"-> Loading classifier from: {CLASSIFIER_FILE}")
        print(f"-> Loading vectorizer from: {VECTORIZER_FILE}")

        with open(CLASSIFIER_FILE, 'rb') as f:
            classifier = pickle.load(f)
        with open(VECTORIZER_FILE, 'rb') as f:
            vectorizer = pickle.load(f)
        print("-> Naive Bayes classifier and vectorizer loaded successfully.")

    except Exception as e:
        print(f"FATAL ERROR during startup: {e}. API may not function.")
        traceback.print_exc()  # Print full error for debugging
    print("--- STARTUP COMPLETE. API is ready. ---")


# --- API Models ---
class SearchRequest(BaseModel):
    query: str


class Publication(BaseModel):
    title: Optional[str] = None
    publication_url: Optional[str] = Field(None, alias='publication_link')
    authors: Optional[List[str]] = None
    publication_year: Optional[int] = Field(None, alias='publicationYear')
    abstract: Optional[str] = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    total: int
    publications: List[Publication]


class ClassificationRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to be classified.")


class ClassificationResponse(BaseModel):
    predicted_category: str
    confidence_score: float


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "API is running."}


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """
    Classifies the given text into a predefined category.
    """
    if not classifier or not vectorizer:
        raise HTTPException(
            status_code=503, detail="Classifier is not available or failed to load."
        )

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
        print("--- AN ERROR OCCURRED DURING CLASSIFICATION ---")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"An error occurred during classification: {e}"
        )


@app.post("/api/search", response_model=SearchResponse)
async def search_publications(
        request: SearchRequest,
        page: int = 1, page_size: int = Query(10, ge=1, le=100),
        min_year: Optional[int] = None, max_year: Optional[int] = None
):
    if not index_data or not document_store:
        raise HTTPException(status_code=503, detail="Search index not available.")

    query_tokens = preprocess_for_search(request.query)
    scores = defaultdict(float)

    for token in query_tokens:
        if token in index_data:
            term_info = index_data[token]
            idf = term_info.get('idf', 1.0)
            for doc_id, tf in term_info['postings'].items():
                scores[doc_id] += tf * idf

    if not scores:
        return SearchResponse(total=0, publications=[])

    if min_year or max_year:
        filtered_doc_ids = []
        for doc_id in scores:
            meta = document_metadata.get(doc_id)
            if not meta or meta.get('year') is None:
                continue
            pub_year = meta['year']
            if (min_year and pub_year < min_year) or (max_year and pub_year > max_year):
                continue
            filtered_doc_ids.append(doc_id)
    else:
        filtered_doc_ids = list(scores.keys())

    sorted_doc_ids = sorted(filtered_doc_ids, key=lambda id: scores[id], reverse=True)

    total_results = len(sorted_doc_ids)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_ids = sorted_doc_ids[start_index:end_index]

    results = [document_store[int(doc_id)] for doc_id in paginated_ids]

    return SearchResponse(total=total_results, publications=results)