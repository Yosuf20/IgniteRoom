from pydantic import Field
from cognee.shared.data_models import KnowledgeGraph

EdgesType = KnowledgeGraph.model_fields["edges"].annotation


class StrictKG(KnowledgeGraph):
    """Same shape as KnowledgeGraph, but edges are mandatory."""
    edges: EdgesType = Field(
        ...,
        description=(
            "REQUIRED, never empty. Directed relationships between nodes, e.g. reported, "
            "assigned_to, works_on, member_of, authored, mentions, uses. "
            "source_node_id and target_node_id must exactly match a node id."
        ),
    )