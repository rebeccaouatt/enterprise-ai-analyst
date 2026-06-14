import os
import instructor
from pydantic import BaseModel, Field
from typing import Optional
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Clients
llm_client = instructor.from_openai(
    OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    ),
    mode=instructor.Mode.JSON
)

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Lazy loading embedder
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

# Pydantic model for query parsing
class SearchIntent(BaseModel):
    company_filter: Optional[str] = Field(
        description="The specific company name mentioned, if any. Otherwise null."
    )
    year_filter: Optional[int] = Field(
        description="The specific year mentioned, if any. Otherwise null."
    )
    semantic_query: str = Field(
        description="The core question to search for, optimized for vector search."
    )

@tool
def search_vector_db(query: str) -> str:
    """Search the financial reports vector database to answer qualitative questions about companies."""
    print(f"\n[TOOL] Vector search for: {query}")

    # Extract filters using LLM
    intent = llm_client.chat.completions.create(
        model="gemini-3-flash-preview",
        response_model=SearchIntent,
        messages=[{"role": "user", "content": f"Extract search filters from this query: {query}"}]
    )

    print(f"[TOOL] Filters -> Company: {intent.company_filter}, Year: {intent.year_filter}")
    print(f"[TOOL] Semantic query: {intent.semantic_query}")

    # Build Qdrant filters
    qdrant_filters = []
    if intent.company_filter:
        qdrant_filters.append(
            models.FieldCondition(
                key="company",
                match=models.MatchValue(value=intent.company_filter)
            )
        )
    if intent.year_filter:
        qdrant_filters.append(
            models.FieldCondition(
                key="year",
                match=models.MatchValue(value=intent.year_filter)
            )
        )

    strict_filter = models.Filter(must=qdrant_filters) if qdrant_filters else None

    # Embed and search
    query_vector = get_embedder().encode(intent.semantic_query).tolist()
    response = qdrant.query_points(
        collection_name="financial_reports",
        query=query_vector,
        query_filter=strict_filter,
        limit=3
    )

    # Format results
    results = []
    for hit in response.points:
        results.append(
            f"Company: {hit.payload['company']} | Year: {hit.payload['year']}\n"
            f"Text: {hit.payload['text']}"
        )

    if not results:
        return "No relevant documents found."

    return "\n\n---\n\n".join(results)