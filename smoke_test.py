"""
smoke_test.py — Minimal standalone test matching Cognee reference demo.

Remembers one sentence, recalls an answer about it via GRAPH_COMPLETION,
and prints the result to verify the environment, LLM, and graph backend
connection before touching the real dataset.

Usage:
    python smoke_test.py
"""

import asyncio
# pyrefly: ignore [missing-import]
from config import configure_cognee
configure_cognee()

import cognee  # noqa: E402

DATASET = "company_brain_smoke_test"
DOCUMENT = "Alice maintains the payments API. The payments API uses PostgreSQL."
QUESTION = "Who maintains the payments API and which database does it use?"


def print_answers(entries):
    """Print answer text from each entry matching the official Cognee demo."""
    for entry in entries:
        text = getattr(entry, "text", str(entry))
        print(text)


async def main():
    print("=" * 60, flush=True)
    print("  Cognee V2 Memory API — Standalone Smoke Test", flush=True)
    print("=" * 60, flush=True)

    print("\n1. Remember test document:", flush=True)
    print(f"   \"{DOCUMENT}\"", flush=True)
    res = await cognee.remember(DOCUMENT, dataset_name=DATASET, self_improvement=False)
    print(f"   ✓ Result: {res}", flush=True)

    print("\n2. Recall question from graph memory:", flush=True)
    print(f"   \"{QUESTION}\"", flush=True)
    entries = await cognee.recall(
        QUESTION,
        query_type=cognee.SearchType.GRAPH_COMPLETION,
        datasets=[DATASET],
    )

    print("\n3. Answer:", flush=True)
    print("-" * 50, flush=True)
    print_answers(entries)
    print("-" * 50, flush=True)
    print("\n✅ Smoke test completed successfully!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
