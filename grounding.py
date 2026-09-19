"""
grounding.py — Neo4j direct graph traversal for Company Brain demo.

Connects to Neo4j AuraDB using GRAPH_DATABASE_* env vars and retrieves the
actual graph paths between entities to visually prove multi-hop reasoning.
"""

import os
from typing import Any
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env", override=True)


def get_neo4j_driver():
    """Create and return a Neo4j driver using configured env variables."""
    from neo4j import GraphDatabase

    url = os.getenv("GRAPH_DATABASE_URL") or os.getenv("NEO4J_URI")
    user = os.getenv("GRAPH_DATABASE_USERNAME") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("GRAPH_DATABASE_PASSWORD") or os.getenv("NEO4J_PASSWORD")

    if not (url and user and password):
        return None

    return GraphDatabase.driver(url, auth=(user, password))


def _extract_node_info(node: Any) -> dict:
    props = dict(node.items())
    name = props.get("name") or props.get("id") or props.get("title") or str(node.id)
    return {
        "id": str(node.element_id if hasattr(node, "element_id") else node.id),
        "labels": list(node.labels) if hasattr(node, "labels") else [],
        "name": str(name),
        "properties": {k: str(v) for k, v in props.items()},
    }


def find_graph_path(start: str, end: str) -> dict:
    """
    Find paths between entity `start` and entity `end` in Neo4j AuraDB.
    Returns nodes, relationships, and human-readable reasoning hops.
    """
    driver = get_neo4j_driver()
    if driver is None:
        return {
            "status": "not_configured",
            "message": "Neo4j credentials (GRAPH_DATABASE_URL/USERNAME/PASSWORD) not set in .env.",
            "start": start,
            "end": end,
            "paths": [],
        }

    paths_data = []

    try:
        with driver.session() as session:
            # 1. Try exact match first
            cypher_exact = """
            MATCH p = (a {name: $start})-[*1..4]-(b {name: $end})
            RETURN p LIMIT 5
            """
            records = list(session.run(cypher_exact, start=start, end=end))

            # 2. If no exact match, try case-insensitive contains match
            if not records:
                cypher_fuzzy = """
                MATCH p = (a)-[*1..4]-(b)
                WHERE (toLower(coalesce(a.name, a.id, '')) CONTAINS toLower($start))
                  AND (toLower(coalesce(b.name, b.id, '')) CONTAINS toLower($end))
                RETURN p LIMIT 5
                """
                records = list(session.run(cypher_fuzzy, start=start, end=end))

            for record in records:
                path = record["p"]
                nodes_list = [_extract_node_info(n) for n in path.nodes]
                rels_list = []
                for rel in path.relationships:
                    start_node = _extract_node_info(rel.start_node)
                    end_node = _extract_node_info(rel.end_node)
                    rels_list.append({
                        "type": rel.type,
                        "from": start_node["name"],
                        "to": end_node["name"],
                        "properties": dict(rel.items()),
                    })

                chain_str = " → ".join(
                    f"({nodes_list[i]['name']}) -[{rels_list[i]['type']}]-> ({nodes_list[i+1]['name']})"
                    for i in range(len(rels_list))
                )

                paths_data.append({
                    "length": len(path.relationships),
                    "nodes": nodes_list,
                    "relationships": rels_list,
                    "chain": chain_str or " → ".join(n["name"] for n in nodes_list),
                })

        driver.close()
        return {
            "status": "ok",
            "start": start,
            "end": end,
            "paths_found": len(paths_data),
            "paths": paths_data,
        }
    except Exception as exc:
        if driver:
            driver.close()
        return {
            "status": "error",
            "message": str(exc),
            "start": start,
            "end": end,
            "paths": [],
        }
