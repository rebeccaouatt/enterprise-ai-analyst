# Enterprise AI Data Analyst

An autonomous AI agent that answers complex business questions by combining SQL queries and semantic search over financial reports.

**Group 12 | Rebecca OUATTARA | Jean -Luc MESSANVI| Aivancity 2026**

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

### 4. Run the ETL Pipeline
```bash
# Create SQL database
python phase1_etl/create_database.py

# Ingest documents into Qdrant
python phase1_etl/ingest_qdrant.py
```

### 5. Run the agent locally
```bash
python -m phase2_agent.agent
```

### 6. Start the API
```bash
uvicorn phase3_deployment.api:api --host 0.0.0.0 --port 8080
```

### 7. Test the API
```bash
# Health check
curl http://localhost:8080/health

# Query the agent
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple total iPhone revenue in 2023?"}'
```

---

## Live Endpoint (Google Cloud Run)

```
https://enterprise-ai-analyst-638408101225.europe-west1.run.app
```

```bash
curl -X POST https://enterprise-ai-analyst-638408101225.europe-west1.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What did NVIDIA say about AI demand in 2023?"}'
```

---

## Project Structure

```
enterprise-ai-analyst/
├── data/
│   └── financial.db              # SQLite database (quarterly revenue)
├── phase1_etl/
│   ├── create_database.py        # Creates SQL database
│   └── ingest_qdrant.py          # Embeds and ingests into Qdrant Cloud
├── phase2_agent/
│   ├── agent.py                  # LangGraph ReAct Agent
│   └── tools/
│       ├── sql_tool.py           # SQL tools with error recovery
│       └── vector_tool.py        # Vector search with metadata filters
├── phase3_deployment/
│   └── api.py                    # FastAPI endpoint + FinOps tracking
├── phase4_report/
│   └── REPORT.md                 # Architecture report + RAGAS evaluation
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local orchestration
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
```

### Tools

| Tool | Description |
|---|---|
| `get_database_schema` | Queries sqlite_master to discover table structure |
| `execute_sql` | Runs SQL with automatic error recovery loop |
| `search_vector_db` | Extracts metadata filters (Instructor + Pydantic) then runs hybrid vector + metadata search |

---

## Dataset

- **Vector DB:** `virattt/financial-qa-10K` (HuggingFace) — 7,000 real extracts from SEC 10-K filings (70 companies, 2023)
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
| API | FastAPI |
| Cloud | Google Cloud Run |
