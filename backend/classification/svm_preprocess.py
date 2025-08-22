import os
import re
import nltk
from pypdf import PdfReader
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report


# --- Step 0: NLTK Data Download ---
def download_nltk_data():
    """Downloads required NLTK data if not already present."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        print("Downloading necessary NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)


download_nltk_data()


# --- Step 1: Load Documents from Local PDFs ---
def load_documents_from_pdfs(data_folder):
    """
    Loads text from PDF files in a structured directory.
    Each subfolder in data_folder is treated as a category.
    """
    documents = []
    labels = []
    print(f"Loading documents from {data_folder}...")

    # Check if the main data folder exists
    if not os.path.isdir(data_folder):
        print(f"Error: Directory '{data_folder}' not found.")
        print("Please create it and place your PDF files inside category subfolders.")
        return [], []

    for category in os.listdir(data_folder):
        category_path = os.path.join(data_folder, category)
        if os.path.isdir(category_path):
            for filename in os.listdir(category_path):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(category_path, filename)
                    try:
                        reader = PdfReader(file_path)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() or ""

                        if text.strip():  # Ensure the PDF contained readable text
                            documents.append(text)
                            labels.append(category)
                    except Exception as e:
                        print(f"Could not read {filename}: {e}")

    print(f"Successfully loaded {len(documents)} documents from {len(set(labels))} categories.")
    return documents, labels


# IMPORTANT: Set this path to your main data folder
DATA_DIRECTORY = "pdf_data"
documents, labels = load_documents_from_pdfs(DATA_DIRECTORY)

# Exit if no documents were loaded
if not documents:
    exit()

# --- Step 2: Advanced NLP Preprocessing ---
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def preprocess_text(text):
    """Cleans, tokenizes, removes stop words, and lemmatizes text."""
    text = re.sub(r'[^a-z\s]', '', text.lower())
    tokens = text.split()
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return " ".join(lemmatized_tokens)


print("\n--- Pre-processing Data with Advanced NLP ---")
preprocessed_documents = [preprocess_text(doc) for doc in documents]
print(f"Sample of a processed document: {preprocessed_documents[0][:100]}...\n")

# --- Step 3: Convert Text to Numbers (Vectorization) ---
print("--- Vectorizing Data using TF-IDF ---")
tfidf_vectorizer = TfidfVectorizer(max_features=1000)
X = tfidf_vectorizer.fit_transform(preprocessed_documents)
y = labels
print(f"Data has been converted into a matrix of shape: {X.shape}\n")

# --- Step 4: Model Training and Evaluation ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

## --- 4a: Support Vector Machine (SVM) ---
print("--- Training the SVM Model ---")
svm_classifier = SVC(kernel='linear')
svm_classifier.fit(X_train, y_train)
y_pred_svm = svm_classifier.predict(X_test)
print(f"SVM Accuracy: {accuracy_score(y_test, y_pred_svm):.2f}")

## --- 4b: Neural Network (MLP Classifier) ---
print("\n--- Training the Neural Network Model ---")
nn_classifier = MLPClassifier(hidden_layer_sizes=(100,), max_iter=300, random_state=42)
nn_classifier.fit(X_train, y_train)
y_pred_nn = nn_classifier.predict(X_test)
print(f"Neural Network Accuracy: {accuracy_score(y_test, y_pred_nn):.2f}\n")

# --- Step 5: Using the Models to Classify New Documents ---
print("--- Classifying New Documents ---")
new_documents = [
    "The prime minister gave a speech on foreign policy.",
    "Healthy eating can prevent many diseases.",
    "Analysts are optimistic about the financial markets."
]

for doc in new_documents:
    processed_doc = preprocess_text(doc)
    vectorized_doc = tfidf_vectorizer.transform([processed_doc])
    prediction_svm = svm_classifier.predict(vectorized_doc)
    prediction_nn = nn_classifier.predict(vectorized_doc)

    print(f"Document: '{doc}'")
    print(f"   -> SVM Prediction: {prediction_svm[0]}")
    print(f"   -> Neural Network Prediction: {prediction_nn[0]}")