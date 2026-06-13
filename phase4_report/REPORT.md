# Enterprise AI Data Analyst — Architecture Report

**Group 12 | Rebecca OUATTARA | Jean -Luc MESSANVI **
**Aivancity : Data Engineering & CLOUD COMPUTING  2026**

---

## 1. System Architecture

### Overview

The Enterprise AI Data Analyst is a production-grade autonomous agent capable of answering complex business questions by combining two data sources: a SQL database for structured numerical data and a Vector Database for unstructured financial reports.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                               │
│   "What was Apple's iPhone revenue in 2023, and what did        │
│    their report say about supply chain risks?"                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                             │
│                  POST /query  GET /health                       │
│              Deployed on Google Cloud Run                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Semantic Cache (Redis) <- EXTRA MILE               │
│   Cosine Similarity >= 0.95 -> Return cached answer instantly  │
└────────────────────────────┬────────────────────────────────────┘
                             │ Cache Miss
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LangGraph ReAct Agent                          │
│                  LLM: Gemini 3 Flash Preview                    │
│                                                                 │
│   START -> [Agent] -> (tool_calls?) -> [Tools] -> [Agent] -> END│
│                            ↑__________________|                 │
└──────────┬──────────────────┬────────────────┬─────────────────┘
           │                  │                │
           ▼                  ▼                ▼
┌──────────────┐  ┌────────────────┐  ┌───────────────────────┐
│get_db_schema │  │  execute_sql   │  │   search_vector_db    │
│              │  │                │  │                       │
│Query         │  │Run SQL query   │  │ 1. Extract filters    │
│sqlite_master │  │with error      │  │    (Instructor +      │
│              │  │recovery loop   │  │    Pydantic)          │
└──────┬───────┘  └───────┬────────┘  │ 2. Build Qdrant       │
       │                  │           │    metadata filters   │
       ▼                  ▼           │ 3. Hybrid vector +    │
┌─────────────────────┐   │           │    metadata search    │
│   SQLite Database   │<──┘           └──────────┬────────────┘
│   financial.db      │                          │
│   quarterly_revenue │                          ▼
│   64 rows           │              ┌───────────────────────┐
│   5 companies       │              │    Qdrant Cloud       │
└─────────────────────┘              │    Frankfurt          │
                                     │    6,994 documents    │
                                     │    10-K SEC Reports   │
                                     │    all-MiniLM-L6-v2   │
                                     └───────────────────────┘
```

### ETL Pipeline

```
Hugging Face Dataset                    SQLite Database
virattt/financial-qa-10K                financial.db
        │                                     │
        ▼                                     ▼
  Clean text                       Create quarterly_revenue
  (clean_dataset.py)               (company, year, quarter,
  6 documents removed               segment, revenue_usd_billions)
        │                                     │
        ▼                                     ▼
  Embed with                           64 rows inserted
  all-MiniLM-L6-v2                     (Apple, Microsoft, Google,
  (384 dimensions)                      Amazon, Meta)
        │
        ▼
  Attach metadata
  {company, ticker,
   year, filing, text}
        │
        ▼
  Create payload indexes
  (company: keyword,
   year: integer)
        │
        ▼
  Upsert to Qdrant Cloud
  (Frankfurt, Free Tier)
  Collection: financial_reports
  6,994 documents ingested
```

---

## 2. RAGAS Evaluation

Five test queries were run through the deployed agent. Outputs were manually graded for:
- **Faithfulness** (0-1): Is the answer grounded in the retrieved context? No hallucinations?
- **Answer Relevance** (0-1): Does the answer directly address the question?

| # | Query | Tool Used | Faithfulness | Answer Relevance | Notes |
|---|-------|-----------|:---:|:---:|-------|
| 1 | What was Apple's total iPhone revenue in 2023? | SQL | 1.0 | 1.0 | Exact SQL result: $105.5B |
| 2 | What did NVIDIA say about AI demand in their 2023 report? | Vector | 1.0 | 1.0 | Grounded in real 10-K extracts |
| 3 | What was Microsoft's cloud revenue in Q3 2023 and what did they say about Azure growth? | SQL + Vector | 1.0 | 1.0 | Hybrid query: $24B + Azure commentary |
| 4 | What were the main risks mentioned by Meta in their 2023 annual report? | Vector | 1.0 | 1.0 | Risk factors retrieved from 10-K |
| 5 | Compare Amazon AWS revenue between Q1 and Q3 2023 | SQL | 1.0 | 1.0 | $21.4B Q1 -> $23.4B Q3 (+9.35%) |

**Average Faithfulness: 1.00 / 1.00**
**Average Answer Relevance: 1.00 / 1.00**

### Key Observations

- The SQL error recovery loop worked correctly: when the agent guessed the wrong segment name, it read the error, queried the schema, and corrected its SQL automatically.
- The Self-Querying Retriever (Instructor + Pydantic) successfully extracted metadata filters (`company_filter`, `year_filter`) from natural language queries before executing vector search, preventing false positives from pure semantic search.
- Hybrid queries combining SQL and Vector DB produced the most comprehensive answers.
- All 5 queries scored perfect 1.0 on both Faithfulness and Answer Relevance.

---

## 3. Cost Analysis

### Token Cost per Query (Gemini 3 Flash Preview)

| Query Type | Avg Input Tokens | Avg Output Tokens | Estimated Cost |
|---|:---:|:---:|:---:|
| SQL only | ~1,200 | ~150 | ~$0.000135 |
| Vector only | ~2,500 | ~400 | ~$0.000308 |
| Hybrid (SQL + Vector) | ~3,800 | ~600 | ~$0.000465 |
| Cache Hit (Redis) | 0 | 0 | $0.000000 |

Pricing: $0.075 per 1M input tokens, $0.30 per 1M output tokens (Gemini Flash).

**Estimated cost per 100 queries (mixed, no cache): ~$0.030**
**Estimated cost per 100 queries (with 80% cache hit rate): ~$0.006**

### GCP Cloud Run Credits Consumed

| Resource | Usage | Cost |
|---|---|---|
| Cloud Build (6 builds) | ~60 min compute | ~$0.10 |
| Cloud Run (requests) | Free tier (2M req/month) | $0.00 |
| Artifact Registry | ~2GB storage | ~$0.04 |
| **Total** | | **~$0.14** |

Cloud Run free tier covers all inference traffic for this project scale.
Self-hosting via Cloud Run is significantly cheaper than managed API providers at scale.

---

## 4. Technical Stack

| Component | Technology |
|---|---|
| LLM | Gemini 3 Flash Preview |
| Agent Framework | LangGraph |
| Structured Outputs | Instructor + Pydantic |
| Vector Database | Qdrant Cloud (Frankfurt, Free Tier) |
| Embedding Model | all-MiniLM-L6-v2 (HuggingFace, local) |
| SQL Database | SQLite |
| Semantic Cache | Redis (Extra Mile) |
| Dataset | virattt/financial-qa-10K (HuggingFace) |
| API | FastAPI + Uvicorn |
| Container | Docker |
| Cloud | Google Cloud Run (europe-west1) |
| Repository | GitHub (public) |
| Language | Python 3.11 |

---

## 5. Data Sources

### Vector Database (Qdrant Cloud)
- **Source:** `virattt/financial-qa-10K` on HuggingFace
- **Content:** 6,994 real extracts from 10-K annual reports filed with the SEC (6 empty documents removed by cleaning pipeline)
- **Companies:** 70 companies including Apple (AAPL), Microsoft (MSFT), Google (GOOGL), Amazon (AMZN), Meta (META), NVIDIA (NVDA), Tesla (TSLA), and 63 others
- **Year:** 2023 fiscal year reports
- **Metadata:** company, ticker, year, filing, text, question, answer
- **Indexes:** Payload indexes on `company` (keyword) and `year` (integer) for fast hybrid filtering

### SQL Database (SQLite)
- **Content:** Quarterly revenue data reconstructed from public financial reports
- **Companies:** Apple, Microsoft, Google, Amazon, Meta
- **Period:** Q1 and Q3 2022-2023
- **Segments:** iPhone, Mac, iPad, Wearables, Services, Productivity, Cloud, Personal, Search, YouTube, AWS, Advertising

*Note: SQL revenue figures are approximations based on publicly available SEC 10-K filings and earnings press releases.*

---

## 6. Extra Mile: Semantic Caching (Redis)

### Motivation
Agent loops are slow and expensive. Every query to the LangGraph agent costs tokens and takes 30-60 seconds. If two users ask similar questions, the second user should get an instant response without calling the LLM.

### Architecture

```
User Query
    │
    ▼
Encode query with all-MiniLM-L6-v2
    │
    ▼
Search Redis cache for similar vectors
    │
    ├── Cosine Similarity >= 0.95 -> CACHE HIT -> Return instantly ($0.00)
    │
    └── Cosine Similarity < 0.95 -> CACHE MISS -> Run LangGraph Agent
                                                        │
                                                        ▼
                                                 Store result in Redis
                                                 (TTL: 24 hours)
```

### Implementation
- **Cache store:** Redis (Docker container, port 6379)
- **Similarity metric:** Cosine Similarity on all-MiniLM-L6-v2 embeddings (384 dims)
- **Threshold:** 0.95 cosine similarity
- **TTL:** 24 hours per cached entry
- **Key:** `cache:{hash(query)}`

### Test Results

```
Query 1: "What was Apple iPhone revenue in 2023?"
-> [CACHE STORED] Query cached for 24h

Query 2: "What was Apple total iPhone revenue 2023?"
-> [CACHE HIT] Similarity: 0.9790 - returning cached answer
-> Cost: $0.00 | Time: ~0.1s (vs ~45s without cache)
```

### API Response with Cache Hit
```json
{
  "question": "What was Apple total iPhone revenue 2023?",
  "answer": "Apple's total iPhone revenue in 2023 was $105.5 billion.",
  "token_cost_usd": 0.0,
  "execution_time_seconds": 0.12,
  "cache_hit": true
}
```

### Impact
- **Cost reduction:** 100% for cached queries ($0.00 vs ~$0.0004)
- **Latency reduction:** 99%+ (0.1s vs 45s)
- **Use case:** Enterprise deployments where multiple users ask similar business questions