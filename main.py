"""
main.py — Company Brain FastAPI backend (Cognee V2 memory API).

Endpoints:
    GET  /                     → serves frontend/index.html
    GET  /health               → health check
    POST /ask                  → graph-grounded Q&A using cognee.recall()
    GET  /graph-path           → direct Neo4j Cypher path traversal between two entities

Start:
    uvicorn main:app --reload --port 8000
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Apply config BEFORE importing cognee ─────────────────────────────────────
# pyrefly: ignore [missing-import]
from config import configure_cognee
configure_cognee()

import cognee  # noqa: E402
# pyrefly: ignore [missing-import]
from grounding import find_graph_path  # noqa: E402

DATASET = "nexora_company_brain"

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Company Brain — Nexora Technologies",
    description="Knowledge-graph Q&A powered by Cognee V2 + Neo4j + Groq",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ───────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class GroundingInfo(BaseModel):
    entities: list[str] = []
    relationships: list[dict] = []
    search_type: str = "GRAPH_COMPLETION"
    raw_snippets: list[str] = []


class AskResponse(BaseModel):
    question: str
    answer: str
    dataset: str
    search_type: str
    grounding: Optional[GroundingInfo] = None


# ── Helpers matching official demo pattern ───────────────────────────────────

def extract_answer_text(entries: list[Any]) -> str:
    """Read .text from each recall entry, matching the demo's print_answers pattern."""
    texts: list[str] = []
    for entry in entries:
        val = getattr(entry, "text", None)
        if val and isinstance(val, str) and val.strip():
            texts.append(val.strip())
        elif isinstance(entry, dict) and "text" in entry:
            texts.append(str(entry["text"]).strip())
        elif isinstance(entry, str) and entry.strip():
            texts.append(entry.strip())

    if texts:
        seen = set()
        unique = []
        for t in texts:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return "\n\n".join(unique)

    return (
        "I could not find an answer in the knowledge graph. "
        "Please ensure data ingestion completed successfully via `python ingest.py`."
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({
        "message": "Company Brain API is running.",
        "endpoints": {
            "health": "GET /health",
            "ask": "POST /ask (body: {'question': '...'})",
            "graph_path": "GET /graph-path?start=X&end=Y"
        }
    })



@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api": "Cognee V2 memory API",
        "dataset": DATASET,
        "graph_db": os.getenv("GRAPH_DATABASE_PROVIDER", "neo4j"),
        "llm": os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile"),
        "embeddings": os.getenv("EMBEDDING_PROVIDER", "fastembed"),
    }


@app.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    try:
        # Official Cognee V2 recall pattern
        entries = await cognee.recall(
            question,
            query_type=cognee.SearchType.GRAPH_COMPLETION,
            datasets=[DATASET],
        )
        answer = extract_answer_text(entries)
    except Exception as exc:
        print(f"[ask] cognee.recall() error: {exc}")
        # Graceful fallback attempt with SearchType.SUMMARIES or general search
        try:
            entries = await cognee.recall(
                question,
                query_type=cognee.SearchType.SUMMARIES,
                datasets=[DATASET],
            )
            answer = extract_answer_text(entries)
        except Exception as inner_exc:
            raise HTTPException(
                status_code=500,
                detail=f"Cognee recall error: {inner_exc}"
            )

    return AskResponse(
        question=question,
        answer=answer,
        dataset=DATASET,
        search_type="GRAPH_COMPLETION",
    )


@app.get("/graph-path")
async def get_graph_path(
    start: str = Query(..., description="Starting entity name, e.g. Ananya Reddy"),
    end: str = Query(..., description="Target entity name, e.g. Ritu Chawla")
):
    """
    Direct Neo4j Cypher query to retrieve the explicit graph path
    between two entities, visually proving multi-hop reasoning.
    """
    start_clean = start.strip()
    end_clean = end.strip()
    if not start_clean or not end_clean:
        raise HTTPException(status_code=422, detail="Both 'start' and 'end' entity names are required.")

    return find_graph_path(start=start_clean, end=end_clean)
