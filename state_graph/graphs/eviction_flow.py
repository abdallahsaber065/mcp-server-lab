"""
Legacy alias — delegates to arrears_flow native LangGraph (no mocks)
"""
from state_graph.graphs.arrears_flow import build_arrears_flow_graph

def build_eviction_flow_graph(checkpointer=None):
    return build_arrears_flow_graph(checkpointer)

__all__ = ["build_eviction_flow_graph"]
