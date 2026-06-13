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
│                  LangGraph ReAct Agent                          │
│                  LLM: Gemini 3 Flash Preview                    │
│                                                                 │
│   START → [Agent] → (tool_calls?) → [Tools] → [Agent] → END   │
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
│   SQLite Database   │◄──┘           └──────────┬────────────┘
│   financial.db      │                          │
│   quarterly_revenue │                          ▼
│   64 rows           │              ┌───────────────────────┐
│   5 companies       │              │    Qdrant Cloud       │
└─────────────────────┘              │    Frankfurt          │
                                     │    7,000 documents    │
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
  Load 7,000 contexts              Create quarterly_revenue
        │                          (company, year, quarter,
        ▼                           segment, revenue_usd_billions)
  Embed with                                │
  all-MiniLM-L6-v2                          ▼
  (384 dimensions)                   64 rows inserted
        │                            (Apple, Microsoft, Google,
        ▼                             Amazon, Meta)
  Attach metadata
  {company, ticker,
   year, filing, text}
        │
        ▼
  Upsert to Qdrant Cloud
  (Frankfurt, Free Tier)
  Collection: financial_reports
```

---

## 2. RAGAS Evaluation

Five test queries were run through the deployed agent. Outputs were manually graded for:
- **Faithfulness** (0-1): Is the answer grounded in the retrieved context? No hallucinations?
- **Answer Relevance** (0-1): Does the answer directly address the question?

| # | Query | Tool Used | Faithfulness | Answer Relevance | Notes |
|---|-------|-----------|:---:|:---:|-------|
| 1 | What was Apple's total iPhone revenue in 2023? | SQL | 1.0 | 1.0 | Exact SQL result: $105.5B |
| 2 | What did NVIDIA say about AI demand in their 2023 report? | Vector | 0.9 | 1.0 | Grounded in 10-K extracts |
| 3 | What was Microsoft's cloud revenue in Q3 2023 and what did they say about Azure growth? | SQL + Vector | 1.0 | 1.0 | Hybrid query combining both sources |
| 4 | What were the main risks mentioned by Meta in their 2023 annual report? | Vector | 0.9 | 0.9 | Context retrieved correctly |
| 5 | Compare Amazon AWS revenue between Q1 and Q3 2023 | SQL | 1.0 | 1.0 | SQL self-corrected schema first |

**Average Faithfulness: 0.96 / 1.0**
**Average Answer Relevance: 0.98 / 1.0**

### Key Observations

- The SQL error recovery loop worked correctly: when the agent guessed the wrong segment name, it read the error, queried the schema, and corrected its SQL automatically.
- The Self-Querying Retriever (Instructor + Pydantic) successfully extracted metadata filters (`company_filter`, `year_filter`) from natural language queries before executing vector search, preventing false positives from pure semantic search.
- Hybrid queries combining SQL and Vector DB produced the most comprehensive answers.

---

## 3. Cost Analysis

### Token Cost per Query (Gemini 3 Flash Preview)

| Query Type | Avg Input Tokens | Avg Output Tokens | Estimated Cost |
|---|:---:|:---:|:---:|
| SQL only | ~1,200 | ~150 | ~$0.000135 |
| Vector only | ~2,500 | ~400 | ~$0.000308 |
| Hybrid (SQL + Vector) | ~3,800 | ~600 | ~$0.000465 |

Pricing: $0.075 per 1M input tokens, $0.30 per 1M output tokens (Gemini Flash).

**Estimated cost per 100 queries (mixed): ~$0.030**

### GCP Cloud Run Credits Consumed

| Resource | Usage | Cost |
|---|---|---|
| Cloud Build (3 builds) | ~33 min compute | ~$0.05 |
| Cloud Run (requests) | Free tier (2M req/month) | $0.00 |
| Artifact Registry | ~2GB storage | ~$0.04 |
| **Total** | | **~$0.09** |

Cloud Run free tier covers all inference traffic for this project scale.
Self-hosting via Cloud Run is significantly cheaper than API providers at scale.

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
- **Content:** 7,000 real extracts from 10-K annual reports filed with the SEC
- **Companies:** 70 companies including Apple (AAPL), Microsoft (MSFT), Google (GOOGL), Amazon (AMZN), Meta (META), NVIDIA (NVDA), Tesla (TSLA), and 63 others
- **Year:** 2023 fiscal year reports
- **Metadata:** company, ticker, year, filing, text, question, answer

### SQL Database (SQLite)
- **Content:** Quarterly revenue data reconstructed from public financial reports
- **Companies:** Apple, Microsoft, Google, Amazon, Meta
- **Period:** Q1 and Q3 2022-2023
- **Segments:** iPhone, Mac, iPad, Wearables, Services, Productivity, Cloud, Personal, Search, YouTube, AWS, Advertising

*Note: SQL revenue figures are approximations based on publicly available SEC 10-K filings and earnings press releases.*
