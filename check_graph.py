from neo4j import GraphDatabase
from cognee.infrastructure.databases.graph.config import get_graph_config

c = get_graph_config()
print("Connected to:", c.graph_database_url)

with GraphDatabase.driver(
    c.graph_database_url,
    auth=(c.graph_database_username, c.graph_database_password),
) as d:
    with d.session() as s:
        print("Nodes:", s.run("MATCH (n) RETURN count(n) AS c").single()["c"])
        print("Rels: ", s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"])
        for r in s.run("MATCH (a)-[r]->(b) RETURN a.name AS a, type(r) AS rel, b.name AS b LIMIT 15"):
            print(r["a"], "-", r["rel"], "->", r["b"])