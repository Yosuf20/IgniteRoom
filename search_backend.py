"""Search routing layer for the stub backend and Person A's HTTP API."""

from collections import defaultdict

import requests


USE_REAL_SEARCH = True
API_BASE_URL = "http://localhost:8000"
REAL_SEARCH_URL = f"{API_BASE_URL}/ask"
REQUEST_TIMEOUT_SECONDS = 20
_last_backend = "stub"
_last_error = None


def backend_status():
    """Return a UI-safe description of the backend used by the last search."""
    return {"mode": _last_backend, "error": _last_error}


def _longest_path(graph, nodes):
    """Find the longest simple path in a small undirected graph component."""
    best = []

    def visit(node, path, visited):
        nonlocal best
        if len(path) > len(best):
            best = path.copy()
        for neighbor in sorted(graph[node]):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                visit(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    for node in sorted(nodes):
        visit(node, [node], {node})
    return best


def _derive_multi_hop_chain(entity_names, relationships):
    """Derive the largest connected simple path from named graph relationships."""
    graph = defaultdict(set)
    for entity_name in entity_names:
        graph[entity_name]

    for relationship in relationships:
        source = relationship.get("source")
        target = relationship.get("target")
        if source and target:
            graph[source].add(target)
            graph[target].add(source)

    components = []
    unseen = set(graph)
    while unseen:
        start = min(unseen)
        component = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            stack.extend(graph[node] - component)
        components.append(component)

    if not components:
        return []
    largest_component = max(components, key=lambda component: (len(component), sorted(component)))
    return _longest_path(graph, largest_component)


def _map_real_response(payload):
    """Map Person A's /ask response into the app's existing result contract."""
    grounding = payload.get("grounding") or {}
    raw_entities = grounding.get("entities") or []
    entity_names = []
    entities = []
    for entity in raw_entities:
        name = entity if isinstance(entity, str) else entity.get("name") or entity.get("id")
        if not name:
            continue
        name = str(name)
        if name not in entity_names:
            entity_names.append(name)
            entities.append({"id": name, "name": name, "type": "entity"})

    relationships = []
    for relationship in grounding.get("relationships") or []:
        source = relationship.get("from") or relationship.get("source")
        target = relationship.get("to") or relationship.get("target")
        if source and target:
            relationships.append(
                {
                    "source": str(source),
                    "relation": str(relationship.get("relation", "related_to")),
                    "target": str(target),
                }
            )

    raw_snippets = [str(snippet) for snippet in grounding.get("raw_snippets") or [] if str(snippet).strip()]
    sources = []
    if raw_snippets:
        sources.append(
            {
                "type": "grounding",
                "id": "REAL-GROUNDING",
                "title": f"Cognee grounding snippets ({len(raw_snippets)})",
            }
        )

    return {
        "answer": str(payload.get("answer") or ""),
        "sources": sources,
        "entities": entities,
        "relationships": relationships,
        "multi_hop_chain": _derive_multi_hop_chain(entity_names, relationships),
    }


def _real_search(query):
    """Call Person A's FastAPI /ask endpoint and map its JSON response."""
    response = requests.post(
        REAL_SEARCH_URL,
        json={"question": query},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return _map_real_response(response.json())


def search(query):
    """Route to real search when enabled; fall back to stub on any real-search failure."""
    global _last_backend, _last_error

    if USE_REAL_SEARCH:
        try:
            result = _real_search(query)
            _last_backend = "real"
            _last_error = None
        except Exception as error:
            _last_backend = "stub fallback"
            _last_error = str(error)
            from stub_data import search as stub_search

            result = stub_search(query)
    else:
        from stub_data import search as stub_search

        result = stub_search(query)
        _last_backend = "stub"
        _last_error = None

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "entities": result["entities"],
        "relationships": result["relationships"],
        "multi_hop_chain": result["multi_hop_chain"],
    }
