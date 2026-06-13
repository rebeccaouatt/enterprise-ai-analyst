import json
import numpy as np
import os
from sentence_transformers import SentenceTransformer

# Redis connection - optional
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_client = redis.from_url(REDIS_URL, decode_responses=False)
    cache_client.ping()
    REDIS_AVAILABLE = True
    print("[CACHE] Redis connected successfully")
except Exception:
    cache_client = None
    REDIS_AVAILABLE = False
    print("[CACHE] Redis not available - caching disabled")

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

SIMILARITY_THRESHOLD = 0.95
CACHE_TTL = 86400  # 24 hours

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def get_cached_response(query: str):
    """Check if a semantically similar query exists in cache."""
    if not REDIS_AVAILABLE:
        return None

    try:
        query_vector = get_embedder().encode(query)
        keys = cache_client.keys("cache:*")
        
        best_score = 0.0
        best_answer = None

        for key in keys:
            data = cache_client.get(key)
            if not data:
                continue
            entry = json.loads(data)
            cached_vector = np.array(entry["vector"])
            score = cosine_similarity(query_vector, cached_vector)
            if score > best_score:
                best_score = score
                best_answer = entry["answer"]

        if best_score >= SIMILARITY_THRESHOLD:
            print(f"\n[CACHE HIT] Similarity: {best_score:.4f}")
            return best_answer

        return None
    except Exception as e:
        print(f"[CACHE ERROR] {e}")
        return None

def cache_response(query: str, answer: str):
    """Store a query-answer pair in Redis cache."""
    if not REDIS_AVAILABLE:
        return

    try:
        vector = get_embedder().encode(query).tolist()
        entry = json.dumps({"query": query, "answer": answer, "vector": vector})
        key = f"cache:{hash(query)}"
        cache_client.setex(key, CACHE_TTL, entry)
        print(f"\n[CACHE STORED] Query cached for 24h")
    except Exception as e:
        print(f"[CACHE ERROR] {e}")