"""
config.py — Central configuration for Company Brain.

Loads .env, injects LLM + fastembed embeddings + Neo4j AuraDB graph config
into Cognee before any cognee operations.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env first, before cognee is imported ───────────────────────────────
_ROOT = Path(__file__).parent
load_dotenv(_ROOT / ".env", override=True)

# ── Cognee settings: disable access control / auth for local hackathon use ───
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "false")


def configure_cognee() -> None:
    """Apply all Cognee config. Must be called before any cognee operation."""
    llm_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_key:
        raise EnvironmentError(
            "Missing required LLM API key: LLM_API_KEY (or GROQ_API_KEY / OPENAI_API_KEY).\n"
            "Please set your LLM API key in .env."
        )

    # Ensure key is available in os.environ under both names
    os.environ["LLM_API_KEY"] = llm_key
    os.environ["GROQ_API_KEY"] = llm_key

    import cognee

    # ── LLM Configuration ───────────────────────────────────────────────────
    llm_provider = os.getenv("LLM_PROVIDER", "custom")
    llm_model = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")

    cognee.config.set("llm_provider", llm_provider)
    cognee.config.set("llm_model", llm_model)
    cognee.config.set("llm_api_key", llm_key)

    # ── Embeddings (fastembed - local, no key needed) ────────────────────────
    cognee.config.set("embedding_provider", os.getenv("EMBEDDING_PROVIDER", "fastembed"))
    cognee.config.set("embedding_model", os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    cognee.config.set("embedding_dimensions", int(os.getenv("EMBEDDING_DIMENSIONS", "384")))

    # ── Graph DB: Neo4j AuraDB ──────────────────────────────────────────────
    graph_url = os.getenv("GRAPH_DATABASE_URL") or os.getenv("NEO4J_URI")
    graph_user = os.getenv("GRAPH_DATABASE_USERNAME") or os.getenv("NEO4J_USERNAME")
    graph_pass = os.getenv("GRAPH_DATABASE_PASSWORD") or os.getenv("NEO4J_PASSWORD")
    graph_name = os.getenv("GRAPH_DATABASE_NAME", "neo4j")

    if graph_url and graph_user and graph_pass:
        os.environ["GRAPH_DATABASE_URL"] = graph_url
        os.environ["GRAPH_DATABASE_USERNAME"] = graph_user
        os.environ["GRAPH_DATABASE_PASSWORD"] = graph_pass
        os.environ["GRAPH_DATABASE_NAME"] = graph_name
        os.environ["GRAPH_DATABASE_PROVIDER"] = "neo4j"

        cognee.config.set("graph_database_provider", "neo4j")
        cognee.config.set("graph_database_url", graph_url)
        # cognee.config.set("graph_database_name", graph_name)
        cognee.config.set("graph_database_username", graph_user)
        cognee.config.set("graph_database_password", graph_pass)
        graph_status = f"Neo4j ({graph_url})"
    else:
        # If Neo4j credentials are not provided, unset neo4j provider so Cognee uses local graph
        if os.environ.get("GRAPH_DATABASE_PROVIDER") == "neo4j":
            del os.environ["GRAPH_DATABASE_PROVIDER"]
        cognee.config.set("graph_database_provider", "networkx")
        graph_status = "Local fallback (Add GRAPH_DATABASE_URL/USERNAME/PASSWORD in .env for Neo4j)"


    print(
        f"[config] Cognee configured\n"
        f"         LLM       : {llm_model} ({llm_provider})\n"
        f"         Embeddings: {os.getenv('EMBEDDING_PROVIDER', 'fastembed')}\n"
        f"         Graph DB  : {graph_status}\n"
        f"         Auth      : disabled"
    )
