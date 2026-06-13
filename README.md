# Enterprise AI Data Analyst

An autonomous AI agent that answers complex business questions by combining SQL queries and semantic search over financial reports.

**Group 12 | Rebecca OUATTARA | Jean -Luc MESSANVI| Aivancity 2026**

---

## Live Endpoint (Google Cloud Run)

```
https://enterprise-ai-analyst-638408101225.europe-west1.run.app
```

Health check:
```
https://enterprise-ai-analyst-638408101225.europe-west1.run.app/health
```

---

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11
- A Gemini API key ([aistudio.google.com](https://aistudio.google.com))
- A Qdrant Cloud account ([cloud.qdrant.io](https://cloud.qdrant.io))

### 1. Clone the repository
```bash
git clone https://github.com/rebeccaouatt/enterprise-ai-analyst.git
cd enterprise-ai-analyst
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your keys
```

```env
API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
```

### 3. Install dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start Docker services
```bash
# Start Qdrant (local)
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Start Redis (Semantic Cache)
docker run -d --name redis -p 6379:6379 redis
```

### 5. Run the ETL Pipeline
```bash
# Create SQL database
python phase1_etl/create_database.py

# Clean and ingest documents into Qdrant
python phase1_etl/ingest_qdrant.py
```

### 6. Run the agent locally
```bash
python -m phase2_agent.agent
```

### 7. Start the API
```bash
uvicorn phase3_deployment.api:api --host 0.0.0.0 --port 8080
```

### 8. Test the API
```bash
# Health check
curl http://localhost:8080/health

# Query the agent
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple total iPhone revenue in 2023?"}'
```

---

## Project Structure

```
enterprise-ai-analyst/
├── data/
│   └── financial.db              # SQLite database (quarterly revenue)
├── phase1_etl/
│   ├── clean_dataset.py          # Text cleaning pipeline
│   ├── create_database.py        # Creates SQL database
│   └── ingest_qdrant.py          # Cleans, embeds and ingests into Qdrant Cloud
├── phase2_agent/
│   ├── agent.py                  # LangGraph ReAct Agent
│   ├── semantic_cache.py         # Redis Semantic Cache (Extra Mile)
│   └── tools/
│       ├── sql_tool.py           # SQL tools with error recovery
│       └── vector_tool.py        # Vector search with metadata filters
├── phase3_deployment/
│   └── api.py                    # FastAPI endpoint + FinOps + Cache
├── phase4_report/
│   ├── REPORT.md                 # Architecture report + RAGAS evaluation
│   └── eval_ragas.py             # RAGAS evaluation script
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local orchestration
├── fix_qdrant_index.py           # Qdrant payload index creation
├── requirements.txt
└── README.md
```

---

## Architecture

The agent uses a **ReAct loop** (Reason + Act) implemented with LangGraph:

```
User Question
     │
     ▼
Semantic Cache (Redis) ← EXTRA MILE
     │
     ├── Cache Hit (similarity >= 0.95) → Instant response, $0.00 cost
     │
     └── Cache Miss
              │
              ▼
     FastAPI /query
              │
              ▼
     LangGraph Agent (Gemini 3 Flash)
              │
              ├── Numerical question → get_database_schema → execute_sql → SQLite
              │
              ├── Qualitative question → search_vector_db → Qdrant Cloud
              │
              └── Complex question → Both tools combined
                                          │
                                          ▼
                                   Store in Redis Cache
```

### Tools

| Tool | Description |
|---|---|
| `get_database_schema` | Queries sqlite_master to discover table structure |
| `execute_sql` | Runs SQL with automatic error recovery loop |
| `search_vector_db` | Extracts metadata filters (Instructor + Pydantic) then runs hybrid vector + metadata search |

---

## Extra Mile: Semantic Caching (Redis)

Agent loops are slow and expensive. This project implements a Semantic Cache:
- Before calling the LangGraph agent, the query is embedded and compared to cached queries
- If cosine similarity >= 0.95, the cached answer is returned instantly at $0.00 cost
- Otherwise, the agent runs and the result is stored in Redis for 24 hours

```bash
# First call: runs the full agent
{"question": "What was Apple iPhone revenue in 2023?"}
→ cache_hit: false, cost: $0.0004, time: 45s

# Second call: returns from cache instantly
{"question": "Apple total iPhone revenue 2023?"}
→ cache_hit: true, cost: $0.00, time: 0.1s
```

---

## Dataset

- **Vector DB:** `virattt/financial-qa-10K` (HuggingFace) — 6,994 cleaned extracts from SEC 10-K filings (70 companies, 2023)
- **SQL DB:** Quarterly revenue data for Apple, Microsoft, Google, Amazon, Meta (2022-2023)

---

## Example Queries

```bash
# SQL query
{"question": "What was Apple's total iPhone revenue in 2023?"}
# → $105.5 billion

# Vector query
{"question": "What did NVIDIA say about AI demand in their 2023 report?"}
# → Detailed answer from the real 10-K filing

# Hybrid query
{"question": "What was Microsoft cloud revenue in Q3 2023 and what did they say about Azure growth?"}
# → $24B + Azure commentary from the annual report
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Gemini 3 Flash Preview |
| Agent | LangGraph ReAct |
| Structured Outputs | Instructor + Pydantic |
| Vector DB | Qdrant Cloud (Frankfurt) |
| Embeddings | all-MiniLM-L6-v2 |
| SQL | SQLite |
| Semantic Cache | Redis (Extra Mile) |
| API | FastAPI |
| Cloud | Google Cloud Run (europe-west1) |
| Repo | GitHub public |