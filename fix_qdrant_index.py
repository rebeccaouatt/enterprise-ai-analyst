# Crée un fichier fix_qdrant_index.py à la racine
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Create payload indexes for filtering
client.create_payload_index(
    collection_name="financial_reports",
    field_name="company",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="financial_reports",
    field_name="year",
    field_schema=models.PayloadSchemaType.INTEGER
)

print("Indexes created successfully!")