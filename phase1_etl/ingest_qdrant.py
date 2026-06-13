from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import re

# Initialize clients
client = QdrantClient(url="http://localhost:6333")
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

# Extract year from filing string (e.g. "2023_10K" -> 2023)
def extract_year(filing: str) -> int:
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

print(f"Embedding and ingesting {total} documents into Qdrant...")

for i, doc in enumerate(documents):
    ticker = doc['ticker']
    company = TICKER_TO_COMPANY.get(ticker, ticker)
    year = extract_year(doc['filing'])
    text = doc['context']

    vector = embedder.encode(text).tolist()

    points.append(
        models.PointStruct(
            id=i,
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

    # Upload batch
    if len(points) == BATCH_SIZE:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"Ingested {i+1}/{total} documents...")
        points = []

# Upload remaining points
if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"\nDone! {total} documents ingested into '{COLLECTION_NAME}'")
print(f"Collection info: {client.get_collection(COLLECTION_NAME)}")