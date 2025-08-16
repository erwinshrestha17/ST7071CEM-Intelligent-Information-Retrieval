# backend/preprocessing.py

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from typing import List

# Initialize tools once to be imported elsewhere
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text: str) -> List[str]:
    """
    Applies consistent preprocessing: lowercasing, tokenization,
    alphanumeric filtering, stop-word removal, and stemming.
    """
    if not text:
        return []
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word.isalnum()]
    return [stemmer.stem(word) for word in tokens if word not in stop_words]