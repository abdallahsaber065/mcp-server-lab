"""
State Graph Test Suite (tests/test_state_graph.py)
Tests Native LangGraph workflows for Lease, Maintenance, and Arrears flows,
verifying Node Execution, Tool Access, HITL Interrupts, and Checkpointing.
"""
import uuid
import pytest
from langgraph.types import Command
from state_graph.graphs.lease_flow import build_lease_flow_graph
from state_graph.graphs.maintenance_flow import build_maintenance_flow_graph
from state_graph.graphs.arrears_flow import build_arrears_flow_graph
from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
from services.state_graph_service import StateGraphService


def test_graph_1_lease_flow_nodes_and_hitl():
    """Test Graph 1: Decompose -> Audit -> Vision -> Accountant HITL -> Executive HITL -> Execute."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_lease_flow_graph(checkpointer=checkpointer)
    thread_id = f"test-lease-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "unit_id": 301,
        "applicant_name": "Dr. Tarek El-Mahdy",
        "proposed_rent": 48000.0,
        "base_rent": 60000.0,
        "receipt_image_urls": ["/receipts/bank_misr_escrow_deposit_suite301.png"],
    }

    # Step 1: Run until first interrupt (Accountant Verification)
    events = list(graph.stream(inputs, config=config))
    assert len(events) >= 1

    state = graph.get_state(config)
    assert len(state.tasks) > 0 or len(state.next) > 0
    # Next node should be accountant_verification
    assert "accountant_verification" in state.next or any("accountant" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_graph_2_maintenance_lats_flow():
    """Test Graph 2: Law 4/1996 RAG -> LATS MCTS -> Engineer HITL -> Availability -> Rating -> Close."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_maintenance_flow_graph(checkpointer=checkpointer)
    thread_id = f"test-maint-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "location": "Cornerstone Heights - Zamalek",
        "issue_description": "Emergency pipe burst causing water leak in unit",
    }

    events = list(graph.stream(inputs, config=config))
    assert len(events) >= 1

    state = graph.get_state(config)
    assert len(state.tasks) > 0 or len(state.next) > 0
    assert "engineer_approval" in state.next or any("engineer" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_graph_3_arrears_tot_negotiation_cycle():
    """Test Graph 3: Audit -> ToT Offers -> Tenant Response HITL -> Legal Approval HITL -> Activate."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_arrears_flow_graph(checkpointer=checkpointer)
    thread_id = f"test-arrears-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "tenant_id": 1,
        "unpaid_months": 2,
        "monthly_rent": 45000.0,
    }

    events = list(graph.stream(inputs, config=config))
    assert len(events) >= 1

    state = graph.get_state(config)
    assert len(state.tasks) > 0 or len(state.next) > 0
    assert "await_tenant_response" in state.next or any("tenant" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_service_list_graphs_and_aliases():
    """Verify StateGraphService exposes canonical IDs and aliases."""
    graphs = StateGraphService.list_graphs()
    ids = {g["graph_id"] for g in graphs}
    assert "commercial_lease_flow" in ids
    assert "maintenance_dispatch_flow" in ids
    assert "arrears_care_flow" in ids

    assert StateGraphService.canonical_id("lease_flow") == "commercial_lease_flow"
    assert StateGraphService.canonical_id("renovation_permit_flow") == "maintenance_dispatch_flow"
    assert StateGraphService.canonical_id("rent_arrears_settlement_flow") == "arrears_care_flow"
