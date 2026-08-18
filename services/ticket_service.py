"""
Failure Ticket Service (services/ticket_service.py)
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.ticket_repo import AsyncTicketRepository, TicketRepository


class TicketService:
    @staticmethod
    def open_ticket(session: Session, run_id: str, graph_id: str, node_name: str, error: Exception, state_dict: Dict[str, Any]) -> str:
        repo = TicketRepository(session)
        return repo.open_ticket(run_id, graph_id, node_name, error, state_dict)

    @staticmethod
    async def aopen_ticket(session: AsyncSession, run_id: str, graph_id: str, node_name: str, error: Exception, state_dict: Dict[str, Any]) -> str:
        repo = AsyncTicketRepository(session)
        return await repo.open_ticket(run_id, graph_id, node_name, error, state_dict)

    @staticmethod
    def list_tickets(session: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
        repo = TicketRepository(session)
        return repo.list_tickets(status=status)

    @staticmethod
    async def alist_tickets(session: AsyncSession, status: Optional[str] = None) -> List[Dict[str, Any]]:
        repo = AsyncTicketRepository(session)
        return await repo.list_tickets(status=status)

    @staticmethod
    def resolve_ticket(session: Session, ticket_id: str, notes: str = "", resolved_by: str = "Admin") -> bool:
        repo = TicketRepository(session)
        return repo.resolve_ticket(ticket_id, notes, resolved_by)

    @staticmethod
    async def aresolve_ticket(session: AsyncSession, ticket_id: str, notes: str = "", resolved_by: str = "Admin") -> bool:
        repo = AsyncTicketRepository(session)
        return await repo.resolve_ticket(ticket_id, notes, resolved_by)
