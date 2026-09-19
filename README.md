# Company Brain — Nexora Technologies Knowledge Graph

> **Hackathon PS-2**: A "Company Brain" that ingests a small company's data, builds a Cognee-powered knowledge graph on Neo4j AuraDB, and answers natural-language questions grounded in that graph — including multi-hop reasoning across data sources.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Knowledge Graph | [Cognee](https://cognee.ai) + Neo4j AuraDB |
| LLM | Groq (llama-3.3-70b-versatile) via LiteLLM |
| Embeddings | FastEmbed (local, sentence-transformers/all-MiniLM-L6-v2) |
| Backend API | FastAPI + Uvicorn |
| Frontend | Single HTML page (served by FastAPI) |
| Config | python-dotenv |

---

## Project Structure

```
IgniteRoom/
├── .env                    # Your secrets (never commit)
├── .env.example            # Template — copy and fill in
├── requirements.txt        # pip dependencies
├── config.py               # Centralised env + Cognee config
├── ingest.py               # Data ingestion + cognify()
├── main.py                 # FastAPI backend
├── verify.py               # Neo4j graph sanity checks
├── frontend/
│   └── index.html          # Q&A UI (served at /)
└── Data/
    ├── Nexora_Company_Data.xlsx
    ├── Nexora_Meeting_Notes.docx
    ├── Nexora_Employee_Handbook.docx
    ├── Nexora_Atlas_Architecture.pdf
    ├── WhatsApp_Chat_Export.txt
    └── Slack_Messages_Export.txt
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- A Neo4j AuraDB Free Tier instance ([console.neo4j.io](https://console.neo4j.io))
- A Groq API key ([console.groq.com](https://console.groq.com))

### 2. Clone and create environment

```bash
cd IgniteRoom
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** On first run, FastEmbed will download the embedding model (~90MB). This requires an internet connection.

### 4. Configure credentials

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=custom
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_API_KEY=gsk_...          # same as GROQ_API_KEY

EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384

GRAPH_DATABASE_URL=neo4j+s://<instance-id>.databases.neo4j.io
GRAPH_DATABASE_USERNAME=<your-aura-username>
GRAPH_DATABASE_PASSWORD=<your-aura-password>
GRAPH_DATABASE_PROVIDER=neo4j
```

### 5. Ingest data and build the graph

```bash
python ingest.py
```

This will:
1. Parse all files in `./Data/`
2. Add them to Cognee (`cognee.add()`)
3. Run `cognee.cognify()` — extracts entities/relationships via Groq, writes to Neo4j
4. Print a summary of nodes and relationships created

To start fresh (wipe and re-ingest):

```bash
python ingest.py --fresh
```

### 6. Verify the graph

```bash
python verify.py
```

Should show: ✅ nodes > 0, relationships > 0, ≥2 label types, sample multi-hop path.

### 7. Start the API

```bash
uvicorn main:app --reload --port 8000
```

### 8. Open the frontend

Navigate to: **[http://localhost:8000](http://localhost:8000)**

---

## API Reference

### `GET /health`

```json
{
  "status": "ok",
  "graph_db": "neo4j",
  "llm": "groq/llama-3.3-70b-versatile",
  "embeddings": "fastembed/all-MiniLM-L6-v2"
}
```

### `POST /ask`

**Request:**
```json
{ "question": "Who approved the budget for the project Ananya Reddy is working on?" }
```

**Response:**
```json
{
  "question": "...",
  "answer": "Ritu Chawla (CEO) approved the budget for Project Comet. Ananya Reddy reports to Vikram Choudhary.",
  "grounding": {
    "entities": ["Ananya Reddy", "Project Comet", "Ritu Chawla", "Vikram Choudhary"],
    "relationships": [
      { "from": "Ananya Reddy", "relation": "WORKS_ON", "to": "Project Comet" },
      { "from": "Ritu Chawla", "relation": "APPROVED_BUDGET", "to": "Project Comet" },
      { "from": "Ananya Reddy", "relation": "REPORTS_TO", "to": "Vikram Choudhary" }
    ],
    "search_type": "GRAPH_COMPLETION",
    "raw_snippets": ["..."]
  }
}
```

Interactive API docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Acceptance Criteria Questions

| # | Question | Expected Answer |
|---|----------|----------------|
| 1 | What caused the login latency issue Aisha raised in WhatsApp, and what fix was decided? | DB session check on every request → Redis-backed session cache; decided in Atlas Weekly Sync |
| 2 | Who was assigned to fix the dashboard performance issue raised in Slack, and what's their relevant skill? | Meera Iyer; React performance / virtualised rendering |
| 3 | Who approved the budget for the project Ananya Reddy is working on, and who manages her? | Ritu Chawla (CEO) approved Comet; Ananya reports to Vikram Choudhary |

---

## Troubleshooting

**`cognify()` fails with auth error**: Check `GROQ_API_KEY` is correct in `.env`.

**Neo4j connection refused**: Verify `GRAPH_DATABASE_URL` starts with `neo4j+s://` (not `bolt://`).

**Empty graph after ingestion**: Run `python ingest.py --fresh` to prune and re-ingest.

**Embedding dimension mismatch**: If switching providers, always run `--fresh` to clear stale vector collections.
