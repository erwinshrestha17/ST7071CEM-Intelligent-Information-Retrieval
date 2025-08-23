# backend/classification/classification_preprocessing.py

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Initialize components once to be efficient
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text: str) -> str:
    """
    Cleans, tokenizes, removes stop words, and lemmatizes text.
    This is the single source of truth for preprocessing.
    """
    text = re.sub(r'[^a-z\s]', '', text.lower())
    tokens = text.split()
    lemmatized = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return " ".join(lemmatized)