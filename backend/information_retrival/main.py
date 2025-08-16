# backend/main.py

import json
import math
import pickle
from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sklearn.pipeline import Pipeline

# Import our own modules using relative paths
from .config import INDEX_FILE, PUBLICATIONS_FILE, CLASSIFIER_FILE
from .preprocessing import preprocess_text
from .crawler import crawl_and_extract
from .indexer import build_inverted_index
from .train_classifier import train_and_save_classifier

# --- App and CORS Setup ---
app = FastAPI(title="Publication Search API")
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Global In-Memory Stores ---
# These will be populated at startup.
inverted_index: dict = {}
document_store: dict = {}
num_documents: int = 0
classifier: Optional[Pipeline] = None


# --- Startup Event Handler ---
@app.on_event("startup")
async def startup_event_handler():
    """
    Orchestrates the crawling, indexing, training, and loading of data on server start.
    """
    global inverted_index, document_store, num_documents, classifier

    print("--- SERVER STARTUP PROCESS INITIATED ---")

    # Step 1: Run Crawler to get the latest publications
    print("\n[STEP 1/4] Running the crawler...")
    crawl_and_extract()
    print("[STEP 1/4] Crawler finished.")

    # Step 2: Run Indexer to build the search index
    print("\n[STEP 2/4] Running the indexer...")
    build_inverted_index()
    print("[STEP 2/4] Indexer finished.")

    # Step 3: Run Classifier Training
    print("\n[STEP 3/4] Training the classifier...")
    train_and_save_classifier()
    print("[STEP 3/4] Classifier training finished.")

    # Step 4: Load all generated files into memory
    print("\n[STEP 4/4] Loading all data files into memory...")
    try:
        with open(INDEX_FILE, 'r') as f:
            inverted_index = json.load(f)
        with open(PUBLICATIONS_FILE, 'r') as f:
            document_store = json.load(f)
        num_documents = len(document_store)
        print(f"-> Index and documents loaded. {len(inverted_index)} terms, {num_documents} documents.")

        with open(CLASSIFIER_FILE, 'rb') as f:
            classifier = pickle.load(f)
        print(f"-> Classifier '{CLASSIFIER_FILE}' loaded successfully.")

    except FileNotFoundError as e:
        print(f"WARNING: Could not load data files after startup: {e}")
        print("Search and classify endpoints may not function correctly.")

    print("\n--- STARTUP PROCESS COMPLETE. API is ready to accept requests. ---")


# --- API Models ---
class SearchQuery(BaseModel):
    query: str


class Publication(BaseModel):
    title: str
    publicationUrl: str
    authors: List[str]
    authorProfileUrl: str
    publicationYear: int


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
async def search_publications_endpoint(
        search_query: SearchQuery,
        page: int = 1,
        page_size: int = Query(10, ge=1, le=100)
):
    if not inverted_index or not document_store:
        return {"total": 0, "publications": []}

    query_tokens = preprocess_text(search_query.query)
    scores = {}

    for token in query_tokens:
        if token in inverted_index:
            postings = inverted_index[token]
            idf = math.log((num_documents + 1) / (len(postings) + 1)) + 1
            for doc_id, tf in postings.items():
                score = (1 + math.log(tf)) * idf
                scores[doc_id] = scores.get(doc_id, 0) + score

    if not scores:
        return {"total": 0, "publications": []}

    sorted_doc_ids = sorted(scores.keys(), key=lambda id: scores[id], reverse=True)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_ids = sorted_doc_ids[start_index:end_index]

    results = [document_store[doc_id] for doc_id in paginated_ids if doc_id in document_store]

    return {"total": len(sorted_doc_ids), "publications": results}


@app.post("/api/classify", response_model=ClassifyResponse)
async def classify_document_endpoint(document: ClassifyRequest):
    if not classifier:
        return {"category": "unknown (classifier not loaded)"}

    prediction = classifier.predict([document.text])
    return {"category": prediction[0]}