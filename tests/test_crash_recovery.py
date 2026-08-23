"""
Crash-and-Resume durability test — native LangGraph with SQLAlchemy checkpoint persistence
"""
import uuid
import pytest
from langgraph.types import Command
from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
from state_graph.graphs.lease_flow import build_lease_flow_graph


def test_crash_and_resume_recovery():
    """Verify atomic state persistence across process restarts using LangGraph checkpointing."""
    thread_id = f"test-crash-recovery-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}
    checkpointer = SQLAlchemyLangGraphCheckpointer()

    # 1. Initial run until first HITL (Accountant Verification)
    graph = build_lease_flow_graph(checkpointer=checkpointer)
    inputs = {
        "unit_id": 301,
        "applicant_name": "Dr. Tarek El-Mahdy",
        "base_rent": 60000.0,
        "proposed_rent": 48000.0,
        "receipt_image_urls": ["/receipts/bank_misr_escrow_deposit_suite301.png"],
    }
    events = list(graph.stream(inputs, config=config))
    assert len(events) >= 1

    state_before_kill = graph.get_state(config)
    assert len(state_before_kill.tasks) > 0 or len(state_before_kill.next) > 0
    assert "accountant_verification" in state_before_kill.next or any("accountant" in str(getattr(t, "interrupts", [])) for t in state_before_kill.tasks)

    # 2. Simulate process restart: completely new checkpointer & graph instances
    del graph
    del checkpointer

    new_checkpointer = SQLAlchemyLangGraphCheckpointer()
    new_graph = build_lease_flow_graph(checkpointer=new_checkpointer)

    # State should be restored directly from database
    recovered_state = new_graph.get_state(config)
    assert recovered_state.values.get("unit_id") == 301
    assert recovered_state.values.get("proposed_rent") == 48000.0
    assert "accountant_verification" in recovered_state.next or any("accountant" in str(getattr(t, "interrupts", [])) for t in recovered_state.tasks)

    # 3. Resume from saved checkpoint using Command(resume=...)
    resume_events = list(new_graph.stream(Command(resume={"approved": True, "notes": "Funds verified"}), config=config))
    assert len(resume_events) >= 1

    post_resume_state = new_graph.get_state(config)
    # Next should be executive concession HITL
    assert "executive_concession" in post_resume_state.next or any("executive" in str(getattr(t, "interrupts", [])) for t in post_resume_state.tasks)
