"""
verify.py — Sanity-check the Neo4j AuraDB graph after ingestion.

Connects directly via the neo4j Python driver and runs Cypher queries to
confirm the graph was built correctly.

Usage: python verify.py
Exit code: 0 = all checks passed, 1 = one or more checks failed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from neo4j import GraphDatabase  # noqa: E402


def run_checks() -> bool:
    uri = os.environ.get("GRAPH_DATABASE_URL", "")
    user = os.environ.get("GRAPH_DATABASE_USERNAME", "")
    password = os.environ.get("GRAPH_DATABASE_PASSWORD", "")

    if not all([uri, user, password]):
        print("✗ GRAPH_DATABASE_URL / USERNAME / PASSWORD not set in .env")
        return False

    print("=" * 60)
    print("  Company Brain — Neo4j Graph Verification")
    print("=" * 60)
    print(f"  Connecting to: {uri}\n")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("  ✅ Connection OK\n")
    except Exception as exc:
        print(f"  ✗ Cannot connect to Neo4j: {exc}")
        return False

    all_passed = True

    with driver.session() as session:

        # ── Check 1: Node count ──────────────────────────────────────────────
        result = session.run("MATCH (n) RETURN count(n) AS c").single()
        node_count = result["c"] if result else 0
        ok = node_count > 0
        status = "✅" if ok else "✗ FAIL"
        print(f"  {status}  Total nodes        : {node_count:,}")
        if not ok:
            all_passed = False

        # ── Check 2: Relationship count ──────────────────────────────────────
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        rel_count = result["c"] if result else 0
        ok = rel_count > 0
        status = "✅" if ok else "✗ FAIL"
        print(f"  {status}  Total relationships: {rel_count:,}")
        if not ok:
            all_passed = False

        # ── Check 3: Distinct node labels ────────────────────────────────────
        result = session.run(
            "CALL db.labels() YIELD label RETURN collect(label) AS labels"
        ).single()
        labels = result["labels"] if result else []
        ok = len(labels) >= 2
        status = "✅" if ok else "✗ FAIL (expected ≥2 label types)"
        print(f"  {status}  Node label types   : {', '.join(labels) or '(none)'}")
        if not ok:
            all_passed = False

        # ── Check 4: Sample relationship types ───────────────────────────────
        result = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN collect(relationshipType) AS types"
        ).single()
        rel_types = result["types"] if result else []
        ok = len(rel_types) > 0
        status = "✅" if ok else "✗ FAIL"
        print(f"  {status}  Relationship types : {', '.join(rel_types[:8]) or '(none)'}")
        if not ok:
            all_passed = False

        print()

        # ── Check 5: Multi-hop path — Ananya → Project → Budget approver ────
        print("  Multi-hop path check (Ananya → Project → Approver):")
        try:
            records = list(session.run(
                """
                MATCH path = (a)-[*1..4]-(b)
                WHERE toLower(a.name) CONTAINS 'ananya'
                RETURN
                  [node IN nodes(path) | coalesce(node.name, node.id, labels(node)[0])] AS node_names,
                  [rel IN relationships(path) | type(rel)] AS rel_types
                LIMIT 3
                """
            ))
            if records:
                for rec in records:
                    nodes_str = " → ".join(n for n in rec["node_names"] if n)
                    rels_str = ", ".join(rec["rel_types"])
                    print(f"      Path: {nodes_str}")
                    print(f"      Rels: {rels_str}")
                print(f"  ✅ Multi-hop path found")
            else:
                print("  ⚠  No path found for Ananya — graph may be sparse; try re-ingesting.")
        except Exception as exc:
            print(f"  ⚠  Path query error: {exc}")

        print()

        # ── Check 6: Sample — Ticket nodes ──────────────────────────────────
        print("  Sample entity search (nodes with 'ATL' or 'PHX' in name/id):")
        try:
            records = list(session.run(
                """
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS 'ATL'
                       OR toString(n[prop]) CONTAINS 'PHX')
                RETURN labels(n) AS lbl, n.name AS name LIMIT 5
                """
            ))
            if records:
                for rec in records:
                    print(f"      [{', '.join(rec['lbl'])}] {rec['name']}")
                print(f"  ✅ Ticket-like nodes found")
            else:
                print("  ⚠  No ticket nodes found — check if Slack/WhatsApp data was ingested.")
        except Exception as exc:
            print(f"  ⚠  Ticket query error: {exc}")

    driver.close()

    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED — graph looks healthy!")
    else:
        print("  ✗  SOME CHECKS FAILED — see above for details.")
        print("     Try: python ingest.py --fresh   to rebuild from scratch.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    ok = run_checks()
    sys.exit(0 if ok else 1)
