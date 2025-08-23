import json
import re
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report

# Import configuration paths from the config file
from backend import config
from backend.classification.classification_preprocessing import preprocess_text

def load_labeled_data(file_path):
    """
    Loads documents and labels from the JSON file.
    Combines 'title' and 'summary' for the document text.
    Maps detailed categories into 'business', 'health', and 'politics'.
    """
    print(f"Loading labeled data from {file_path}...")
    if not file_path.exists():
        print(f"Error: Labeled data file not found at {file_path}")
        return [], []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = [item['title'] + ' ' + item['summary'] for item in data]

    # Re-introduced mapping logic to consolidate labels
    labels = []
    health_keywords = ['health', 'disease', 'pharma', 'medical', 'nutrition', 'humanitarian', 'vaccine', 'covid']
    politics_keywords = ['politics', 'elections', 'relations', 'policy']

    for item in data:
        category_lower = item['category'].lower()
        if any(keyword in category_lower for keyword in health_keywords):
            labels.append('health')
        elif any(keyword in category_lower for keyword in politics_keywords):
            labels.append('politics')
        else:  # Default to business for Finance, Tech, Economy, etc.
            labels.append('business')

    print(f"Successfully loaded {len(documents)} documents and mapped them to {len(set(labels))} primary categories.")
    return documents, labels




def main():
    """
    Main function to run the classifier training pipeline.
    """


    # --- Step 1: Load Data ---
    documents, labels = load_labeled_data(config.LABELED_DATA_FILE)
    if not documents:
        return

    # --- Step 2: Preprocess Data ---
    print("Pre-processing data...")
    preprocessed_docs = [preprocess_text(doc) for doc in documents]
    # --- Step 3: Vectorize Data ---
    print("Vectorizing data using TF-IDF...")
    tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    X = tfidf_vectorizer.fit_transform(preprocessed_docs)
    y = labels
    print(f"Data matrix shape: {X.shape}")

    # --- Step 4: Train and Evaluate SVM Model ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    print("Training the SVM model...")
    svm_classifier = SVC(kernel='linear', probability=True, random_state=42)
    svm_classifier.fit(X_train, y_train)

    y_pred = svm_classifier.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nSVM Model Accuracy: {accuracy:.2f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # --- Step 5: Save the Model and Vectorizer ---
    print("Saving model and vectorizer to disk...")
    with open(config.CLASSIFIER_FILE, 'wb') as f:
        pickle.dump(svm_classifier, f)

    with open(config.VECTORIZER_FILE, 'wb') as f:
        pickle.dump(tfidf_vectorizer, f)

    print(f"  -> Model saved to: {config.CLASSIFIER_FILE}")
    print(f"  -> Vectorizer saved to: {config.VECTORIZER_FILE}")


if __name__ == "__main__":
    main()