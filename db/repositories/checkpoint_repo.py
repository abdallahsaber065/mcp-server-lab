"""
Graph Checkpoint Repository (db/repositories/checkpoint_repo.py)
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import GraphCheckpoint
from db.repositories.base import BaseRepository, AsyncBaseRepository
from state_graph.models import GraphState


class CheckpointRepository(BaseRepository[GraphCheckpoint]):
    def __init__(self, session: Session):
        super().__init__(GraphCheckpoint, session)

    def save_checkpoint(self, state: GraphState) -> str:
        checkpoint_id = str(uuid.uuid4())
        checkpoint = GraphCheckpoint(
            checkpoint_id=checkpoint_id,
            run_id=state.run_id,
            step_number=state.step_number,
            node_name=state.current_node or "terminal",
            state_json=state.model_dump_json(),
            status=state.status
        )
        self.session.add(checkpoint)
        self.session.commit()
        return checkpoint_id

    def load_latest_checkpoint(self, run_id: str) -> Optional[GraphState]:
        stmt = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id)
            .order_by(GraphCheckpoint.step_number.desc(), GraphCheckpoint.created_at.desc())
            .limit(1)
        )
        row = self.session.scalars(stmt).first()
        if row:
            return GraphState.model_validate_json(row.state_json)
        return None

    def list_checkpoints(self, run_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id)
            .order_by(GraphCheckpoint.step_number.asc())
        )
        rows = self.session.scalars(stmt).all()
        return [
            {
                "checkpoint_id": r.checkpoint_id,
                "step": r.step_number,
                "node": r.node_name,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in rows
        ]


class AsyncCheckpointRepository(AsyncBaseRepository[GraphCheckpoint]):
    def __init__(self, session: AsyncSession):
        super().__init__(GraphCheckpoint, session)

    async def save_checkpoint(self, state: GraphState) -> str:
        checkpoint_id = str(uuid.uuid4())
        checkpoint = GraphCheckpoint(
            checkpoint_id=checkpoint_id,
            run_id=state.run_id,
            step_number=state.step_number,
            node_name=state.current_node or "terminal",
            state_json=state.model_dump_json(),
            status=state.status
        )
        self.session.add(checkpoint)
        await self.session.commit()
        return checkpoint_id

    async def load_latest_checkpoint(self, run_id: str) -> Optional[GraphState]:
        stmt = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id)
            .order_by(GraphCheckpoint.step_number.desc(), GraphCheckpoint.created_at.desc())
            .limit(1)
        )
        result = await self.session.scalars(stmt)
        row = result.first()
        if row:
            return GraphState.model_validate_json(row.state_json)
        return None
