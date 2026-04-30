# Intelligent Information Retrieval System

## Assignment Information

**Module:** ST7071CEM – Intelligent Information Retrieval  
**Coursework:** Individual Coursework  
**Student:** Erwin Shrestha  
**CUID:** 16542468  
**Student ID:** 250089  
**Institution:** Softwarica College of IT & E-Commerce in collaboration with Coventry University

## Project Overview

This assignment implements an **Intelligent Information Retrieval System** consisting of two main parts:

1. **Vertical Search Engine** for academic publications from Coventry University's School of Economics, Finance, and Accounting.
2. **Text Classification System** that classifies documents into **Business**, **Health**, or **Politics** categories.

The system demonstrates core information retrieval and machine learning concepts including web crawling, text preprocessing, inverted indexing, TF-IDF ranking, cosine similarity, and Naïve Bayes classification.

## Key Features

### 1. Vertical Search Engine

- Crawls academic publication data from a focused university publication source.
- Extracts metadata such as:
  - Title
  - Authors
  - Publication date
  - Abstract
  - Publication link
- Cleans and preprocesses text using NLP techniques.
- Builds an inverted index for efficient search.
- Uses TF-IDF weighting and cosine similarity for ranked retrieval.
- Supports free-text search queries.
- Returns ranked academic publication results through a web interface.

### 2. Text Classification

- Classifies text into:
  - Business
  - Health
  - Politics
- Uses a supervised machine learning approach.
- Implements a Multinomial Naïve Bayes classifier.
- Uses TF-IDF vectorization for feature extraction.
- Evaluates performance using accuracy, precision, recall, F1-score, confusion matrix, and cross-validation.

## Technology Stack

### Backend

- Python
- FastAPI
- BeautifulSoup
- Requests
- Scikit-learn
- NLTK
- Pickle

### Frontend

- React
- TypeScript
- Tailwind CSS
- Shadcn/ui

### Data and Storage

- JSON files for labeled classification data
- CSV files for crawled publication data
- Serialized `.pkl` files for trained models and vectorizers
- JSON-based inverted index storage

## System Architecture

The project follows a **decoupled client-server architecture**.

```text
Frontend: React + TypeScript SPA
        |
        | REST API / JSON
        v
Backend: FastAPI Server
        |
        | Search, Classification, Crawling, Indexing
        v
Data: Crawled publications, inverted index, trained ML model
```

The frontend handles the user interface, while the backend performs crawling, indexing, search ranking, and classification tasks.

## Project Structure

A suggested folder structure for this project is:

```text
InformationRetrivalSystem/
│
├── backend/
│   ├── main.py
│   ├── crawler.py
│   ├── indexer.py
│   ├── classifier.py
│   ├── search.py
│   ├── labeled_data.json
│   ├── publications.csv
│   ├── inverted_index.json
│   ├── naive_bayes_classifier.pkl
│   └── tfidf_vectorizer_nb.pkl
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── README.md
└── requirements.txt
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/erwinshrestha17/InformationRetrivalSystem.git
cd InformationRetrivalSystem
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Run the Backend Server

```bash
uvicorn main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

FastAPI documentation can be accessed at:

```text
http://127.0.0.1:8000/docs
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend should run at:

```text
http://localhost:5173
```

## Backend API Endpoints

### Search Publications

```http
POST /api/search
```

Example request:

```json
{
  "query": "fraud risk assessment process",
  "min_year": null,
  "max_year": null
}
```

Example response:

```json
{
  "total": 10,
  "publications": [
    {
      "title": "What Matters in the Assessment of Financial Reporting Fraud Risk?",
      "authors": ["Author Name"],
      "abstract": "Publication abstract...",
      "publicationUrl": "https://example.com",
      "score": 1.49,
      "category": "health"
    }
  ]
}
```

### Classify Text

```http
POST /api/classify
```

Example request:

```json
{
  "text": "Businesses are increasingly focusing on digital transformation to improve efficiency and reduce costs."
}
```

Example response:

```json
{
  "category": "business",
  "confidence": 0.8531
}
```

## Information Retrieval Workflow

### Step 1: Crawling

The crawler collects publication information from the target academic publication source. It follows polite crawling principles such as respecting request delays and avoiding excessive server load.

### Step 2: Text Preprocessing

The collected text is cleaned using:

- Lowercasing
- Tokenization
- Stop-word removal
- Stemming or lemmatization

### Step 3: Indexing

An inverted index is created to map terms to the documents in which they appear. This allows efficient search without scanning every document manually.

### Step 4: Ranking

The system calculates TF-IDF scores and uses cosine similarity to rank documents based on relevance to the user query.

## Classification Workflow

### Step 1: Dataset Preparation

A labeled dataset is prepared with articles from Business, Health, and Politics categories.

### Step 2: Preprocessing

Text is cleaned and normalized before training.

### Step 3: Feature Extraction

TF-IDF vectorization converts text into numerical features.

### Step 4: Model Training

A Multinomial Naïve Bayes classifier is trained using the labeled dataset.

### Step 5: Evaluation

The model is evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- 5-fold cross-validation

## Evaluation Summary

The classifier achieved an accuracy range of approximately **76% to 96%** depending on the evaluation split and validation method. Politics showed the strongest classification performance, Health performed well with slightly lower recall, and Business had the most misclassification overlap with Politics due to similar vocabulary such as government, economy, trade, and policy.

## Screenshots Included in Report

The coursework report includes screenshots of:

- Publication search engine interface
- Search results for academic publication queries
- Google Scholar comparison
- Text classifier interface
- Classification outputs for Business, Health, and Politics
- Confusion matrix and evaluation outputs

## Limitations

- The search engine uses TF-IDF and cosine similarity, which are keyword-based and do not fully understand semantic meaning.
- The classifier uses a bag-of-words style approach, meaning it does not understand word order, grammar, or deeper context.
- The dataset size for classification is relatively small.
- Business and Politics categories may overlap due to similar vocabulary.
- The crawler depends on the structure of the target website, so changes in HTML structure may require code updates.

## Future Improvements

- Add semantic search using sentence embeddings or transformer models.
- Improve crawler robustness for dynamic websites.
- Add advanced filtering by author, year, category, and publication venue.
- Expand the classification dataset.
- Use models such as Logistic Regression, SVM, Random Forest, or BERT for improved classification.
- Add authentication and admin controls.
- Store data in a database such as PostgreSQL instead of flat files.
- Add Docker support for easier deployment.

## Repository and Demo

**GitHub Repository:**  
https://github.com/erwinshrestha17/InformationRetrivalSystem.git

**YouTube Demo:**  
https://youtu.be/hbVQRygxPSI

## Conclusion

This project demonstrates a complete intelligent information retrieval system using modern full-stack development practices. It combines a vertical academic search engine with a machine learning-based document classifier. The system successfully applies core IR and ML concepts such as crawling, preprocessing, inverted indexing, TF-IDF ranking, cosine similarity, and Naïve Bayes classification in a practical web application.
