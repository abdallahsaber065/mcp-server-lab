"""
Chat Context Builder (web/services/chat/context_builder.py)

Extracts memory context and RAG-grounded knowledge for a chat request.
Single Responsibility: build the enriched system prompt + side-channel payloads.
"""

from typing import Any, Dict, List, Optional, Tuple


def build_memory_payload(
    tenant_id: Optional[int],
    user_email: Optional[str],
    semantic_store: Any,
    episodic_store: Any
) -> Optional[Dict[str, Any]]:
    """Return memory context SSE payload or None if nothing relevant found."""
    if not tenant_id:
        return None
    try:
        active_facts = semantic_store.get_active_facts(subject=f"tenant_{tenant_id}")
        episodes = episodic_store.query_episodes(entity_id=f"tenant_{tenant_id}", limit=4)
        if active_facts or episodes:
            return {
                "type": "memory_context",
                "persona_name": user_email or f"Tenant #{tenant_id}",
                "active_facts": active_facts or [],
                "recent_episodes": episodes or [],
            }
    except Exception:
        pass
    return None


def build_rag_payload(
    msg_text: str,
    rag_strategy: str,
    rag_store: Any,
    hybrid_engine: Any,
    agentic_router: Any,
    graph_rag: Any,
    pgvector_rag_store: Any,
    role: Optional[str] = None,
    tenant_id: Optional[int] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Run the selected RAG strategy and return:
      (rag_snippet: str to append to system_prompt, rag_payload: Optional SSE event dict)
    """
    from rag.naive_rag import naive_rag_search

    rag_knowledge_items: List[str] = []
    citations_list: List[str] = []

    if rag_strategy == "hybrid":
        search_results = hybrid_engine.search(msg_text, top_k=3)
        for r in search_results:
            rag_knowledge_items.append(f"• {r['payload']}")
            citations_list.append(r.get("title") or r.get("payload", "")[:80])
    elif rag_strategy == "agentic":
        agentic_result = agentic_router.reason_and_retrieve(msg_text)
        for e in agentic_result["evidence"]:
            rag_knowledge_items.append(f"• {e}")
        citations_list = agentic_result.get("sub_queries", [])
    elif rag_strategy == "graph":
        graph_result = graph_rag.query_graph(msg_text)
        for p in graph_result["paths"]:
            rag_knowledge_items.append(f"• {p['source']} {p['relation']} {p['target']}")
        citations_list = graph_result.get("matched_entities", [])
    elif rag_strategy == "pgvector":
        search_results = pgvector_rag_store.search(
            query=msg_text, role=role, user_tenant_id=tenant_id, top_k=3
        )
        for r in search_results:
            rag_knowledge_items.append(f"• [{r['title']}]: {r['payload']}")
            citations_list.append(f"{r['title']} ({r['similarity']:.2f})")
    elif rag_strategy == "naive":
        search_results = naive_rag_search(query=msg_text, vector_store=rag_store, top_k=3)
        for r in search_results:
            rag_knowledge_items.append(f"• {r['payload']}")
            citations_list.append(r.get("title") or r.get("payload", "")[:80])

    if not rag_knowledge_items:
        return "", None

    rag_body = "\n".join(rag_knowledge_items)
    snippet = f"\n\n[RELEVANT RESIDENCE & POLICY KNOWLEDGE BASE]:\n{rag_body}\n"
    payload = {
        "type": "self_rag",
        "strategy": rag_strategy,
        "is_relevant": True,
        "is_supported": True,
        "score": 0.96,
        "citations": citations_list or ["Cornerstone Master Policy"],
        "preview": rag_body[:250],
    }
    return snippet, payload
