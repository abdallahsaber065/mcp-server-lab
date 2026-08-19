"""
Durable State Graph Checkpointer (state_graph/checkpoint.py)
Built on SQLAlchemy 2.0 ORM CheckpointRepository for PostgreSQL & SQLite persistence.
Supports time-travel inspection, state diffing, and historical snapshot recovery.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.session import SessionLocal, init_sync_db
from db.models import GraphCheckpoint
from db.repositories.checkpoint_repo import CheckpointRepository
from state_graph.models import GraphState

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

