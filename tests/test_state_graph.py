"""
Unit & Integration Tests for Durable Checkpointer & Graph 2 Renovation Flow (tests/test_state_graph.py)
"""

import pytest
from state_graph.checkpoint import DurableCheckpointer
from state_graph.models import GraphState
from state_graph.graphs.renovation_flow import build_renovation_flow_graph
from scripts.demo_crash_recovery import main as run_crash_demo


def test_durable_checkpointer_save_load_list():
    """Test saving, loading latest, and listing checkpoints with DurableCheckpointer."""
    checkpointer = DurableCheckpointer()
    state = GraphState(
        run_id="test-checkpointer-run-1",
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        step_number=1,
        variables={"location": "Zamalek"}
    )
    
    # Save checkpoint
    cp_id = checkpointer.save_checkpoint(state)
    assert cp_id is not None
    
    # Load latest checkpoint
    loaded_state = checkpointer.load_latest_checkpoint("test-checkpointer-run-1")
    assert loaded_state is not None
    assert loaded_state.run_id == "test-checkpointer-run-1"
    assert loaded_state.variables["location"] == "Zamalek"
    
    # List checkpoints
    cps = checkpointer.list_checkpoints("test-checkpointer-run-1")
    assert len(cps) >= 1
    assert cps[0]["node"] == "retrieve_engineering_policy"
    
    checkpointer.close()


def test_renovation_flow_execution_full():
    """Verify Graph 2 (Emergency Maintenance Dispatch & Contractor Tendering)."""
    checkpointer = DurableCheckpointer()
    graph = build_renovation_flow_graph(checkpointer=checkpointer)
    
    # 1. Initial run -> executes retrieve policy & LATS -> pauses at HITL engineer approval
    initial_state = GraphState(
        run_id="renovation-test-1",
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        variables={"location": "Cornerstone Heights - Zamalek", "property_name": "Zamalek Royal Suites"}
    )
    result1 = graph.run(initial_state)
    assert result1.status == "PAUSED_HITL"
    assert result1.current_node == "engineer_hitl_approval"
    assert result1.pending_hitl is not None
    assert "Chief Maintenance Engineer Approval Required" in result1.pending_hitl["reason"]
    assert result1.variables.get("selected_contractor") == "Nile Specialized Engineering & Maintenance"
    
    # 2. Engineer approves work order -> resumes execution -> pauses at tenant webhook
    result1.variables["engineer_decision"] = "APPROVED"
    result1.status = "RUNNING"
    result2 = graph.run(result1)
    assert result2.status == "AWAITING_WEBHOOK"
    assert result2.current_node == "tenant_completion_and_rating"
    
    # 3. Tenant completes physical inspection and submits 5-star rating -> finishes
    result2.variables["tenant_confirmation_payload"] = {"rating": 5}
    result2.status = "RUNNING"
    result3 = graph.run(result2)
    assert result3.status == "COMPLETED"
    assert result3.variables["work_order_status"] == "RESOLVED"
    assert result3.variables["tenant_rating"] == 5
    
    checkpointer.close()


def test_crash_recovery_demo_execution():
    """Verify scripts/demo_crash_recovery.py main() executes without errors."""
    run_crash_demo()
