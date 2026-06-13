import re
from datasets import load_dataset

def clean_text(text: str) -> str:
    """
    Clean a financial report text extract.
    - Remove excessive whitespace and newlines
    - Remove special characters that add no meaning
    - Normalize quotes and dashes
    - Remove very short fragments (less than 20 chars)
    """
    if not text or len(text.strip()) < 20:
        return ""

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E]', ' ', text)

    # Normalize quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')

    # Normalize dashes
    text = text.replace('\u2013', '-').replace('\u2014', '-')

    # Remove repeated punctuation
    text = re.sub(r'([.!?])\1+', r'\1', text)

    # Remove lines that are just numbers or symbols
    text = re.sub(r'^\W+$', '', text)

    # Final strip
    text = text.strip()

    return text


def clean_dataset():
    print("Loading dataset from Hugging Face...")
    ds = load_dataset("virattt/financial-qa-10K")
    documents = ds['train']

    total = len(documents)
    cleaned = 0
    removed = 0

    print(f"Cleaning {total} documents...")

    clean_results = []
    for doc in documents:
        original_text = doc['context']
        cleaned_text = clean_text(original_text)

        if not cleaned_text:
            removed += 1
            continue

        clean_results.append({
            "ticker": doc['ticker'],
            "filing": doc['filing'],
            "question": doc['question'],
            "answer": doc['answer'],
            "context_original": original_text,
            "context_cleaned": cleaned_text,
            "chars_removed": len(original_text) - len(cleaned_text)
        })
        cleaned += 1

    print(f"\nCleaning complete:")
    print(f"  Total documents  : {total}")
    print(f"  Cleaned          : {cleaned}")
    print(f"  Removed (empty)  : {removed}")

    avg_chars_removed = sum(r['chars_removed'] for r in clean_results) / len(clean_results)
    print(f"  Avg chars removed: {avg_chars_removed:.1f} per document")

    # Show sample
    print("\nSample cleaned document:")
    sample = clean_results[0]
    print(f"  Ticker  : {sample['ticker']}")
    print(f"  Original: {sample['context_original'][:100]}...")
    print(f"  Cleaned : {sample['context_cleaned'][:100]}...")

    return clean_results


if __name__ == "__main__":
    clean_dataset()