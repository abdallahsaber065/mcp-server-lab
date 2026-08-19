"""
Durable State Graph Checkpointer (state_graph/checkpoint.py)
Built on SQLAlchemy 2.0 ORM CheckpointRepository for PostgreSQL & SQLite persistence.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from db.session import SessionLocal, init_sync_db
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

    def close(self):
        if not self._session_provided:
            self.session.close()
