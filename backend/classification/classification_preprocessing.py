# backend/classification/classification_preprocessing.py

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
lemmatizer = WordNetLemmatizer()

default_stopwords = set(stopwords.words('english'))
negation_words = {'not', 'no', 'never', 'nor', 'cannot', 'isnt', 'wont', 'shouldnt', 'couldnt'}
custom_stop_words = default_stopwords - negation_words


def preprocess_text(text: str) -> str:
    text = re.sub(r'[^a-z\s]', '', text.lower())
    tokens = text.split()
    # MODIFICATION: Use the custom stop word list instead of the default
    lemmatized = [lemmatizer.lemmatize(word) for word in tokens if word not in custom_stop_words]
    return " ".join(lemmatized)