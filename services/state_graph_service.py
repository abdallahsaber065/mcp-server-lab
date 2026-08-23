"""
State Graph Service (services/state_graph_service.py)
Coordinates State Graph execution, checkpoint persistence, webhook resumes, and HITL decisions.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.checkpoint_repo import AsyncCheckpointRepository, CheckpointRepository
from state_graph.engine import StateGraph
from state_graph.graphs.lease_flow import build_lease_flow_graph
from state_graph.models import GraphState


class CheckpointerAdapter:
    """Adapts CheckpointRepository to the StateGraph checkpointer interface."""
    def __init__(self, repo: CheckpointRepository):
        self.repo = repo

    def save_checkpoint(self, state: GraphState) -> str:
        return self.repo.save_checkpoint(state)


class AsyncCheckpointerAdapter:
    """Adapts AsyncCheckpointRepository to the StateGraph async checkpointer interface."""
    def __init__(self, repo: AsyncCheckpointRepository):
        self.repo = repo

    async def asave_checkpoint(self, state: GraphState) -> str:
        return await self.repo.save_checkpoint(state)


class StateGraphService:
    @staticmethod
    def get_graph(graph_id: str, checkpointer=None) -> StateGraph:
        if graph_id == "commercial_lease_flow":
            return build_lease_flow_graph(checkpointer=checkpointer)
        raise ValueError(f"Unknown graph_id '{graph_id}'")

    @staticmethod
    def run_graph(session: Session, initial_state: GraphState) -> GraphState:
        repo = CheckpointRepository(session)
        adapter = CheckpointerAdapter(repo)
        graph = StateGraphService.get_graph(initial_state.graph_id, checkpointer=adapter)
        return graph.run(initial_state)

    @staticmethod
    async def arun_graph(session: AsyncSession, initial_state: GraphState) -> GraphState:
        repo = AsyncCheckpointRepository(session)
        adapter = AsyncCheckpointerAdapter(repo)
        graph = StateGraphService.get_graph(initial_state.graph_id, checkpointer=adapter)
        return await graph.arun(initial_state)

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
