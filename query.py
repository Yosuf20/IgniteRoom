"""
query.py — Company Brain query module using Cognee V2 recall().

Usage:
    python query.py "Who approved the budget for the project Ananya Reddy is working on?"
"""

import sys
import asyncio
# pyrefly: ignore [missing-import]
from config import configure_cognee
configure_cognee()

import cognee  # noqa: E402

DATASET = "nexora_company_brain"


def print_answers(entries):
    """Print answer text from each entry matching Cognee demo pattern."""
    for entry in entries:
        print(getattr(entry, "text", str(entry)))


def extract_answers(entries) -> list[str]:
    """Extract list of text strings from recall entries."""
    answers = []
    for entry in entries:
        text = getattr(entry, "text", None)
        if text:
            answers.append(str(text))
        elif isinstance(entry, dict) and "text" in entry:
            answers.append(str(entry["text"]))
        elif isinstance(entry, str):
            answers.append(entry)
        else:
            answers.append(str(entry))
    return answers


async def ask_question(question: str) -> list[str]:
    """Query the knowledge graph using Cognee V2 recall()."""
    entries = await cognee.recall(
        question,
        query_type=cognee.SearchType.GRAPH_COMPLETION,
        datasets=[DATASET],
    )
    return extract_answers(entries)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    else:
        q = "Who approved the budget for the project Ananya Reddy is working on, and who manages her?"

    print(f"\nQuestion: {q}\n" + "-" * 50)
    results = asyncio.run(ask_question(q))
    if results:
        print("\nAnswer:\n" + "\n\n".join(results))
    else:
        print("No answer returned.")
