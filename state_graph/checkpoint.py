"""
Durable State Graph Checkpointer (state_graph/checkpoint.py)
Built on SQLAlchemy 2.0 ORM CheckpointRepository for PostgreSQL & SQLite persistence.
Supports time-travel inspection, state diffing, and historical snapshot recovery.
Native LangGraph BaseCheckpointSaver adapter for official StateGraph persistence (v1.x).
"""
from typing import Optional, List, Dict, Any, Iterator, Sequence, Tuple
import json
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.session import SessionLocal, init_sync_db
from db.models import GraphCheckpoint
from db.repositories.checkpoint_repo import CheckpointRepository
from state_graph.models import GraphState
import logging
logger = logging.getLogger("state_graph.checkpoint")

try:
    from langgraph.checkpoint.base import (
        BaseCheckpointSaver,
        Checkpoint,
        CheckpointMetadata,
        CheckpointTuple,
        ChannelVersions,
    )
    from langchain_core.runnables import RunnableConfig
    _HAS_LANGGRAPH = True
except Exception:
    _HAS_LANGGRAPH = False
    BaseCheckpointSaver = object  # type: ignore
    Checkpoint = dict  # type: ignore
    CheckpointMetadata = dict  # type: ignore
    CheckpointTuple = Any  # type: ignore
    ChannelVersions = dict  # type: ignore
    RunnableConfig = dict  # type: ignore

class DurableCheckpointer:
    """Persists immutable state snapshots to the database for crash-and-resume recovery."""

    def __init__(self, session: Optional[Session] = None):
        self._session_provided = session is not None
        if not self._session_provided:
            init_sync_db()
        self.session = session or SessionLocal()
        self.repo = CheckpointRepository(self.session)

    def save_checkpoint(self, state: GraphState) -> str:
        """Save a new state snapshot."""
        return self.repo.save_checkpoint(state)

    def load_latest_checkpoint(self, run_id: str) -> Optional[GraphState]:
        """Load the most recent checkpoint for a run."""
        return self.repo.load_latest_checkpoint(run_id)

    def list_checkpoints(self, run_id: str) -> List[Dict[str, Any]]:
        """List all historical checkpoints for time-travel inspection."""
        return self.repo.list_checkpoints(run_id)

    def diff_checkpoints(self, run_id: str, step_a: int, step_b: int) -> Dict[str, Any]:
        """Compute state variable diffs and transition log delta between two historical step checkpoints."""
        cps = self.list_checkpoints(run_id)
        cp_a = next((c for c in cps if c["step"] == step_a), None)
        cp_b = next((c for c in cps if c["step"] == step_b), None)
        if not cp_a or not cp_b:
            return {"error": "One or both specified step checkpoints were not found."}

        stmt_a = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id, GraphCheckpoint.step_number == step_a)
            .limit(1)
        )
        stmt_b = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id, GraphCheckpoint.step_number == step_b)
            .limit(1)
        )
        row_a = self.session.scalars(stmt_a).first()
        row_b = self.session.scalars(stmt_b).first()

        if not row_a or not row_b:
            return {"error": "Could not retrieve full checkpoint snapshots."}

        state_a = GraphState.model_validate_json(row_a.state_json)
        state_b = GraphState.model_validate_json(row_b.state_json)

        added = {k: v for k, v in state_b.variables.items() if k not in state_a.variables}
        modified = {
            k: {"from": state_a.variables[k], "to": state_b.variables[k]}
            for k in state_b.variables
            if k in state_a.variables and state_a.variables[k] != state_b.variables[k]
        }
        removed = [k for k in state_a.variables if k not in state_b.variables]

        return {
            "run_id": run_id,
            "from_step": step_a,
            "to_step": step_b,
            "status_from": state_a.status,
            "status_to": state_b.status,
            "node_from": state_a.current_node,
            "node_to": state_b.current_node,
            "added_variables": added,
            "modified_variables": modified,
            "removed_variables": removed,
        }

    def rollback_to_checkpoint(self, run_id: str, step_number: int) -> Optional[GraphState]:
        """Rollback a state graph run to a target historical step checkpoint snapshot."""
        stmt = (
            select(GraphCheckpoint)
            .where(GraphCheckpoint.run_id == run_id, GraphCheckpoint.step_number == step_number)
            .order_by(GraphCheckpoint.created_at.desc())
            .limit(1)
        )
        row = self.session.scalars(stmt).first()
        if not row:
            return None

        restored = GraphState.model_validate_json(row.state_json)
        latest = self.load_latest_checkpoint(run_id)
        if latest:
            restored.step_number = latest.step_number + 1
        restored.history.append({
            "step": restored.step_number,
            "node": restored.current_node,
            "status": "ROLLBACK",
            "message": f"Rolled back state machine from step {latest.step_number if latest else 0} to historical step {step_number}."
        })
        self.save_checkpoint(restored)
        return restored

    def close(self):
        if not self._session_provided:
            self.session.close()


try:
    from langgraph.checkpoint.memory import MemorySaver
except Exception:
    MemorySaver = BaseCheckpointSaver  # type: ignore


class SQLAlchemyLangGraphCheckpointer(MemorySaver):
    """
    Durable LangGraph checkpointer backed by in-memory channel storage + DB synchronization.
    Supports native LangGraph 1.x StateSnapshot, tasks, interrupts, and time-travel rollback.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(serde=None)
        self._session_provided = session is not None
        if not self._session_provided:
            init_sync_db()
        self.session = session or SessionLocal()

    def get_tuple(self, config):  # type: ignore[override]
        # Try in-memory first
        tup = super().get_tuple(config)
        if tup is not None:
            return tup
        # Fallback to database for process crash recovery
        thread_id = config.get("configurable", {}).get("thread_id", "")
        if not thread_id:
            return None
        cid = config.get("configurable", {}).get("checkpoint_id")
        try:
            with SessionLocal() as s:
                q = s.query(GraphCheckpoint).filter(GraphCheckpoint.run_id == thread_id)
                if cid:
                    q = q.filter(GraphCheckpoint.checkpoint_id == cid)
                row = q.order_by(GraphCheckpoint.step_number.desc()).first()
                if row and row.state_json:
                    data = json.loads(row.state_json)
                    checkpoint = data.get("checkpoint") or {}
                    metadata = data.get("metadata") or {}
                    parent_config = data.get("parent_config")
                    from langgraph.checkpoint.base import CheckpointTuple
                    return CheckpointTuple(
                        config={"configurable": {"thread_id": thread_id, "checkpoint_ns": config.get("configurable", {}).get("checkpoint_ns", ""), "checkpoint_id": row.checkpoint_id}},
                        checkpoint=checkpoint,  # type: ignore
                        metadata=metadata,  # type: ignore
                        parent_config=parent_config,
                        pending_writes=[],
                    )
        except Exception as e:
            logger.warning("SQL get_tuple recovery fallback: %s", e)
        return None

    def put(self, config, checkpoint, metadata, new_versions):  # type: ignore[override]
        res = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id", "")
        checkpoint_id = checkpoint.get("id") or str(uuid.uuid4())
        step = int(metadata.get("step", 0)) if isinstance(metadata, dict) else 0
        node_name = str(metadata.get("source", "node") or metadata.get("node", "node")) if isinstance(metadata, dict) else "node"
        logger.info("checkpoint put thread=%s step=%s node=%s id=%s", thread_id, step, node_name, checkpoint_id[:8])
        try:
            with SessionLocal() as s:
                rec = GraphCheckpoint(
                    checkpoint_id=checkpoint_id,
                    run_id=thread_id,
                    step_number=step,
                    node_name=node_name,
                    state_json=json.dumps({"checkpoint": checkpoint, "metadata": metadata, "parent_config": config}, default=str),
                    status=str(metadata.get("writes", {}).get("status", "RUNNING") if isinstance(metadata, dict) else "RUNNING"),
                )
                s.merge(rec)
                s.commit()
        except Exception as e:
            logger.warning("SQL checkpoint persist fallback: %s", e)
        return res



