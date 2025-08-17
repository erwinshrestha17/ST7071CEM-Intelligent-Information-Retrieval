# backend/information_retrival/__init__.py
from backend.information_retrival.crawler import crawl_and_extract
from backend.information_retrival.indexer import build_index
from backend.information_retrival.train_classifier import train_and_save_classifier


def run_full_pipeline():
    """
    Executes the entire data processing pipeline in the correct order:
    1. Crawls for publications data.
    2. Builds the search index from the crawled data.
    3. Trains the text classification model.
    """
    print("--- Starting Full Backend Data Pipeline ---")

    try:
        # Step 1: Run the crawler to gather the raw data
        print("\n[STEP 1/3] --- Running Crawler ---")
        crawl_and_extract()
        print("[STEP 1/3] --- Crawler finished ---")

        # Step 2: Build the inverted search index from the crawled data
        print("\n[STEP 2/3] --- Running Indexer ---")
        build_index()
        print("[STEP 2/3] --- Indexer finished ---")

        # Step 3: Train the classifier model
        print("\n[STEP 3/3] --- Training Classifier ---")
        train_and_save_classifier()
        print("[STEP 3/3] --- Classifier training finished ---")

        print("\n✅ --- Full Backend Pipeline Completed Successfully! ---")

    except Exception as e:
        import traceback
        print(f"\n❌ --- An error occurred during the pipeline execution: {e} ---")
        traceback.print_exc()
        print("Pipeline halted.")

# This allows the entire pipeline to be executed by running the package
# from the command line: `python -m backend.information_retrival`
if __name__ == "__main__":
    run_full_pipeline()