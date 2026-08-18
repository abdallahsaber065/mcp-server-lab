"""
State Graph Router (web/routers/state_graph.py)
"""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GraphCheckpoint
from db.repositories.checkpoint_repo import AsyncCheckpointRepository
from db.session import get_async_db
from services.state_graph_service import StateGraphService
from state_graph.models import GraphState
from web.deps import require_roles

router = APIRouter(prefix="/api/state-graph", tags=["State Graph"])


class StateGraphRunRequest(BaseModel):
    graph_id: str
    run_id: Optional[str] = None
    variables: Dict[str, Any] = {}


@router.post("/run")
async def run_state_graph(
    req: StateGraphRunRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Start or advance a state graph run asynchronously."""
    run_id = req.run_id or f"run-{uuid.uuid4().hex[:8]}"
    initial_state = GraphState(
        run_id=run_id,
        graph_id=req.graph_id,
        current_node="",
        variables=req.variables
    )
    res_state = await StateGraphService.arun_graph(db, initial_state)
    return {
        "status": "success",
        "run_id": res_state.run_id,
        "graph_status": res_state.status,
        "current_node": res_state.current_node,
        "step_number": res_state.step_number,
        "pending_hitl": res_state.pending_hitl,
        "last_error": res_state.last_error,
        "variables": res_state.variables,
        "history": res_state.history
    }


@router.get("/{run_id}")
async def get_state_graph_status(run_id: str, db: AsyncSession = Depends(get_async_db)):
    """Retrieve the latest checkpoint state for a run."""
    state = await StateGraphService.aload_latest_state(db, run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return {"status": "success", "state": state.model_dump()}


@router.get("/{run_id}/history")
async def get_state_graph_history(run_id: str, db: AsyncSession = Depends(get_async_db)):
    """List historical checkpoint steps for time-travel inspection."""
    repo = AsyncCheckpointRepository(db)
    stmt = select(GraphCheckpoint).where(GraphCheckpoint.run_id == run_id).order_by(GraphCheckpoint.step_number.asc())
    rows = (await db.scalars(stmt)).all()
    checkpoints = [
        {"checkpoint_id": r.checkpoint_id, "step": r.step_number, "node": r.node_name, "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else ""}
        for r in rows
    ]
    return {"status": "success", "run_id": run_id, "checkpoints": checkpoints}
