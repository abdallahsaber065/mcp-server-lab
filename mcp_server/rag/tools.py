from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from mcp_server.rag.store import knowledge_store

class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(..., description="Search keywords to query in domain knowledge base policies, rules, and procedures.")
    entity_id: Optional[str] = Field(default=None, description="Optional scope search to a specific document or policy ID.")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of relevant chunks to retrieve.")

    model_config = ConfigDict(extra="forbid")  # Strict MCP defensive Pydantic spec

def search_knowledge_base_handler(args: Dict[str, Any], session_role: str) -> Dict[str, Any]:
    """
    Search domain knowledge base with BM25 ranking and server-side role authorization filtering.
    `session_role` comes from the authenticated session context, not untrusted LLM args.
    """
    try:
        parsed = SearchKnowledgeBaseInput.model_validate(arguments if (arguments := args) else {})
    except Exception as err:
        return {
            "status": "validation_error",
            "message": f"Invalid arguments for search_knowledge_base: {str(err)}"
        }

    filter_dict = {}
    if parsed.entity_id:
        filter_dict["entity_id"] = parsed.entity_id

    raw_matches = knowledge_store.query(
        query_text=parsed.query,
        top_k=parsed.top_k,
        filter_metadata=filter_dict if filter_dict else None
    )

    # Server-side authorization check: filter out records restricted to higher privilege roles
    visible_matches = [
        m for m in raw_matches
        if m["metadata"].get("role_required") in ("any", session_role)
        or (session_role == "executive_admin")  # Executive admin sees all
    ]

    if not visible_matches:
        return {
            "status": "no_results",
            "message": "No relevant records found matching query and authorization context.",
            "query": parsed.query,
            "count": 0
        }

    return {
        "status": "success",
        "query": parsed.query,
        "count": len(visible_matches),
        "results": [
            {
                "id": m["id"],
                "content": m["payload"],
                "category": m["metadata"].get("category", "general"),
                "score": m["score"]
            }
            for m in visible_matches
        ]
    }
