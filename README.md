# Enterprise AI Data Analyst

An autonomous AI agent that answers complex business questions by combining SQL queries and semantic search over financial reports.

**Group 12 | Rebecca OUATTARA & Jean-Luc MESSANVI | Aivancity 2026**
**GitHub:** https://github.com/rebeccaouatt/enterprise-ai-analyst
**Live API:** https://enterprise-ai-analyst-638408101225.europe-west1.run.app/docs

---

## Live Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns `{"status":"ok"}` — service is running |
| `/docs` | GET | Swagger UI — test all endpoints interactively |
| `/query` | POST | Send a question, get an AI-powered answer |

> **Note:** The root URL `/` returns `{"detail":"Not Found"}` — this is expected FastAPI behavior.
> Always use `/health`, `/docs`, or `/query`.

---

## Local Setup (Full Pipeline)

### Prerequisites
- Docker Desktop (running)
- Python 3.11
- A Gemini API key: [aistudio.google.com](https://aistudio.google.com)
- A Qdrant Cloud account: [cloud.qdrant.io](https://cloud.qdrant.io)

### 1. Clone the repository
```powershell
git clone https://github.com/rebeccaouatt/enterprise-ai-analyst.git
cd enterprise-ai-analyst
```

### 2. Create virtual environment
```powershell
python -m venv venv
```

Activate (Windows PowerShell):
```powershell
# If execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file at the root:
```env
API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
```

### 5. Start Docker services
```powershell
# Qdrant Vector DB (local development)
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Redis Semantic Cache (Extra Mile)
docker run -d --name redis -p 6379:6379 redis
```

### 6. Run ETL Pipeline
```powershell
# Step 1: Create SQL database (64 rows, 5 companies)
python phase1_etl/create_database.py

# Step 2: Clean and ingest 6,994 documents into Qdrant Cloud
python phase1_etl/ingest_qdrant.py

# Step 3: Create payload indexes for fast filtering
python fix_qdrant_index.py
```

### 7. Test the agent locally
```powershell
python -m phase2_agent.agent
```

### 8. Start the API locally
```powershell
uvicorn phase3_deployment.api:api --host 0.0.0.0 --port 8080
```

### 9. Test the API (Windows PowerShell)
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8080/health"

# SQL query
Invoke-WebRequest -Uri "http://localhost:8080/query" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"question": "What was Apple total iPhone revenue in 2023?"}'

# Vector query
Invoke-WebRequest -Uri "http://localhost:8080/query" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"question": "What did NVIDIA say about AI demand in 2023?"}'

# Test live Cloud Run endpoint
Invoke-WebRequest -Uri "https://enterprise-ai-analyst-638408101225.europe-west1.run.app/query" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"question": "What was Apple total iPhone revenue in 2023?"}'
```

> Alternatively, use the Swagger UI at `/docs` to test interactively from the browser.

### 10. Run RAGAS Evaluation
```powershell
python -m phase4_report.eval_ragas
```

---

## Cloud Deployment (Google Cloud Run)

### Prerequisites
- Google Cloud SDK installed: [cloud.google.com/sdk](https://cloud.google.com/sdk)
- GCP project with billing enabled

```powershell
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID `
  --member="serviceAccount:YOUR_COMPUTE_SA@developer.gserviceaccount.com" `
  --role="roles/storage.objectViewer"

# Deploy
gcloud run deploy enterprise-ai-analyst `
  --source . `
  --region europe-west1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars "API_KEY=your_gemini_key,QDRANT_URL=your_qdrant_url,QDRANT_API_KEY=your_qdrant_key" `
  --memory 2Gi `
  --timeout 300
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
│   └── ingest_qdrant.py          # Cleans, embeds and ingests into Qdrant
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
│   ├── eval_ragas.py             # RAGAS evaluation script
│   └── eval_results.md           # Real evaluation results (1.0/1.0)
├── fix_qdrant_index.py           # Creates Qdrant payload indexes
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local orchestration
├── requirements.txt
└── README.md
```

---

## Architecture

```
User Question
     │
     ▼
Semantic Cache (Redis) <- EXTRA MILE
     │
     ├── Cache Hit (similarity >= 0.95) -> Instant response, $0.00
     │
     └── Cache Miss
              │
              ▼
     LangGraph ReAct Agent (Gemini 3 Flash)
              │
              ├── SQL question -> get_schema -> execute_sql -> SQLite
              ├── Qualitative  -> search_vector_db -> Qdrant Cloud
              └── Complex      -> Both tools combined
```

### Tools

| Tool | Description |
|---|---|
| `get_database_schema` | Discovers table structure via sqlite_master |
| `execute_sql` | Runs SQL with automatic error recovery loop |
| `search_vector_db` | Extracts metadata filters (Instructor+Pydantic) + hybrid search |

---

## Example Queries & Results

| Query | Tool | Answer |
|---|---|---|
| "What was Apple's total iPhone revenue in 2023?" | SQL | $105.5 billion |
| "What did NVIDIA say about AI demand?" | Vector | Data Center +41% YoY, GenAI demand |
| "Microsoft cloud Q3 2023 + Azure growth?" | SQL + Vector | $24B + hybrid cloud commentary |
| "Main risks in Meta's 2023 report?" | Vector | Advertising, privacy, Reality Labs |
| "Compare Amazon AWS Q1 vs Q3 2023" | SQL | $21.4B -> $23.4B (+9.35%) |

---

## RAGAS Evaluation Results

| Metric | Score |
|---|---|
| Average Faithfulness | 1.00 / 1.00 |
| Average Answer Relevance | 1.00 / 1.00 |

---

## Extra Mile: Semantic Caching (Redis)

Agent loops are slow and expensive. This project implements a Semantic Cache using Redis:
- Before calling the LangGraph agent, the query is embedded and compared to cached queries
- If cosine similarity >= 0.95, the cached answer is returned instantly at $0.00 cost
- Otherwise, the agent runs and the result is stored in Redis for 24 hours
- If Redis is not available, the agent runs normally (graceful fallback)

```
First call:  "What was Apple iPhone revenue in 2023?"
             -> cache_hit: false | time: ~45s | cost: ~$0.0004

Second call: "Apple total iPhone revenue 2023?"
             -> cache_hit: true  | time: ~0.1s | cost: $0.00
             -> Similarity: 0.979
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Gemini 3 Flash Preview |
| Agent | LangGraph ReAct |
| Structured Outputs | Instructor + Pydantic |
| Vector DB | Qdrant Cloud (Frankfurt) |
| Embeddings | all-MiniLM-L6-v2 (HuggingFace) |
| SQL | SQLite |
| Semantic Cache | Redis (Extra Mile) |
| API | FastAPI + Uvicorn |
| Cloud | Google Cloud Run (europe-west1) |
| OS | Windows 11 / PowerShell |

---

## Dataset

- **Vector DB:** `virattt/financial-qa-10K` (HuggingFace) — 6,994 cleaned extracts from real SEC 10-K filings (70 companies, 2023)
- **SQL DB:** Quarterly revenue for Apple, Microsoft, Google, Amazon, Meta (2022-2023)