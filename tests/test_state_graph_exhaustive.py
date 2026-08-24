"""
Exhaustive Native LangGraph Test Suite for the 3 Domain State Graphs
Graph 1: Commercial Lease & Escrow (decompose -> audit -> vision -> accountant HITL -> executive HITL -> execute)
Graph 2: Emergency Maintenance & LATS (retrieve Law 4/1996 -> LATS MCTS -> engineer HITL -> availability -> tenant rating -> close)
Graph 3: Arrears Remediation & ToT (audit arrears -> ToT offers -> tenant choice HITL -> legal counsel HITL -> activate)
"""
import uuid
import pytest
from langgraph.types import Command
from services.state_graph_service import StateGraphService, ALIASES
from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
from state_graph.graphs.lease_flow import build_lease_flow_graph
from state_graph.graphs.maintenance_flow import build_maintenance_flow_graph
from state_graph.graphs.arrears_flow import build_arrears_flow_graph


# ============================================================================
# Graph 1: Commercial Lease Flow
# ============================================================================
def test_g1_execution_pauses_at_accountant_hitl():
    """Verify Graph 1 runs through decomposition, audit, and vision, then pauses for Accountant."""
    graph = build_lease_flow_graph()
    thread_id = f"g1-test-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "unit_id": 301,
        "applicant_name": "Dr. Tarek El-Mahdy",
        "proposed_rent": 48000.0,
        "base_rent": 60000.0,
    }
    list(graph.stream(inputs, config=config))
    state = graph.get_state(config)

    assert "accountant_verification" in state.next or any("accountant" in str(getattr(t, "interrupts", [])) for t in state.tasks)
    assert state.values.get("discount_pct") == 20.0
    assert state.values.get("escrow_required") == 144000.0


def test_g1_accountant_approved_triggers_executive_concession():
    """Verify Accountant approval on a 20% discount routes to Executive Concession HITL."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_lease_flow_graph(checkpointer=checkpointer)
    thread_id = f"g1-acct-exec-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "unit_id": 301,
        "applicant_name": "Dr. Tarek El-Mahdy",
        "proposed_rent": 48000.0,
        "base_rent": 60000.0,
        "receipt_image_urls": ["/receipts/bank_misr_escrow_deposit_suite301.png"],
    }
    list(graph.stream(inputs, config=config))

    # Resume Accountant approval
    list(graph.stream(Command(resume={"approved": True, "notes": "Funds confirmed in bank"}), config=config))
    state = graph.get_state(config)

    # Next node should be executive_concession because 20% discount > 15% threshold
    assert "executive_concession" in state.next or any("executive" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_g1_executive_approved_completes_lease():
    """Verify Executive approval completes the lease execution."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_lease_flow_graph(checkpointer=checkpointer)
    thread_id = f"g1-full-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "unit_id": 301,
        "applicant_name": "Dr. Tarek El-Mahdy",
        "proposed_rent": 48000.0,
        "base_rent": 60000.0,
        "receipt_image_urls": ["/receipts/bank_misr_escrow_deposit_suite301.png"],
    }
    list(graph.stream(inputs, config=config))
    # Resume Accountant
    list(graph.stream(Command(resume={"approved": True}), config=config))
    # Resume Executive
    list(graph.stream(Command(resume={"decision": "APPROVE"}), config=config))

    final_state = graph.get_state(config)
    assert final_state.values.get("lease_status") == "active"
    assert final_state.values.get("status") == "COMPLETED"


# ============================================================================
# Graph 2: Emergency Maintenance & LATS Flow
# ============================================================================
def test_g2_execution_pauses_at_engineer_approval():
    """Verify Graph 2 performs Law 4/1996 RAG and LATS MCTS, then pauses for Chief Engineer."""
    graph = build_maintenance_flow_graph()
    thread_id = f"g2-test-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "location": "Nile Heights Tower",
        "issue_description": "Burst pipe water leak",
    }
    list(graph.stream(inputs, config=config))
    state = graph.get_state(config)

    assert "engineer_approval" in state.next or any("engineer" in str(getattr(t, "interrupts", [])) for t in state.tasks)
    assert state.values.get("liability") == "owner"
    assert state.values.get("estimate") > 10000.0


def test_g2_engineer_approved_pauses_for_tenant_rating():
    """Verify Engineer approval routes to vendor dispatch and tenant completion rating."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_maintenance_flow_graph(checkpointer=checkpointer)
    thread_id = f"g2-eng-rating-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "location": "Nile Heights Tower",
        "issue_description": "Burst pipe water leak",
    }
    list(graph.stream(inputs, config=config))
    # Resume Engineer
    list(graph.stream(Command(resume={"approved": True, "notes": "Approved emergency quote"}), config=config))
    state = graph.get_state(config)

    # Next node should be tenant_rating
    assert "tenant_rating" in state.next or any("tenant" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_g2_tenant_rating_completes_work_order():
    """Verify high tenant rating closes the emergency work order."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_maintenance_flow_graph(checkpointer=checkpointer)
    thread_id = f"g2-full-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "location": "Nile Heights Tower",
        "issue_description": "Burst pipe water leak",
    }
    list(graph.stream(inputs, config=config))
    # Resume Engineer
    list(graph.stream(Command(resume={"approved": True}), config=config))
    # Resume Tenant Rating (5 stars)
    list(graph.stream(Command(resume={"rating": 5}), config=config))

    final_state = graph.get_state(config)
    assert final_state.values.get("status") == "COMPLETED"
    assert final_state.values.get("tenant_rating") == 5


# ============================================================================
# Graph 3: Arrears Remediation & ToT Negotiation Flow
# ============================================================================
def test_g3_tot_offers_and_pauses_at_tenant_choice():
    """Verify Graph 3 audits debt, generates 3 ToT restructuring plans, and pauses for Tenant."""
    graph = build_arrears_flow_graph()
    thread_id = f"g3-test-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "tenant_id": 1,
        "unpaid_months": 2,
        "monthly_rent": 45000.0,
    }
    list(graph.stream(inputs, config=config))
    state = graph.get_state(config)

    assert "await_tenant_response" in state.next or any("tenant" in str(getattr(t, "interrupts", [])) for t in state.tasks)
    assert state.values.get("total_arrears") == 90000.0
    assert len(state.values.get("dynamic_offers", [])) == 3


def test_g3_tenant_accept_routes_to_legal_counsel_approval():
    """Verify Tenant accepting Plan A routes to Legal Counsel HITL sign-off."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_arrears_flow_graph(checkpointer=checkpointer)
    thread_id = f"g3-legal-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "tenant_id": 1,
        "unpaid_months": 2,
        "monthly_rent": 45000.0,
    }
    list(graph.stream(inputs, config=config))
    # Resume Tenant selecting Option A
    list(graph.stream(Command(resume={"choice": "A"}), config=config))
    state = graph.get_state(config)

    # Next node should be finance_legal_approval
    assert "finance_legal_approval" in state.next or any("legal" in str(getattr(t, "interrupts", [])) for t in state.tasks)


def test_g3_legal_approved_activates_restructuring_plan():
    """Verify Legal Counsel sign-off activates the debt recovery plan."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_arrears_flow_graph(checkpointer=checkpointer)
    thread_id = f"g3-full-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "tenant_id": 1,
        "unpaid_months": 2,
        "monthly_rent": 45000.0,
    }
    list(graph.stream(inputs, config=config))
    # Resume Tenant (Plan A)
    list(graph.stream(Command(resume={"choice": "A"}), config=config))
    # Resume Legal Counsel
    list(graph.stream(Command(resume={"approved": True, "notes": "Approved restructuring plan"}), config=config))

    final_state = graph.get_state(config)
    assert final_state.values.get("status") == "COMPLETED"
    assert final_state.values.get("legal_approved") is True


def test_g3_tenant_refusal_escalates_to_legal_notice():
    """Verify Tenant rejecting all settlement plans routes to escalation."""
    checkpointer = SQLAlchemyLangGraphCheckpointer()
    graph = build_arrears_flow_graph(checkpointer=checkpointer)
    thread_id = f"g3-refuse-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "tenant_id": 1,
        "unpaid_months": 2,
        "monthly_rent": 45000.0,
    }
    list(graph.stream(inputs, config=config))
    # Resume Tenant with rejection
    list(graph.stream(Command(resume={"choice": "REJECT"}), config=config))

    final_state = graph.get_state(config)
    assert final_state.values.get("status") == "ESCALATED"
