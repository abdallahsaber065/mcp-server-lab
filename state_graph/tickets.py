"""
Graph Failure Ticketing System (state_graph/tickets.py)
Built on SQLAlchemy 2.0 ORM TicketRepository for PostgreSQL & SQLite persistence.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.repositories.ticket_repo import TicketRepository


class TicketSystem:
    """Catches unhandled node exceptions and persists incident tickets with full execution traces."""

    def __init__(self, session: Optional[Session] = None):
        self._session_provided = session is not None
        self.session = session or SessionLocal()
        self.repo = TicketRepository(self.session)

    def open_ticket(self, run_id: str, graph_id: str, node_name: str, error: Exception, state_dict: Dict[str, Any]) -> str:
        """Open an incident ticket with stack trace and frozen state snapshot."""
        return self.repo.open_ticket(run_id, graph_id, node_name, error, state_dict)

    def list_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List incident tickets filtered by status."""
        return self.repo.list_tickets(status)

    def resolve_ticket(self, ticket_id: str, notes: str = "", resolved_by: str = "Admin") -> bool:
        """Mark an incident ticket as resolved with resolution notes."""
        return self.repo.resolve_ticket(ticket_id, notes, resolved_by)

    def close(self):
        if not self._session_provided:
            self.session.close()
