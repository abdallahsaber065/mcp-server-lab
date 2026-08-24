"""
Graph 2: Emergency Maintenance & LATS Tendering — Native LangGraph
Clean, modern StateGraph compiling MaintenanceState and typed modular nodes.
"""
from typing import Any, Optional
from langgraph.graph import StateGraph, START, END

from state_graph.schemas.maintenance_schema import MaintenanceState
from state_graph.nodes.maintenance_nodes import (
    retrieve_policy_node,
    lats_tender_search_node,
    engineer_approval_node,
    check_availability_node,
    tenant_rating_node,
    close_ticket_node,
)


def _route_after_tender(state: MaintenanceState) -> str:
    """Route to engineer approval if quote > 10,000 EGP, else dispatch directly."""
    estimate = float(state.get("estimate", 14500.0))
    if estimate > 10000.0:
        return "engineer_approval"
    return "check_availability"


def _route_after_engineer(state: MaintenanceState) -> str:
    """Route based on engineer approval."""
    approved = state.get("engineer_approved", True)
    if approved:
        return "check_availability"
    return "lats_tender_search"


def _route_after_availability(state: MaintenanceState) -> str:
    """Route based on contractor availability."""
    available = state.get("contractor_available", True)
    if available:
        return "tenant_rating"
    return "lats_tender_search"


def _route_after_rating(state: MaintenanceState) -> str:
    """Route based on tenant satisfaction rating."""
    rating = int(state.get("tenant_rating", 5))
    if rating >= 3:
        return "close_ticket"
    return "lats_tender_search"


def build_maintenance_flow_graph(checkpointer: Optional[Any] = None) -> Any:
    """Build and compile the native LangGraph for Emergency Maintenance & LATS Tendering."""
    workflow = StateGraph(MaintenanceState)

    # Register Nodes
    workflow.add_node("retrieve_policy", retrieve_policy_node)
    workflow.add_node("lats_tender_search", lats_tender_search_node)
    workflow.add_node("engineer_approval", engineer_approval_node)
    workflow.add_node("check_availability", check_availability_node)
    workflow.add_node("tenant_rating", tenant_rating_node)
    workflow.add_node("close_ticket", close_ticket_node)

    # Wire Edges
    workflow.add_edge(START, "retrieve_policy")
    workflow.add_edge("retrieve_policy", "lats_tender_search")
    workflow.add_conditional_edges("lats_tender_search", _route_after_tender)
    workflow.add_conditional_edges("engineer_approval", _route_after_engineer)
    workflow.add_conditional_edges("check_availability", _route_after_availability)
    workflow.add_conditional_edges("tenant_rating", _route_after_rating)
    workflow.add_edge("close_ticket", END)

    from langgraph.checkpoint.base import BaseCheckpointSaver
    if checkpointer is None:
        from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
        langgraph_checkpointer = SQLAlchemyLangGraphCheckpointer()
    elif isinstance(checkpointer, BaseCheckpointSaver):
        langgraph_checkpointer = checkpointer
    else:
        langgraph_checkpointer = None

    compiled = workflow.compile(checkpointer=langgraph_checkpointer)
    compiled.graph_id = "maintenance_dispatch_flow"  # type: ignore[attr-defined]
    return compiled


build_maintenance_graph = build_maintenance_flow_graph
