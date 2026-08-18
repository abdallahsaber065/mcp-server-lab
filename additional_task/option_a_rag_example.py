"""
OPTION A EXAMPLE: search_knowledge_base tool (keyword search, no embeddings)

Same shape as a RAG tool, but retrieval is done with BM25 keyword search
instead of a vector database. No embedding model, no API key, nothing
external to configure — just `pip install rank_bm25`.
"""

from typing import Optional

from keyword_search import KeywordStore
from pydantic import BaseModel, ConfigDict, Field

# Store: same upsert()/query() shape you'd use with a vector DB,

knowledge_store = KeywordStore()


#  Indexing step (run once, or whenever the source docs change)

def index_documents(docs: list[dict]):
    """
    docs: [{"text": "...", "entity_id": "pet_42", "role_required": "vet"}, ...]
    """
    for doc in docs:
        knowledge_store.upsert(
            payload=doc["text"],
            metadata={
                "entity_id": doc["entity_id"],
                "role_required": doc["role_required"],
            },
        )


# 3The MCP tool itself: typed schema + handler

class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(..., description="Keywords to search for")
    entity_id: str = Field(..., description="Scope search to this entity only")
    top_k: int = Field(default=3, ge=1, le=10)

    model_config = ConfigDict(extra="forbid")  # additionalProperties: false


def search_knowledge_base_handler(args: dict, session_role: str) -> str:
    """
    This is the function your MCP server registers as a tool.
    `session_role` comes from the authenticated session, same as your
    existing role checks — never trust a role field inside `args`.
    """
    parsed = SearchKnowledgeBaseInput.model_validate(args)

    matches = knowledge_store.query(
        query_text=parsed.query,
        top_k=parsed.top_k,
        filter={"entity_id": parsed.entity_id},
    )

    # authorization check happens in the handler, not just the schema
    visible = [
        m for m in matches
        if m["metadata"]["role_required"] in ("any", session_role)
    ]

    if not visible:
        return "No relevant records found for this query."

    return "\n\n".join(m["payload"] for m in visible)


# Demo

if __name__ == "__main__":
    index_documents([
        {
            "text": "Visit 2026-03-01: mild ear infection, prescribed drops.",
            "entity_id": "pet_42",
            "role_required": "any",
        },
        {
            "text": "Visit 2026-05-14: controlled substance administered, vet sign-off required.",
            "entity_id": "pet_42",
            "role_required": "vet",
        },
        {
            "text": "Visit 2026-01-10: routine checkup, no notes.",
            "entity_id": "pet_99",
            "role_required": "any",
        },
    ])

    front_desk_result = search_knowledge_base_handler(
        {"query": "recent visits ear infection", "entity_id": "pet_42", "top_k": 5},
        session_role="front_desk",
    )
    print("--- front_desk sees ---")
    print(front_desk_result)

    vet_result = search_knowledge_base_handler(
        {"query": "controlled substance", "entity_id": "pet_42", "top_k": 5},
        session_role="vet",
    )
    print("\n--- vet sees ---")
    print(vet_result)

    empty_result = search_knowledge_base_handler(
        {"query": "anything", "entity_id": "pet_does_not_exist", "top_k": 5},
        session_role="vet",
    )
    print("\n--- unknown entity ---")
    print(empty_result)

    no_match_result = search_knowledge_base_handler(
        {"query": "broken leg surgery", "entity_id": "pet_42", "top_k": 5},
        session_role="vet",
    )
    print("\n--- no keyword overlap ---")
    print(no_match_result)
