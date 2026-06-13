import os
import re
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Initialize Qdrant Cloud client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = "financial_reports"

# Load embedding model
print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Map tickers to company names
TICKER_TO_COMPANY = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google",
    "AMZN": "Amazon", "META": "Meta", "NVDA": "NVIDIA",
    "TSLA": "Tesla", "NFLX": "Netflix", "IBM": "IBM",
    "JPM": "JPMorgan", "BAC": "Bank of America", "GS": "Goldman Sachs",
    "JNJ": "Johnson & Johnson", "PG": "Procter & Gamble",
    "KO": "Coca-Cola", "WMT": "Walmart", "HD": "Home Depot",
    "COST": "Costco", "SBUX": "Starbucks", "NKE": "Nike",
    "AMD": "AMD", "INTU": "Intuit", "CRM": "Salesforce",
    "AVGO": "Broadcom", "CMCSA": "Comcast", "T": "AT&T",
    "ABBV": "AbbVie", "LLY": "Eli Lilly", "UNH": "UnitedHealth",
    "CVS": "CVS Health", "HUM": "Humana", "GILD": "Gilead",
    "DAL": "Delta Airlines", "FDX": "FedEx", "GM": "General Motors",
    "F": "Ford", "CAT": "Caterpillar", "GIS": "General Mills",
    "HSY": "Hershey", "KR": "Kroger", "DLTR": "Dollar Tree",
    "EBAY": "eBay", "ETSY": "Etsy", "ABNB": "Airbnb",
    "PTON": "Peloton", "GME": "GameStop", "AMC": "AMC",
    "LULU": "Lululemon", "PLTR": "Palantir", "EA": "EA",
    "HAS": "Hasbro", "GRMN": "Garmin", "HPQ": "HP",
    "HPE": "HPE", "ICE": "ICE", "IRM": "Iron Mountain",
    "AXP": "American Express", "V": "Visa", "SCHW": "Schwab",
    "BRK-A": "Berkshire Hathaway", "CB": "Chubb",
    "CVX": "Chevron", "ENPH": "Enphase", "EFX": "Equifax",
    "AZO": "AutoZone", "CMG": "Chipotle", "DVA": "DaVita",
    "HLT": "Hilton", "LVS": "Las Vegas Sands",
}

def clean_text(text: str) -> str:
    """Clean a financial report text extract before ingestion."""
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
    return text.strip()

def extract_year(filing: str) -> int:
    import re
    match = re.search(r'\d{4}', filing)
    return int(match.group()) if match else 2023

# Create collection (reset if exists)
if client.collection_exists(COLLECTION_NAME):
    client.delete_collection(COLLECTION_NAME)

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(
        size=384,
        distance=models.Distance.COSINE
    )
)

# Load dataset
print("Loading dataset from Hugging Face...")
ds = load_dataset("virattt/financial-qa-10K")
documents = ds['train']

# Embed and ingest in batches
BATCH_SIZE = 100
points = []
total = len(documents)
ingested = 0
skipped = 0

print(f"Cleaning, embedding and ingesting {total} documents into Qdrant Cloud...")

for i, doc in enumerate(documents):
    # Clean text before ingestion
    text = clean_text(doc['context'])
    if not text:
        skipped += 1
        continue

    ticker = doc['ticker']
    company = TICKER_TO_COMPANY.get(ticker, ticker)
    year = extract_year(doc['filing'])

    vector = embedder.encode(text).tolist()

    points.append(
        models.PointStruct(
            id=ingested,
            vector=vector,
            payload={
                "company": company,
                "ticker": ticker,
                "year": year,
                "filing": doc['filing'],
                "text": text,
                "question": doc['question'],
                "answer": doc['answer']
            }
        )
    )
    ingested += 1

    if len(points) == BATCH_SIZE:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"Ingested {ingested}/{total} documents...")
        points = []

if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"\nDone!")
print(f"  Ingested : {ingested}")
print(f"  Skipped  : {skipped}")
print(f"Collection: '{COLLECTION_NAME}' on Qdrant Cloud")