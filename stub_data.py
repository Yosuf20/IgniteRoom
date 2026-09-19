"""Fake company knowledge data and a deterministic search implementation."""

DOCUMENTS = [
    {
        "type": "document",
        "id": "DOC-001",
        "title": "Q3 Customer Export Specification",
        "content": (
            "The customer export feature must support CSV and JSON formats. "
            "The delivery deadline is 2026-10-15, and the export API must include "
            "an account_id field."
        ),
    }
]

TICKETS = [
    {
        "type": "ticket",
        "id": "TKT-001",
        "title": "Add JSON export to customer downloads",
        "content": (
            "Implement the customer export feature with JSON output and account_id. "
            "This ticket references DOC-001 and is targeted for the 2026-10-15 deadline."
        ),
    }
]

MEETING_NOTES = [
    {
        "type": "meeting",
        "id": "MTG-001",
        "title": "Product sync — customer export",
        "content": (
            "The product sync reviewed TKT-001. Priya confirmed that the team will "
            "finish the JSON export before the DOC-001 deadline of 2026-10-15."
        ),
    }
]

ENTITIES = [
    {"id": "DOC-001", "name": "Q3 Customer Export Specification", "type": "document"},
    {"id": "TKT-001", "name": "Add JSON export to customer downloads", "type": "ticket"},
    {"id": "MTG-001", "name": "Product sync — customer export", "type": "meeting"},
    {"id": "FEAT-EXPORT", "name": "Customer export feature", "type": "feature"},
    {"id": "DATE-2026-10-15", "name": "2026-10-15 delivery deadline", "type": "deadline"},
]

RELATIONSHIPS = [
    {"source": "TKT-001", "relation": "implements", "target": "FEAT-EXPORT"},
    {"source": "FEAT-EXPORT", "relation": "specified_by", "target": "DOC-001"},
    {"source": "DOC-001", "relation": "has_deadline", "target": "DATE-2026-10-15"},
    {"source": "MTG-001", "relation": "discusses", "target": "TKT-001"},
]


def _result(answer, source_ids, chain):
    source_lookup = {item["id"]: item for item in DOCUMENTS + TICKETS + MEETING_NOTES}
    sources = [
        {"type": source_lookup[item_id]["type"], "id": item_id, "title": source_lookup[item_id]["title"]}
        for item_id in source_ids
    ]
    entity_ids = set(chain)
    for relationship in RELATIONSHIPS:
        if relationship["source"] in chain or relationship["target"] in chain:
            entity_ids.add(relationship["source"])
            entity_ids.add(relationship["target"])
    entities = [entity for entity in ENTITIES if entity["id"] in entity_ids]
    relationships = [
        relationship
        for relationship in RELATIONSHIPS
        if relationship["source"] in entity_ids and relationship["target"] in entity_ids
    ]
    return {
        "answer": answer,
        "sources": sources,
        "entities": entities,
        "relationships": relationships,
        "multi_hop_chain": chain,
    }


def search(query):
    """Return the shared answer/source/graph shape for a natural-language query."""
    normalized = (query or "").lower()

    if any(term in normalized for term in ("meeting", "sync", "discuss", "who", "status")):
        answer = (
            "The product sync discussed TKT-001, which implements the customer export feature. "
            "The team confirmed it would finish the JSON export before 2026-10-15."
        )
        source_ids = ["MTG-001", "TKT-001", "DOC-001"]
        chain = ["MTG-001", "TKT-001", "FEAT-EXPORT", "DOC-001", "DATE-2026-10-15"]
    elif any(term in normalized for term in ("deadline", "when", "date", "due", "export", "json", "feature")):
        answer = (
            "The customer export feature is due on 2026-10-15. DOC-001 specifies CSV and JSON "
            "support plus an account_id field, and TKT-001 tracks the JSON implementation."
        )
        source_ids = ["DOC-001", "TKT-001", "MTG-001"]
        chain = ["TKT-001", "FEAT-EXPORT", "DOC-001", "DATE-2026-10-15"]
    else:
        answer = (
            "The company knowledge base centers on the customer export feature: TKT-001 implements "
            "it, DOC-001 defines CSV/JSON requirements and a 2026-10-15 deadline, and MTG-001 "
            "records the delivery discussion."
        )
        source_ids = ["DOC-001", "TKT-001", "MTG-001"]
        chain = ["TKT-001", "FEAT-EXPORT", "DOC-001", "DATE-2026-10-15"]

    return _result(answer, source_ids, chain)
