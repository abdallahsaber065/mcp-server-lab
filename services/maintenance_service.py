"""
Maintenance Service (services/maintenance_service.py)
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.maintenance_repo import AsyncMaintenanceRepository, MaintenanceRepository


class MaintenanceService:
    @staticmethod
    def submit_maintenance_ticket(
        session: Session,
        unit_id: int,
        tenant_id: int,
        issue_type: str,
        priority: str,
        description: str,
        estimated_cost: float = 0.0
    ) -> Dict[str, Any]:
        repo = MaintenanceRepository(session)
        ticket = repo.submit_request(
            unit_id=unit_id,
            tenant_id=tenant_id,
            issue_type=issue_type,
            priority=priority,
            description=description,
            estimated_cost=estimated_cost
        )
        return {
            "ticket_id": ticket.request_id,
            "unit_id": ticket.unit_id,
            "status": ticket.status,
            "priority": ticket.priority,
            "estimated_cost": ticket.estimated_cost,
            "submitted_at": ticket.submitted_at.isoformat() if ticket.submitted_at else ""
        }

    @staticmethod
    async def asubmit_maintenance_ticket(
        session: AsyncSession,
        unit_id: int,
        tenant_id: int,
        issue_type: str,
        priority: str,
        description: str,
        estimated_cost: float = 0.0
    ) -> Dict[str, Any]:
        repo = AsyncMaintenanceRepository(session)
        ticket = await repo.submit_request(
            unit_id=unit_id,
            tenant_id=tenant_id,
            issue_type=issue_type,
            priority=priority,
            description=description,
            estimated_cost=estimated_cost
        )
        return {
            "ticket_id": ticket.request_id,
            "unit_id": ticket.unit_id,
            "status": ticket.status,
            "priority": ticket.priority,
            "estimated_cost": ticket.estimated_cost,
            "submitted_at": ticket.submitted_at.isoformat() if ticket.submitted_at else ""
        }
