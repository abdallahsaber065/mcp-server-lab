"""
Legacy alias — delegates to maintenance_flow native LangGraph (no mocks)
"""
from state_graph.graphs.maintenance_flow import build_maintenance_flow_graph

def build_renovation_flow_graph(checkpointer=None):
    return build_maintenance_flow_graph(checkpointer)

# Re-export for backward compat
__all__ = ["build_renovation_flow_graph"]
