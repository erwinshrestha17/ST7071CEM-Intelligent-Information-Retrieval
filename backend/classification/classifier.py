import json
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Assuming classification_preprocessing.py is in the same directory or accessible
from classification_preprocessing import preprocess_text


def load_labeled_data(file_path):
    """
    Loads documents and labels from the JSON file.
    """
    file_path = Path(file_path)
    print(f"Loading labeled data from {file_path}...")
    if not file_path.exists():
        print(f"Error: Labeled data file not found at {file_path}")
        return [], []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = [item['title'] + ' ' + item['summary'] for item in data]

    # Mapping logic to define the final three categories
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

    print(f"Successfully loaded {len(documents)} documents.")
    return documents, labels


# MODIFICATION: New function to plot the confusion matrix
def plot_confusion_matrix(cm, class_names, filename="confusion_matrix.png"):
    """
    Creates, displays, and saves a confusion matrix plot using seaborn.
    """
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.title('Confusion Matrix')
    plt.tight_layout()  # Adjust layout to make sure everything fits
    plt.savefig(filename)
    print(f"\nConfusion matrix plot saved to: {filename}")


def main():
    """
    Main function to run the classifier training pipeline.
    """
    # --- Step 1: Load Data ---
    documents, labels = load_labeled_data("labeled_data.json")
    if not documents:
        return

    # --- Step 2: Preprocess Data ---
    print("Pre-processing data...")
    preprocessed_docs = [preprocess_text(doc) for doc in documents]

    # --- Step 3: Vectorize Data ---
    print("Vectorizing data using TF-IDF...")
    tfidf_vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), sublinear_tf=True)
    X = tfidf_vectorizer.fit_transform(preprocessed_docs)
    y = labels

    # --- Step 4: Train and Evaluate Naïve Bayes Model ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    print("Searching for the best Naïve Bayes model using GridSearchCV...")
    param_grid = {'alpha': [0.1, 0.5, 1.0, 1.5, 2.0]}
    grid_search = GridSearchCV(MultinomialNB(), param_grid, refit=True, verbose=1, cv=5)
    grid_search.fit(X_train, y_train)

    best_classifier = grid_search.best_estimator_
    print(f"\nBest parameters found: {grid_search.best_params_}")

    y_pred = best_classifier.predict(X_test)

    # --- Evaluation Metrics ---
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nFINAL Naïve Bayes Model Accuracy: {accuracy:.2f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    print("\nConfusion Matrix (Text):")
    cm = confusion_matrix(y_test, y_pred)
    class_labels = best_classifier.classes_
    print(cm)
    print(f"\nLabels: {class_labels}")

    # MODIFICATION: Call the new function to generate and save the plot
    plot_confusion_matrix(cm, class_labels)

    # --- Step 5: Save the BEST Model and Vectorizer ---
    classifier_path = Path("naive_bayes_classifier.pkl")
    vectorizer_path = Path("tfidf_vectorizer_nb.pkl")

    print("\nSaving best model and vectorizer to disk...")
    with open(classifier_path, 'wb') as f:
        pickle.dump(best_classifier, f)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(tfidf_vectorizer, f)

    print(f"  -> Model saved to: {classifier_path}")
    print(f"  -> Vectorizer saved to: {vectorizer_path}")


if __name__ == "__main__":
    main()