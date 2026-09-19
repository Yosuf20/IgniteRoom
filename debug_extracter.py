import asyncio, sys
sys.stdout.reconfigure(encoding="utf-8")
# pyrefly: ignore [missing-import]
from ingest import CUSTOM_PROMPT   # this also applies your Cognee config

from cognee.infrastructure.llm.LLMGateway import LLMGateway
from cognee.shared.data_models import KnowledgeGraph

TEXT = open("Data/Slack_Messages_Export.txt", encoding="utf-8").read()[:1500]

import asyncio, sys
sys.stdout.reconfigure(encoding="utf-8")
CUSTOM_PROMPT
from cognee.infrastructure.llm.LLMGateway import LLMGateway
from cognee.shared.data_models import KnowledgeGraph

TEXT = open("Data/Slack_Messages_Export.txt", encoding="utf-8").read()[:1500]

EDGE_RULES = """

OUTPUT FORMAT (critical):
Return two lists: "nodes" and "edges". The "edges" list MUST NOT be empty.
Each edge has source_node_id, target_node_id and relationship_name. Both ids must
exactly equal the id of a node in your nodes list.

Example. Text: "Aisha raised JIRA-104 about login latency; Raj is fixing it."
nodes: aisha (Person), raj (Person), jira-104 (Ticket)
edges: aisha -[reported]-> jira-104 ; jira-104 -[assigned_to]-> raj
"""



from pydantic import Field
from cognee.shared.data_models import KnowledgeGraph

EdgesType = KnowledgeGraph.model_fields["edges"].annotation

class StrictKG(KnowledgeGraph):
    edges: EdgesType = Field(
        ...,
        description=(
            "REQUIRED, never empty. Directed relationships between nodes, e.g. reported, "
            "assigned_to, works_on, member_of, authored, mentions, uses. "
            "source_node_id and target_node_id must exactly match a node id."
        ),
    )

async def try_model(name, model, prompt):
    kg = await asyncio.wait_for(
        LLMGateway.acreate_structured_output(
            text_input=TEXT, system_prompt=prompt, response_model=model
        ),
        120,
    )
    ids = {n.id for n in kg.nodes}
    good = sum(e.source_node_id in ids and e.target_node_id in ids for e in kg.edges)
    print(f"[{name}] nodes={len(kg.nodes)} edges={len(kg.edges)} valid={good}", flush=True)
    for e in kg.edges[:10]:
        print("    ", e.source_node_id, "-[", e.relationship_name, "]->", e.target_node_id)

async def main():
    await try_model("StrictKG + prompt", StrictKG, CUSTOM_PROMPT)
    await try_model("StrictKG + edge rules", StrictKG, CUSTOM_PROMPT + EDGE_RULES)

asyncio.run(main())