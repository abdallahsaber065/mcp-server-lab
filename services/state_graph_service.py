"""
State Graph Service (services/state_graph_service.py)
Coordinates State Graph execution, checkpoint persistence, webhook resumes, and HITL decisions.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

import logging

from db.repositories.checkpoint_repo import AsyncCheckpointRepository, CheckpointRepository
from state_graph.models import GraphState

logger = logging.getLogger("state_graph.service")


class CheckpointerAdapter:
    def __init__(self, repo: CheckpointRepository):
        self.repo = repo

    def save_checkpoint(self, state: GraphState) -> str:
        return self.repo.save_checkpoint(state)


class AsyncCheckpointerAdapter:
    def __init__(self, repo: AsyncCheckpointRepository):
        self.repo = repo

    async def asave_checkpoint(self, state: GraphState) -> str:
        return await self.repo.save_checkpoint(state)


ALIASES = {
    "graph_commercial_lease": "commercial_lease_flow",
    "graph_renovation_dag": "maintenance_dispatch_flow",
    "graph_eviction_resolution": "arrears_care_flow",
    "lease_flow": "commercial_lease_flow",
    "renovation_flow": "maintenance_dispatch_flow",
    "renovation_permit_flow": "maintenance_dispatch_flow",
    "eviction_flow": "arrears_care_flow",
    "rent_arrears_settlement_flow": "arrears_care_flow",
    "maintenance_flow": "maintenance_dispatch_flow",
    "arrears_flow": "arrears_care_flow",
}


class StateGraphService:
    @staticmethod
    def canonical_id(graph_id: str) -> str:
        return ALIASES.get(graph_id, graph_id)

    @staticmethod
    def get_graph(graph_id: str, checkpointer=None):
        """Return native LangGraph CompiledStateGraph (preferred) or legacy shim."""
        from state_graph.graphs.lease_flow import build_lease_flow_graph
        from state_graph.graphs.maintenance_flow import build_maintenance_flow_graph
        from state_graph.graphs.arrears_flow import build_arrears_flow_graph

        builders = {
            "commercial_lease_flow": build_lease_flow_graph,
            "maintenance_dispatch_flow": build_maintenance_flow_graph,
            "arrears_care_flow": build_arrears_flow_graph,
        }
        gid = StateGraphService.canonical_id(graph_id)
        builder = builders.get(gid)
        if not builder:
            raise HTTPException(status_code=400, detail={"error": f"Unknown graph_id '{graph_id}'", "valid_graph_ids": list(builders.keys()), "aliases": ALIASES})
        logger.info("get_graph gid=%s canonical=%s checkpointer=%s", graph_id, gid, type(checkpointer).__name__ if checkpointer else "None")
        return builder(checkpointer=checkpointer)

    @staticmethod
    def get_native_graph(graph_id: str, checkpointer=None):
        """Explicit native graph accessor for background/platform — with SQLAlchemyLangGraphCheckpointer default."""
        if checkpointer is None:
            try:
                from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
                checkpointer = SQLAlchemyLangGraphCheckpointer()
            except Exception as e:
                logger.warning("native checkpointer fallback failed: %s", e)
                checkpointer = None
        return StateGraphService.get_graph(graph_id, checkpointer=checkpointer)

    @staticmethod
    def list_graphs():
        return [
            {"graph_id": "commercial_lease_flow", "label": "Graph 1: Lease & Escrow — AI reads receipt, accountant verifies paid (TaskDecomp + ReAct + Vision)", "aliases": ["graph_commercial_lease", "lease_flow"]},
            {"graph_id": "maintenance_dispatch_flow", "label": "Graph 2: Maintenance — branching on cost/policy & LATS vendor matrix (RAG + LATS)", "aliases": ["renovation_flow", "renovation_permit_flow"]},
            {"graph_id": "arrears_care_flow", "label": "Graph 3: Arrears Care — dynamic AI-tailored offers, refuse→human (RAG + ToT)", "aliases": ["eviction_flow", "rent_arrears_settlement_flow"]},
        ]

    @staticmethod
    def run_graph(session: Session, initial_state: GraphState) -> GraphState:
        initial_state.graph_id = StateGraphService.canonical_id(initial_state.graph_id)
        repo = CheckpointRepository(session)
        adapter = CheckpointerAdapter(repo)
        graph = StateGraphService.get_graph(initial_state.graph_id, checkpointer=adapter)
        return graph.run(initial_state)

    @staticmethod
    async def arun_graph(session: AsyncSession, initial_state: GraphState) -> GraphState:
        initial_state.graph_id = StateGraphService.canonical_id(initial_state.graph_id)
        repo = AsyncCheckpointRepository(session)
        adapter = AsyncCheckpointerAdapter(repo)
        graph = StateGraphService.get_graph(initial_state.graph_id, checkpointer=adapter)
        return await graph.arun(initial_state)

    @staticmethod
    def astream_graph(session: AsyncSession, initial_state: GraphState):
        initial_state.graph_id = StateGraphService.canonical_id(initial_state.graph_id)
        repo = AsyncCheckpointRepository(session)
        adapter = AsyncCheckpointerAdapter(repo)
        graph = StateGraphService.get_graph(initial_state.graph_id, checkpointer=adapter)
        return graph.astream(initial_state)

    @staticmethod
    def load_latest_state(session: Session, run_id: str) -> Optional[GraphState]:
        repo = CheckpointRepository(session)
        return repo.load_latest_checkpoint(run_id)

    @staticmethod
    async def aload_latest_state(session: AsyncSession, run_id: str) -> Optional[GraphState]:
        repo = AsyncCheckpointRepository(session)
        return await repo.load_latest_checkpoint(run_id)

    @staticmethod
    def list_history(session: Session, run_id: str) -> List[Dict[str, Any]]:
        repo = CheckpointRepository(session)
        return repo.list_checkpoints(run_id)
