# verify_data.py
import json
from collections import Counter


def verify_data_balance(file_path="labeled_data.json"):
    """
    Loads data and counts the final mapped categories to verify balance.
    """
    print(f"Verifying data balance in: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Use the EXACT same mapping logic as the main script
    labels = []
    health_keywords = ['health', 'disease', 'pharma', 'medical', 'nutrition', 'humanitarian', 'vaccine', 'covid']
    politics_keywords = ['politics', 'elections', 'relations', 'policy']

    for item in data:
        category_lower = item['category'].lower()
        if any(keyword in category_lower for keyword in health_keywords):
            labels.append('health')
        elif any(keyword in category_lower for keyword in politics_keywords):
            labels.append('politics')
        else:
            labels.append('business')

    counts = Counter(labels)
    print("\nCategory Counts:")
    for category, count in counts.items():
        print(f"- {category.title()}: {count}")

    total = sum(counts.values())
    print(f"\nTotal Documents: {total}")


if __name__ == "__main__":
    verify_data_balance()