"""
Human-in-the-Loop (HITL) Task Manager (state_graph/hitl.py)
Built on SQLAlchemy 2.0 ORM HITLRepository for PostgreSQL & SQLite persistence.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.repositories.hitl_repo import HITLRepository


class HITLManager:
    """Manages pending human approval tasks for State Graph executions."""

    def __init__(self, session: Optional[Session] = None):
        self._session_provided = session is not None
        self.session = session or SessionLocal()
        self.repo = HITLRepository(self.session)

    def create_task(self, run_id: str, graph_id: str, node_name: str, reason: str, payload: Dict[str, Any]) -> str:
        """Create a new pending HITL task."""
        return self.repo.create_task(run_id, graph_id, node_name, reason, payload)

    def list_pending_tasks(self) -> List[Dict[str, Any]]:
        """List all pending HITL tasks across all graphs."""
        return self.repo.list_pending_tasks()

    def resolve_task(self, task_id: str, decision: str, notes: str = "", decided_by: str = "Admin") -> bool:
        """Approve, modify, or reject a pending HITL task."""
        return self.repo.resolve_task(task_id, decision, notes, decided_by)

    def close(self):
        if not self._session_provided:
            self.session.close()
