import pytest
from mcp_server.rag import knowledge_store, SearchKnowledgeBaseInput, search_knowledge_base_handler
from mcp_server.server import CornerstoneMCPServer

def test_rag_bm25_store_query():
    """Verify BM25 store returns relevant chunks matching keywords."""
    results = knowledge_store.query("early termination penalty", top_k=2)
    assert len(results) > 0
    assert "60-day written notice" in results[0]["payload"]
    assert results[0]["score"] > 0.0

def test_rag_tool_schema_extra_forbid():
    """Verify defensive Pydantic schema extra='forbid' validation."""
    with pytest.raises(Exception):
        SearchKnowledgeBaseInput.model_validate({
            "query": "lease penalty",
            "unwanted_extra_field": "hacker_payload"
        })

def test_rag_role_authorization_filtering():
    """Verify server-side role filtering hides executive-only documents from standard roles."""
    # Executive admin query should see confidential commercial escalation clause
    exec_res = search_knowledge_base_handler(
        {"query": "commercial escalation clause rent waivers"},
        session_role="executive_admin"
    )
    assert exec_res["status"] == "success"
    assert any("annual 7.5% rent escalation" in r["content"] for r in exec_res["results"])

    # Tenant query for the same topic should NOT see confidential executive document
    tenant_res = search_knowledge_base_handler(
        {"query": "commercial escalation clause rent waivers"},
        session_role="tenant"
    )
    # Either no results or filtered out executive items
    if tenant_res["status"] == "success":
        assert all("executive_rules" not in r.get("id", "") for r in tenant_res["results"])
        assert not any("Confidential Commercial" in r["content"] for r in tenant_res["results"])

def test_rag_mcp_server_integration():
    """Verify search_knowledge_base via CornerstoneMCPServer instance."""
    server = CornerstoneMCPServer()
    res = server.call_tool(
        "search_knowledge_base",
        {"query": "quiet hours pets weight"}
    )
    assert res["status"] == "success"
    assert res["count"] > 0
    assert any("10:00 PM and 7:00 AM" in r["content"] for r in res["results"])
