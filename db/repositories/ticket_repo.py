"""
Failure Ticket Repository (db/repositories/ticket_repo.py)
"""

import json
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import GraphFailureTicket
from db.repositories.base import AsyncBaseRepository, BaseRepository


class TicketRepository(BaseRepository[GraphFailureTicket]):
    def __init__(self, session: Session):
        super().__init__(GraphFailureTicket, session)

    def open_ticket(
        self,
        run_id: str,
        graph_id: str,
        node_name: str,
        error: Exception,
        state_dict: Dict[str, Any]
    ) -> str:
        ticket_id = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        tb_str = traceback.format_exc()
        ticket = GraphFailureTicket(
            ticket_id=ticket_id,
            run_id=run_id,
            graph_id=graph_id,
            node_name=node_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=tb_str,
            persisted_state_json=json.dumps(state_dict),
            ticket_status="open"
        )
        self.session.add(ticket)
        self.session.commit()
        return ticket_id

    def list_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = select(GraphFailureTicket)
        if status:
            stmt = stmt.where(GraphFailureTicket.ticket_status == status)
        stmt = stmt.order_by(GraphFailureTicket.created_at.desc())
        rows = self.session.scalars(stmt).all()
        return [
            {
                "ticket_id": r.ticket_id,
                "run_id": r.run_id,
                "graph_id": r.graph_id,
                "node": r.node_name,
                "error_type": r.error_type,
                "message": r.error_message,
                "status": r.ticket_status,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in rows
        ]

    def resolve_ticket(self, ticket_id: str, notes: str = "", resolved_by: str = "Admin") -> bool:
        ticket = self.session.get(GraphFailureTicket, ticket_id)
        if ticket:
            ticket.ticket_status = "resolved"
            ticket.resolution_notes = notes
            ticket.resolved_by = resolved_by
            ticket.resolved_at = datetime.utcnow()
            self.session.commit()
            return True
        return False


class AsyncTicketRepository(AsyncBaseRepository[GraphFailureTicket]):
    def __init__(self, session: AsyncSession):
        super().__init__(GraphFailureTicket, session)

    async def open_ticket(
        self,
        run_id: str,
        graph_id: str,
        node_name: str,
        error: Exception,
        state_dict: Dict[str, Any]
    ) -> str:
        ticket_id = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        tb_str = traceback.format_exc()
        ticket = GraphFailureTicket(
            ticket_id=ticket_id,
            run_id=run_id,
            graph_id=graph_id,
            node_name=node_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=tb_str,
            persisted_state_json=json.dumps(state_dict),
            ticket_status="open"
        )
        self.session.add(ticket)
        await self.session.commit()
        return ticket_id

    async def list_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = select(GraphFailureTicket)
        if status:
            stmt = stmt.where(GraphFailureTicket.ticket_status == status)
        stmt = stmt.order_by(GraphFailureTicket.created_at.desc())
        result = await self.session.scalars(stmt)
        rows = result.all()
        return [
            {
                "ticket_id": r.ticket_id,
                "run_id": r.run_id,
                "graph_id": r.graph_id,
                "node": r.node_name,
                "error_type": r.error_type,
                "message": r.error_message,
                "status": r.ticket_status,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in rows
        ]

    async def resolve_ticket(self, ticket_id: str, notes: str = "", resolved_by: str = "Admin") -> bool:
        ticket = await self.session.get(GraphFailureTicket, ticket_id)
        if ticket:
            ticket.ticket_status = "resolved"
            ticket.resolution_notes = notes
            ticket.resolved_by = resolved_by
            ticket.resolved_at = datetime.utcnow()
            await self.session.commit()
            return True
        return False
