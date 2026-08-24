"""
Graph 3: Arrears Remediation & ToT Negotiation — Native LangGraph
Clean, modern StateGraph compiling ArrearsState and typed modular nodes.
"""
from typing import Any, Optional
from langgraph.graph import StateGraph, START, END

from state_graph.schemas.arrears_schema import ArrearsState
from state_graph.nodes.arrears_nodes import (
    audit_arrears_node,
    tot_offers_generator_node,
    await_tenant_response_node,
    finance_legal_approval_node,
    activate_plan_node,
    escalate_refusal_node,
)


def _route_after_audit(state: ArrearsState) -> str:
    """Route from audit to ToT offers generation."""
    return "tot_offers_generator"


def _route_after_tot(state: ArrearsState) -> str:
    """Route from ToT generation to awaiting tenant response."""
    return "await_tenant_response"


def _route_after_tenant_response(state: ArrearsState) -> str:
    """Route based on tenant choice."""
    choice = state.get("tenant_choice", "A")
    if choice in ("REJECT", "REFUSE", "NO"):
        return "escalate_refusal"
    elif choice in ("COUNTER", "CUSTOM"):
        return "tot_offers_generator"
    return "finance_legal_approval"


def _route_after_legal(state: ArrearsState) -> str:
    """Route based on legal counsel approval."""
    approved = state.get("legal_approved", True)
    if approved:
        return "activate_plan"
    return "tot_offers_generator"


def build_arrears_flow_graph(checkpointer: Optional[Any] = None) -> Any:
    """Build and compile the native LangGraph for Arrears Remediation & ToT Negotiation."""
    workflow = StateGraph(ArrearsState)

    # Register Nodes
    workflow.add_node("audit_arrears", audit_arrears_node)
    workflow.add_node("tot_offers_generator", tot_offers_generator_node)
    workflow.add_node("await_tenant_response", await_tenant_response_node)
    workflow.add_node("finance_legal_approval", finance_legal_approval_node)
    workflow.add_node("activate_plan", activate_plan_node)
    workflow.add_node("escalate_refusal", escalate_refusal_node)

    # Wire Edges
    workflow.add_edge(START, "audit_arrears")
    workflow.add_conditional_edges("audit_arrears", _route_after_audit)
    workflow.add_conditional_edges("tot_offers_generator", _route_after_tot)
    workflow.add_conditional_edges("await_tenant_response", _route_after_tenant_response)
    workflow.add_conditional_edges("finance_legal_approval", _route_after_legal)
    workflow.add_edge("activate_plan", END)
    workflow.add_edge("escalate_refusal", END)

    from langgraph.checkpoint.base import BaseCheckpointSaver
    if checkpointer is None:
        from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
        langgraph_checkpointer = SQLAlchemyLangGraphCheckpointer()
    elif isinstance(checkpointer, BaseCheckpointSaver):
        langgraph_checkpointer = checkpointer
    else:
        langgraph_checkpointer = None

    compiled = workflow.compile(checkpointer=langgraph_checkpointer)
    compiled.graph_id = "arrears_care_flow"  # type: ignore[attr-defined]
    return compiled


build_arrears_graph = build_arrears_flow_graph
