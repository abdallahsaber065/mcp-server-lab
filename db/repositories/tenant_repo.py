"""
Tenant & Lease Repository (db/repositories/tenant_repo.py)
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import Lease, Property, Tenant, Unit
from db.repositories.base import AsyncBaseRepository, BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, session: Session):
        super().__init__(Tenant, session)

    def get_by_email(self, email: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.email == email)
        return self.session.scalars(stmt).first()

    def get_lease_details(self, email: str) -> Dict[str, Any]:
        """Fetch active lease details for a tenant by email."""
        stmt = (
            select(Tenant, Lease, Unit, Property)
            .join(Lease, Tenant.tenant_id == Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Tenant.email == email)
        )
        result = self.session.execute(stmt).first()
        if not result:
            return {"found": False, "message": f"No lease records found for email '{email}'."}

        tenant, lease, unit, prop = result
        return {
            "found": True,
            "tenant_id": tenant.tenant_id,
            "tenant_name": tenant.full_name,
            "email": tenant.email,
            "property_name": prop.name,
            "unit_number": unit.unit_number,
            "monthly_rent": lease.monthly_rent,
            "start_date": lease.start_date,
            "end_date": lease.end_date,
            "is_active": bool(lease.is_active),
            "requires_executive_signoff": bool(lease.requires_executive_signoff)
        }

    def modify_lease(self, lease_id: int, new_monthly_rent: float, duration_months: int) -> Optional[Lease]:
        lease = self.session.get(Lease, lease_id)
        if lease:
            lease.monthly_rent = new_monthly_rent
            self.session.commit()
            self.session.refresh(lease)
        return lease


class AsyncTenantRepository(AsyncBaseRepository[Tenant]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def get_by_email(self, email: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.email == email)
        result = await self.session.scalars(stmt)
        return result.first()

    async def get_lease_details(self, email: str) -> Dict[str, Any]:
        stmt = (
            select(Tenant, Lease, Unit, Property)
            .join(Lease, Tenant.tenant_id == Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Tenant.email == email)
        )
        result = (await self.session.execute(stmt)).first()
        if not result:
            return {"found": False, "message": f"No lease records found for email '{email}'."}

        tenant, lease, unit, prop = result
        return {
            "found": True,
            "tenant_id": tenant.tenant_id,
            "tenant_name": tenant.full_name,
            "email": tenant.email,
            "property_name": prop.name,
            "unit_number": unit.unit_number,
            "monthly_rent": lease.monthly_rent,
            "start_date": lease.start_date,
            "end_date": lease.end_date,
            "is_active": bool(lease.is_active),
            "requires_executive_signoff": bool(lease.requires_executive_signoff)
        }
