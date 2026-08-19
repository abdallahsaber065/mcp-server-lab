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
    assert result1.current_node == "tenant_completion_and_rating"
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


def test_checkpoint_time_travel_diff_and_rollback():
    """Verify time-travel state diffing and historical snapshot rollback engine (Issue #37)."""
    checkpointer = DurableCheckpointer()
    run_id = "test-time-travel-run"
    
    state_s1 = GraphState(
        run_id=run_id,
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        step_number=1,
        variables={"stage": "initial", "budget": 10000.0}
    )
    checkpointer.save_checkpoint(state_s1)
    
    state_s2 = GraphState(
        run_id=run_id,
        graph_id="renovation_permit_flow",
        current_node="lats_vendor_tender_search",
        step_number=2,
        variables={"stage": "tender_selected", "budget": 18500.0, "vendor": "Nile Specialized"}
    )
    checkpointer.save_checkpoint(state_s2)
    
    # 1. Compute state diff between Step 1 and Step 2
    diff = checkpointer.diff_checkpoints(run_id, 1, 2)
    assert diff["from_step"] == 1
    assert diff["to_step"] == 2
    assert "vendor" in diff["added_variables"]
    assert diff["modified_variables"]["budget"]["from"] == 10000.0
    assert diff["modified_variables"]["budget"]["to"] == 18500.0
    
    # 2. Rollback to Step 1
    rolled_back = checkpointer.rollback_to_checkpoint(run_id, 1)
    assert rolled_back is not None
    assert rolled_back.variables["stage"] == "initial"
    assert rolled_back.variables["budget"] == 10000.0
    assert rolled_back.step_number == 3
    assert any("Rolled back" in h.get("message", "") for h in rolled_back.history)
    
    checkpointer.close()


def test_renovation_flow_multi_criteria_vendor_scoring():
    """Verify Graph 2 multi-criteria vendor scoring engine (Issue #38)."""
    checkpointer = DurableCheckpointer()
    graph = build_renovation_flow_graph(checkpointer=checkpointer)
    
    initial_state = GraphState(
        run_id="test-scoring-run",
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        variables={"location": "Cornerstone Heights - Zamalek"}
    )
    res = graph.run(initial_state)
    assert "vendor_sla_matrix" in res.variables
    matrix = res.variables["vendor_sla_matrix"]
    assert matrix["vendor_name"] == "Nile Specialized Engineering & Maintenance"
    assert matrix["dispatch_sla_hours"] == 1.5
    assert matrix["composite_score"] > 0.5
    
    checkpointer.close()

