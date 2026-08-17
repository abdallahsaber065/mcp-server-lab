"""
Maintenance Request Repository (db/repositories/maintenance_repo.py)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import MaintenanceRequest, Unit
from db.repositories.base import BaseRepository, AsyncBaseRepository


class MaintenanceRepository(BaseRepository[MaintenanceRequest]):
    def __init__(self, session: Session):
        super().__init__(MaintenanceRequest, session)

    def submit_request(
        self,
        unit_id: int,
        tenant_id: int,
        issue_type: str,
        priority: str,
        description: str,
        estimated_cost: float = 0.0
    ) -> MaintenanceRequest:
        req = MaintenanceRequest(
            unit_id=unit_id,
            tenant_id=tenant_id,
            issue_type=issue_type,
            priority=priority,
            description=description,
            estimated_cost=estimated_cost,
            status="open",
            submitted_at=datetime.utcnow()
        )
        self.session.add(req)
        self.session.commit()
        self.session.refresh(req)
        return req

    def list_by_unit(self, unit_id: int) -> List[MaintenanceRequest]:
        stmt = select(MaintenanceRequest).where(MaintenanceRequest.unit_id == unit_id)
        return list(self.session.scalars(stmt).all())


class AsyncMaintenanceRepository(AsyncBaseRepository[MaintenanceRequest]):
    def __init__(self, session: AsyncSession):
        super().__init__(MaintenanceRequest, session)

    async def submit_request(
        self,
        unit_id: int,
        tenant_id: int,
        issue_type: str,
        priority: str,
        description: str,
        estimated_cost: float = 0.0
    ) -> MaintenanceRequest:
        req = MaintenanceRequest(
            unit_id=unit_id,
            tenant_id=tenant_id,
            issue_type=issue_type,
            priority=priority,
            description=description,
            estimated_cost=estimated_cost,
            status="open",
            submitted_at=datetime.utcnow()
        )
        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)
        return req
