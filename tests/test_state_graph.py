"""
State Graph Test Suite (tests/test_state_graph.py)
Comprehensive test suite verifying all 3 state graphs, HITL lifecycle, failure ticketing, checkpointer, and recovery.
"""
import uuid
import pytest
from scripts.demo_crash_recovery import main as run_crash_demo
from state_graph.checkpoint import DurableCheckpointer
from state_graph.graphs.eviction_flow import build_eviction_flow_graph
from state_graph.graphs.lease_flow import build_lease_flow_graph
from state_graph.graphs.renovation_flow import build_renovation_flow_graph
from state_graph.hitl import HITLManager
from state_graph.models import GraphState
from state_graph.tickets import TicketSystem


def test_graph_1_lease_flow_hitl():
    checkpointer = DurableCheckpointer()
    graph = build_lease_flow_graph(checkpointer=checkpointer)
    state = GraphState(
        run_id=f"test-lease-{uuid.uuid4().hex[:6]}",
        graph_id="commercial_lease_flow",
        current_node="decompose_requirements",
        variables={"unit_id": 301, "proposed_rent": 45000.0, "base_rent": 60000.0}
    )
    result = graph.run(state)
    assert result.status in ("AWAITING_WEBHOOK", "PAUSED_HITL", "PAUSE_HITL")
    assert result.current_node in ("await_bank_escrow", "execute_lease_final", "accountant_deposit_verification")

    # Escrow confirmed triggers executive HITL approval
    result.variables["bank_webhook_payload"] = {"escrow_confirmed": True, "transaction_id": "BM-9901"}
    result.status = "RUNNING"
    result_hitl = graph.run(result)
    assert result_hitl.status in ("PAUSED_HITL", "PAUSE_HITL")
    assert result_hitl.pending_hitl is not None
    checkpointer.close()


def test_graph_2_maintenance_lats_flow():
    checkpointer = DurableCheckpointer()
    graph = build_renovation_flow_graph(checkpointer=checkpointer)
    state = GraphState(
        run_id=f"test-maint-{uuid.uuid4().hex[:6]}",
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        variables={"property_name": "Cornerstone Heights - Zamalek", "location": "Cornerstone Heights - Zamalek"}
    )
    result = graph.run(state)
    assert result.status in ("PAUSED_HITL", "PAUSE_HITL")
    assert result.current_node in ("tenant_completion_and_rating", "engineer_hitl_approval")
    assert result.variables.get("selected_contractor") == "Nile Specialized Engineering & Maintenance"
    checkpointer.close()


def test_graph_3_arrears_tot_negotiation_cycle():
    checkpointer = DurableCheckpointer()
    graph = build_eviction_flow_graph(checkpointer=checkpointer)
    state = GraphState(
        run_id=f"test-arrears-{uuid.uuid4().hex[:6]}",
        graph_id="rent_arrears_settlement_flow",
        current_node="audit_arrears_and_profile",
        variables={"tenant_id": 1, "unpaid_months": 3, "monthly_rent": 40000.0}
    )
    result = graph.run(state)
    assert result.status in ("AWAITING_WEBHOOK", "WAIT_WEBHOOK")
    assert result.current_node == "await_tenant_choice_or_counter"
    assert result.variables["total_arrears"] == 120000.0
    assert result.variables["proposed_settlement"]["installments_count"] == 6

    # Test Counter-Offer Cycle (Tenant requests 9 months)
    result.variables["tenant_negotiation_response"] = {"action": "COUNTER_OFFER", "requested_months": 9}
    result.status = "RUNNING"
    result_counter = graph.run(result)
    assert result_counter.status in ("AWAITING_WEBHOOK", "WAIT_WEBHOOK")
    assert result_counter.variables.get("requested_months") == 9

    # Test Tenant Accept -> HITL Counsel Approval
    result_counter.variables["tenant_negotiation_response"] = {"action": "ACCEPT"}
    result_counter.status = "RUNNING"
    result_counsel = graph.run(result_counter)
    assert result_counsel.status in ("PAUSED_HITL", "PAUSE_HITL")
    assert result_counsel.pending_hitl is not None
    assert "Legal Counsel" in result_counsel.pending_hitl["reason"]

    # Test Counsel Ratification -> Activation
    result_counsel.variables["counsel_decision"] = "APPROVED"
    result_counsel.status = "RUNNING"
    result_final = graph.run(result_counsel)
    assert result_final.status == "COMPLETED"
    assert result_final.variables["settlement_status"] == "ACTIVE"
    assert result_final.variables["legal_hold"] is False
    checkpointer.close()


def test_hitl_task_lifecycle():
    manager = HITLManager()
    task_id = manager.create_task(f"run-{uuid.uuid4().hex[:6]}", "test_graph", "review_node", "High discount", {"discount": 25})
    assert task_id is not None
    pending = manager.list_pending_tasks()
    assert any(t["task_id"] == task_id for t in pending)
    assert manager.resolve_task(task_id, "approved", "Looks good", "Lead Auditor")
    manager.close()


def test_failure_ticket_lifecycle():
    system = TicketSystem()
    try:
        raise ValueError("Simulated DB connection failure during escrow transfer")
    except Exception as e:
        ticket_id = system.open_ticket(f"run-err-{uuid.uuid4().hex[:6]}", "test_graph", "escrow_transfer", e, {"balance": 1000})
    assert ticket_id.startswith("TCK-")
    tickets = system.list_tickets("open")
    assert any(t["ticket_id"] == ticket_id for t in tickets)
    assert system.resolve_ticket(ticket_id, "Restarted connection pool", "DevOps Admin")
    system.close()


def test_durable_checkpointer_save_load_list():
    """Test saving, loading latest, and listing checkpoints with DurableCheckpointer."""
    checkpointer = DurableCheckpointer()
    run_id = f"test-checkpointer-run-{uuid.uuid4().hex[:6]}"
    state = GraphState(
        run_id=run_id,
        graph_id="renovation_permit_flow",
        current_node="retrieve_engineering_policy",
        step_number=1,
        variables={"location": "Zamalek"}
    )
    cp_id = checkpointer.save_checkpoint(state)
    assert cp_id is not None
    loaded_state = checkpointer.load_latest_checkpoint(run_id)
    assert loaded_state is not None
    assert loaded_state.run_id == run_id
    assert loaded_state.variables["location"] == "Zamalek"
    cps = checkpointer.list_checkpoints(run_id)
    assert len(cps) >= 1
    assert cps[0]["node"] == "retrieve_engineering_policy"
    checkpointer.close()


def test_crash_recovery_demo_execution():
    """Verify scripts/demo_crash_recovery.py main() executes without errors."""
    run_crash_demo()


def test_checkpoint_time_travel_diff_and_rollback():
    """Verify time-travel state diffing and historical snapshot rollback engine."""
    checkpointer = DurableCheckpointer()
    run_id = f"test-time-travel-{uuid.uuid4().hex[:6]}"
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
    diff = checkpointer.diff_checkpoints(run_id, 1, 2)
    assert diff["from_step"] == 1
    assert diff["to_step"] == 2
    assert "vendor" in diff["added_variables"]
    assert diff["modified_variables"]["budget"]["from"] == 10000.0
    assert diff["modified_variables"]["budget"]["to"] == 18500.0
    rolled_back = checkpointer.rollback_to_checkpoint(run_id, 1)
    assert rolled_back is not None
    assert rolled_back.variables["stage"] == "initial"
    assert rolled_back.variables["budget"] == 10000.0
    assert rolled_back.step_number == 3
    assert any("Rolled back" in h.get("message", "") for h in rolled_back.history)
    checkpointer.close()


def test_renovation_flow_multi_criteria_vendor_scoring():
    """Verify Graph 2 multi-criteria vendor scoring engine."""
    checkpointer = DurableCheckpointer()
    graph = build_renovation_flow_graph(checkpointer=checkpointer)
    initial_state = GraphState(
        run_id=f"test-scoring-run-{uuid.uuid4().hex[:6]}",
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
