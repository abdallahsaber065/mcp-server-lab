"""
Tenant & Lease Repository (db/repositories/tenant_repo.py)
Supports multi-lease lookups, lease modifications, renewal requests, and termination.
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

    def get_all_leases(self, email_or_id: Any) -> List[Dict[str, Any]]:
        """Fetch all active and historical leases for a tenant by email or ID."""
        stmt = (
            select(Tenant, Lease, Unit, Property)
            .join(Lease, Tenant.tenant_id == Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
        )
        if isinstance(email_or_id, int) or (isinstance(email_or_id, str) and email_or_id.isdigit()):
            stmt = stmt.where(Tenant.tenant_id == int(email_or_id))
        else:
            stmt = stmt.where(Tenant.email == str(email_or_id))

        rows = self.session.execute(stmt).all()
        results = []
        for tenant, lease, unit, prop in rows:
            results.append({
                "lease_id": lease.lease_id,
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.full_name,
                "email": tenant.email,
                "property_id": prop.property_id,
                "property_name": prop.name,
                "unit_id": unit.unit_id,
                "unit_number": unit.unit_number,
                "monthly_rent": lease.monthly_rent,
                "deposit_amount": lease.deposit_amount,
                "lease_type": getattr(lease, "lease_type", "residential"),
                "status": getattr(lease, "status", "active"),
                "start_date": lease.start_date,
                "end_date": lease.end_date,
                "payment_status": getattr(lease, "payment_status", "current"),
                "renewal_status": getattr(lease, "renewal_status", "none"),
                "is_active": bool(lease.is_active),
                "requires_executive_signoff": bool(lease.requires_executive_signoff),
                "notes": lease.notes
            })
        return results

    def get_lease_details(self, email: str) -> Dict[str, Any]:
        """Fetch primary active lease details for a tenant by email (backward compatible)."""
        leases = self.get_all_leases(email)
        if not leases:
            return {"found": False, "message": f"No lease records found for email '{email}'."}

        active_leases = [l for l in leases if l["is_active"]]
        primary = active_leases[0] if active_leases else leases[0]
        return {
            "found": True,
            **primary,
            "all_leases": leases,
            "total_leases_count": len(leases),
            "active_leases_count": len(active_leases)
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

    async def get_all_leases(self, email_or_id: Any) -> List[Dict[str, Any]]:
        """Fetch all active and historical leases for a tenant by email or ID."""
        stmt = (
            select(Tenant, Lease, Unit, Property)
            .join(Lease, Tenant.tenant_id == Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
        )
        if isinstance(email_or_id, int) or (isinstance(email_or_id, str) and email_or_id.isdigit()):
            stmt = stmt.where(Tenant.tenant_id == int(email_or_id))
        else:
            stmt = stmt.where(Tenant.email == str(email_or_id))

        rows = (await self.session.execute(stmt)).all()
        results = []
        for tenant, lease, unit, prop in rows:
            results.append({
                "lease_id": lease.lease_id,
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.full_name,
                "email": tenant.email,
                "property_id": prop.property_id,
                "property_name": prop.name,
                "unit_id": unit.unit_id,
                "unit_number": unit.unit_number,
                "monthly_rent": lease.monthly_rent,
                "deposit_amount": lease.deposit_amount,
                "lease_type": getattr(lease, "lease_type", "residential"),
                "status": getattr(lease, "status", "active"),
                "start_date": lease.start_date,
                "end_date": lease.end_date,
                "payment_status": getattr(lease, "payment_status", "current"),
                "renewal_status": getattr(lease, "renewal_status", "none"),
                "is_active": bool(lease.is_active),
                "requires_executive_signoff": bool(lease.requires_executive_signoff),
                "notes": lease.notes
            })
        return results

    async def get_lease_details(self, email: str) -> Dict[str, Any]:
        leases = await self.get_all_leases(email)
        if not leases:
            return {"found": False, "message": f"No lease records found for email '{email}'."}

        active_leases = [l for l in leases if l["is_active"]]
        primary = active_leases[0] if active_leases else leases[0]
        return {
            "found": True,
            **primary,
            "all_leases": leases,
            "total_leases_count": len(leases),
            "active_leases_count": len(active_leases)
        }
