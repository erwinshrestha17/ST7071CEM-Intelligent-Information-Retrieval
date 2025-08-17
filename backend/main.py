# backend/main.py

import json
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sklearn.pipeline import Pipeline
import pickle
from collections import defaultdict

# Import our own modules
from backend.information_retrival.config import INDEX_FILE, PUBLICATIONS_FILE, CLASSIFIER_FILE
from backend.information_retrival.preprocessing import preprocess_text

# --- App and CORS Setup ---
app = FastAPI(title="Publication Search API", version="1.0.0")
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Global In-Memory Stores ---
index_data: dict = {}
document_metadata: dict = {}
document_store: list = []
classifier: Optional[Pipeline] = None


# --- Startup Event Handler ---
@app.on_event("startup")
async def startup_event_handler():
    """Loads pre-built index, metadata, documents, and classifier into memory."""
    global index_data, document_metadata, document_store, classifier
    print("--- SERVER STARTUP: Loading data files into memory... ---")

    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            full_index = json.load(f)
            index_data = full_index.get('index', {})
            document_metadata = full_index.get('metadata', {})

        with open(PUBLICATIONS_FILE, 'r', encoding='utf-8') as f:
            document_store = json.load(f)

        print(f"-> Index and metadata loaded. {len(index_data)} terms, {len(document_metadata)} documents.")

        if Path(CLASSIFIER_FILE).exists():
            with open(CLASSIFIER_FILE, 'rb') as f:
                classifier = pickle.load(f)
            print(f"-> Classifier '{CLASSIFIER_FILE}' loaded.")
        else:
            print("-> Classifier file not found, skipping.")

    except FileNotFoundError as e:
        print(f"WARNING: Critical data file not found: {e}. API may not function correctly.")

    print("--- STARTUP COMPLETE. API is ready. ---")


# --- API Models ---
class Publication(BaseModel):
    title: Optional[str] = None
    publicationUrl: Optional[str] = None
    authors: Optional[List[str]] = None
    publicationYear: Optional[int] = None
    abstract: Optional[str] = None


class SearchResponse(BaseModel):
    total: int
    publications: List[Publication]


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    category: str


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "API is running."}


@app.post("/api/search", response_model=SearchResponse)
async def search_publications(
        query: str,
        page: int = 1,
        page_size: int = Query(10, ge=1, le=100),
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
):
    """
    Performs a search query against the index, with support for filtering and pagination.
    """
    if not index_data or not document_store:
        raise HTTPException(status_code=503, detail="Search index is not available.")

    query_tokens = preprocess_text(query)
    scores = defaultdict(float)

    # 1. Calculate TF-IDF scores for all documents matching query terms
    for token in query_tokens:
        if token in index_data:
            term_info = index_data[token]
            idf = term_info.get('idf', 1.0)
            for doc_id, tf in term_info['postings'].items():
                # Correct scoring: normalized TF * IDF
                scores[doc_id] += tf * idf

    if not scores:
        return {"total": 0, "publications": []}

    # 2. Filter the scored documents by year using the efficient metadata lookup
    if min_year or max_year:
        filtered_doc_ids = []
        for doc_id in scores:
            meta = document_metadata.get(doc_id)
            if not meta or 'year' not in meta or meta['year'] is None:
                continue

            pub_year = meta['year']
            if min_year and pub_year < min_year:
                continue
            if max_year and pub_year > max_year:
                continue
            filtered_doc_ids.append(doc_id)
    else:
        filtered_doc_ids = list(scores.keys())

    # 3. Sort the filtered documents by score
    sorted_doc_ids = sorted(filtered_doc_ids, key=lambda id: scores[id], reverse=True)

    # 4. Paginate the results
    total_results = len(sorted_doc_ids)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_ids = sorted_doc_ids[start_index:end_index]

    # 5. Retrieve full document data for the paginated page
    results = [document_store[int(doc_id)] for doc_id in paginated_ids if
               doc_id.isdigit() and int(doc_id) < len(document_store)]

    return {"total": total_results, "publications": results}


@app.post("/api/classify", response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest):
    if not classifier:
        raise HTTPException(status_code=503, detail="Classifier is not available.")
    try:
        prediction = classifier.predict([request.text])
        return {"category": prediction[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {e}")