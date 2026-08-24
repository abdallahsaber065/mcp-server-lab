"""
State Graph Subsystem Package (state_graph/)
Provides persistent, recoverable state graph engines, checkpointing, HITL nodes, and failure recovery tickets.
"""

from state_graph.models import GraphState, NodeResult

try:
    from state_graph.engine import StateGraph  # deprecated, use langgraph.graph.StateGraph
except Exception:  # pragma: no cover
    StateGraph = None  # type: ignore

__all__ = ["GraphState", "NodeResult", "StateGraph"]
