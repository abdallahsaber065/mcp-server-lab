"""
Graph 1: Commercial Lease & Escrow Flow — Native LangGraph
Clean, modern StateGraph compiling LeaseState and typed modular nodes.
"""
from typing import Any, Optional
from langgraph.graph import StateGraph, START, END

from state_graph.schemas.lease_schema import LeaseState
from state_graph.nodes.lease_nodes import (
    decompose_requirements_node,
    audit_unit_and_credit_node,
    verify_receipt_vision_node,
    accountant_verification_node,
    executive_concession_node,
    execute_lease_node,
)


def _route_after_audit(state: LeaseState) -> str:
    """Route from audit to vision receipt verification."""
    return "verify_receipt_vision"


def _route_after_vision(state: LeaseState) -> str:
    """Route from vision receipt to accountant verification."""
    return "accountant_verification"


def _route_after_accountant(state: LeaseState) -> str:
    """Route based on accountant verification and concession threshold (>15% or rent > 40k)."""
    verified = state.get("accountant_verified", True)
    if not verified:
        return "verify_receipt_vision"

    disc = float(state.get("discount_pct", 20.0))
    proposed = float(state.get("proposed_rent", 48000.0))
    if disc > 15.0 or proposed > 40000.0:
        return "executive_concession"
    return "execute_lease"


def _route_after_executive(state: LeaseState) -> str:
    """Route based on executive concession decision."""
    decision = state.get("executive_decision", "APPROVE")
    if decision == "REJECT":
        return END
    elif decision == "COUNTER_10PCT":
        return "decompose_requirements"
    return "execute_lease"


def build_lease_flow_graph(checkpointer: Optional[Any] = None) -> Any:
    """Build and compile the native LangGraph for Commercial Lease Onboarding."""
    workflow = StateGraph(LeaseState)

    # Register Nodes
    workflow.add_node("decompose_requirements", decompose_requirements_node)
    workflow.add_node("audit_unit_and_credit", audit_unit_and_credit_node)
    workflow.add_node("verify_receipt_vision", verify_receipt_vision_node)
    workflow.add_node("accountant_verification", accountant_verification_node)
    workflow.add_node("executive_concession", executive_concession_node)
    workflow.add_node("execute_lease", execute_lease_node)

    # Wire Edges
    workflow.add_edge(START, "decompose_requirements")
    workflow.add_edge("decompose_requirements", "audit_unit_and_credit")
    workflow.add_conditional_edges("audit_unit_and_credit", _route_after_audit)
    workflow.add_conditional_edges("verify_receipt_vision", _route_after_vision)
    workflow.add_conditional_edges("accountant_verification", _route_after_accountant)
    workflow.add_conditional_edges("executive_concession", _route_after_executive)
    workflow.add_edge("execute_lease", END)

    from langgraph.checkpoint.base import BaseCheckpointSaver
    if checkpointer is None:
        from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
        langgraph_checkpointer = SQLAlchemyLangGraphCheckpointer()
    elif isinstance(checkpointer, BaseCheckpointSaver):
        langgraph_checkpointer = checkpointer
    else:
        langgraph_checkpointer = None

    compiled = workflow.compile(checkpointer=langgraph_checkpointer)
    compiled.graph_id = "commercial_lease_flow"  # type: ignore[attr-defined]
    return compiled


build_lease_graph = build_lease_flow_graph
