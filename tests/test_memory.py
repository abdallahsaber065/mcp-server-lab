import pytest
from mcp_server.memory import (
    memory_store, decide_memory_fate,
    RecordMemoryInput, RecallMemoryInput,
    record_tenant_memory_handler, recall_tenant_memories_handler
)
from mcp_server.server import CornerstoneMCPServer

def test_memory_routing_decision():
    """Verify memory fate decision routing logic."""
    decision_keep = decide_memory_fate("Tenant prefers morning appointments and has dust allergy")
    assert decision_keep.destination == "episodic"

    decision_forget = decide_memory_fate("Good morning, how are you today?")
    assert decision_forget.destination == "forget"

def test_episodic_memory_isolation_and_recall():
    """Verify two separate runs/sessions recall entity-scoped memories without cross-tenant leakage."""
    tenant_a_id = 901
    tenant_b_id = 902

    # Session 1: Record fact for Tenant A
    memory_store.record_memory(
        tenant_id=tenant_a_id,
        event_summary="Tenant A prefers email contact only and requires handicap parking.",
        category="preference"
    )

    # Session 1: Record fact for Tenant B
    memory_store.record_memory(
        tenant_id=tenant_b_id,
        event_summary="Tenant B requires high-voltage EV charger station.",
        category="preference"
    )

    # Session 2: Recall for Tenant A (separate query run)
    recalled_a = memory_store.recall_memories(tenant_id=tenant_a_id, query="parking email")
    assert len(recalled_a) > 0
    assert "handicap parking" in recalled_a[0]["event_summary"]

    # Session 2: Recall for Tenant B (separate query run)
    recalled_b = memory_store.recall_memories(tenant_id=tenant_b_id, query="EV charger")
    assert len(recalled_b) > 0
    assert "EV charger" in recalled_b[0]["event_summary"]

    # Cross-tenant check: Tenant B query on Tenant A returns nothing
    empty_cross = memory_store.recall_memories(tenant_id=tenant_b_id, query="handicap parking")
    assert len(empty_cross) == 0

def test_memory_mcp_server_integration():
    """Verify record_tenant_memory and recall_tenant_memories via CornerstoneMCPServer instance."""
    server = CornerstoneMCPServer()

    # Record via server tool call
    rec_res = server.call_tool(
        "record_tenant_memory",
        {
            "tenant_id": 1,
            "event_summary": "Tenant requested quiet weekend maintenance window.",
            "category": "preference"
        }
    )
    assert rec_res["status"] == "success"

    # Recall via server tool call
    recall_res = server.call_tool(
        "recall_tenant_memories",
        {
            "tenant_id": 1,
            "query": "quiet weekend maintenance"
        }
    )
    assert recall_res["status"] == "success"
    assert recall_res["count"] > 0
    assert any("quiet weekend" in m["event_summary"] for m in recall_res["memories"])

def test_memory_schema_extra_forbid():
    """Verify defensive Pydantic schema extra='forbid' validation."""
    with pytest.raises(Exception):
        RecordMemoryInput.model_validate({
            "tenant_id": 1,
            "event_summary": "test",
            "malicious_extra_prop": "error"
        })

def test_maybe_remember_and_load_memory_context():
    """Verify exact functions from option_b_memory_example.py work as expected."""
    from mcp_server.memory import maybe_remember, load_memory_context

    # 1. Transient turn -> forget
    forget_res = maybe_remember("The weather is nice today.", "tenant_42")
    assert forget_res is None

    # 2. Preference turn -> episodic
    store_res = maybe_remember("Tenant prefers morning appointments and has a severe penicillin allergy.", "tenant_42")
    assert store_res is not None
    assert store_res["tenant_id"] == 42

    # 3. Load memory context string
    context_str = load_memory_context("tenant_42", "penicillin allergy concerns")
    assert "Relevant past notes:" in context_str
    assert "penicillin allergy" in context_str
