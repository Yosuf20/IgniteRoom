"""
ingest.py — Nexora Technologies "Company Brain" data ingestion.

Parses all source files in ./Data/, adds them to Cognee 1.6, and runs
cognify() to build the knowledge graph in Neo4j AuraDB.

Usage:
    python ingest.py           # incremental (safe to re-run)
    python ingest.py --fresh   # prune everything first, then re-ingest
"""

import asyncio
import sys
from pathlib import Path

# ── Apply config BEFORE importing cognee ─────────────────────────────────────
# pyrefly: ignore [missing-import]
from config import configure_cognee
configure_cognee()

import cognee  # noqa: E402

DATA_DIR = Path(__file__).parent / "Data"
DATASET_NAME = "nexora"


# ── File parsers ─────────────────────────────────────────────────────────────

def parse_xlsx(path: Path) -> list[dict]:
    """Parse all sheets from an Excel file into labelled text chunks."""
    import pandas as pd

    chunks = []
    xl = pd.ExcelFile(path)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        rows_text = []
        for _, row in df.iterrows():
            row_str = " | ".join(
                f"{col}: {val}"
                for col, val in row.items()
                if str(val) not in ("nan", "NaT", "")
            )
            if row_str.strip():
                rows_text.append(row_str)

        sheet_text = (
            f"=== {path.stem} — Sheet: {sheet} ===\n"
            + "\n".join(rows_text)
        )
        chunks.append({"label": f"{path.stem}__{sheet}", "text": sheet_text})
    return chunks


def parse_docx(path: Path) -> str:
    """Extract full text from a .docx file."""
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_pdf(path: Path) -> str:
    """Extract text from a PDF, page by page."""
    import pdfplumber

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages)


def parse_txt(path: Path) -> str:
    """Read a plain-text file."""
    return path.read_text(encoding="utf-8", errors="replace")


# ── Source manifest ──────────────────────────────────────────────────────────

def collect_documents() -> list[dict]:
    """
    Returns a list of dicts: {"label": str, "text": str}.
    One entry per logical document/sheet.
    """
    docs: list[dict] = []
    skipped: list[str] = []

    files = {
        "Nexora_Company_Data.xlsx": "xlsx",
        "Nexora_Meeting_Notes.docx": "docx",
        "Nexora_Employee_Handbook.docx": "docx",
        "Nexora_Atlas_Architecture.pdf": "pdf",
        "WhatsApp_Chat_Export.txt": "txt",
        "Slack_Messages_Export.txt": "txt",
    }

    for filename, ftype in files.items():
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  ⚠  SKIP  {filename} — not found in {DATA_DIR}")
            skipped.append(filename)
            continue

        print(f"  📄 Parsing {filename} …")
        try:
            if ftype == "xlsx":
                chunks = parse_xlsx(path)
                docs.extend(chunks)
                print(f"       → {len(chunks)} sheet(s)")
            elif ftype == "docx":
                text = parse_docx(path)
                docs.append({"label": path.stem, "text": text})
                print(f"       → {len(text):,} chars")
            elif ftype == "pdf":
                text = parse_pdf(path)
                docs.append({"label": path.stem, "text": text})
                print(f"       → {len(text):,} chars")
            elif ftype == "txt":
                text = parse_txt(path)
                docs.append({"label": path.stem, "text": text})
                print(f"       → {len(text):,} chars")
        except Exception as exc:
            print(f"  ✗ ERROR parsing {filename}: {exc}")
            skipped.append(filename)

    print(f"\n  Parsed {len(docs)} document chunk(s), skipped {len(skipped)} file(s).")
    return docs


# ── Neo4j summary query ───────────────────────────────────────────────────────

def print_graph_summary() -> None:
    """Query Neo4j directly to print node/relationship counts."""
    import os
    from neo4j import GraphDatabase

    uri = os.environ["GRAPH_DATABASE_URL"]
    user = os.environ["GRAPH_DATABASE_USERNAME"]
    password = os.environ["GRAPH_DATABASE_PASSWORD"]

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            result = session.run(
                "CALL db.labels() YIELD label RETURN collect(label) AS labels"
            ).single()
            labels = result["labels"] if result else []
        driver.close()

        print(f"\n  ✅ Neo4j Graph Summary:")
        print(f"     Nodes        : {node_count:,}")
        print(f"     Relationships: {rel_count:,}")
        print(f"     Node Labels  : {', '.join(labels) or '(none yet)'}")

        if node_count == 0:
            print(
                "\n  ⚠  Graph appears empty — cognify() may not have finished yet.\n"
                "     Wait a minute and run `python verify.py` to re-check."
            )
    except Exception as exc:
        print(f"  ⚠  Could not fetch graph summary: {exc}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def main(fresh: bool = False) -> None:
    print("=" * 60)
    print("  Company Brain — Nexora Data Ingestion (cognee 1.6)")
    print("=" * 60)

    if fresh:
        print("\n[1/4] 🗑  Pruning existing data (--fresh mode) …")
        try:
            # cognee 1.6 prune API
            await cognee.prune.prune_data()
            await cognee.prune.prune_system(metadata=True)
            print("      Done.")
        except AttributeError:
            # Fallback for different cognee versions
            try:
                import cognee.api.v1.prune as prune_module
                await prune_module.prune_data()
                await prune_module.prune_system(metadata=True)
                print("      Done (via prune module).")
            except Exception as exc2:
                print(f"      Warning: prune failed ({exc2}) — continuing anyway.")
        except Exception as exc:
            print(f"      Warning: prune failed ({exc}) — continuing anyway.")

    print("\n[2/4] 📚 Collecting documents from ./Data/ …")
    docs = collect_documents()
    if not docs:
        print("  ✗ No documents found. Aborting.")
        sys.exit(1)

    print("\n[3/4] ⬆  Adding documents to Cognee …")
    added = 0
    for doc in docs:
        label = doc["label"]
        text = doc["text"]
        if not text.strip():
            print(f"  ⚠  Skipping empty doc: {label}")
            continue
        try:
            # cognee 1.6: remember() combines add + cognify in one call,
            # but we use add() + cognify() for explicit control and a single
            # cognify() pass over all documents (more efficient).
            await cognee.add(text, dataset_name=DATASET_NAME)
            print(f"  ✓  {label}")
            added += 1
        except Exception as exc:
            print(f"  ✗  {label} — {exc}")

    print(f"\n  Added {added}/{len(docs)} documents to Cognee dataset '{DATASET_NAME}'.")

    print(f"\n[4/4] 🧠 Running cognify() — building knowledge graph …")
    print("      (Extracts entities/relationships via Groq → writes to Neo4j.)")
    print("      This may take several minutes. Do not interrupt.\n")
    try:
        await cognee.cognify()
        print("\n  ✅ cognify() complete!")
    except Exception as exc:
        print(f"\n  ✗ cognify() failed: {exc}")
        print("  Tip: Check your GROQ_API_KEY and Neo4j credentials in .env")
        raise

    print_graph_summary()
    print("\n" + "=" * 60)
    print("  Ingestion finished!")
    print("  Next steps:")
    print("    1. python verify.py")
    print("    2. uvicorn main:app --reload --port 8000")
    print("    3. Open http://localhost:8000")
    print("=" * 60)


if __name__ == "__main__":
    fresh = "--fresh" in sys.argv
    asyncio.run(main(fresh=fresh))
