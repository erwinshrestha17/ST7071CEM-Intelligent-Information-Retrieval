# backend/crawling/preprocessing.py

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from typing import List

# Ensure necessary NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/omw-1.4')
# Use LookupError as it's the base exception for these download errors
except LookupError:
    print("First-time setup: Downloading NLTK data...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    print("NLTK data download complete.")


# Initialize tools once to be imported elsewhere
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text: str) -> List[str]:
    # ... (rest of the file is identical to your version, no changes needed)
    """
    Applies consistent preprocessing: lowercasing, tokenization,
    alphanumeric filtering, stop-word removal, and lemmatization.
    """
    if not text:
        return []
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word.isalnum()]
    return [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]