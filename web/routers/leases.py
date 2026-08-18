"""
Leases Router (web/routers/leases.py)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lease, Property, Tenant, Unit
from db.repositories.tenant_repo import AsyncTenantRepository
from db.session import get_async_db
from services.lease_service import LeaseService
from web.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/leases", tags=["Leases"])


class DiscountEvaluationRequest(BaseModel):
    base_rent: float
    proposed_rent: float


@router.get("/me")
async def get_my_lease(current_user: Tenant = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """Retrieve active lease details for the currently logged-in tenant."""
    repo = AsyncTenantRepository(db)
    details = await repo.get_lease_details(current_user.email)
    if not details.get("found"):
        raise HTTPException(status_code=404, detail="No active lease found for your account.")
    return {"status": "success", "lease": details}


@router.get("")
async def list_all_leases(
    current_user: Tenant = Depends(require_roles(["property_manager", "executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """List all leases across properties (restricted to Managers and Admins)."""
    stmt = (
        select(Lease, Tenant, Unit, Property)
        .join(Tenant, Lease.tenant_id == Tenant.tenant_id)
        .join(Unit, Lease.unit_id == Unit.unit_id)
        .join(Property, Unit.property_id == Property.property_id)
    )
    rows = (await db.execute(stmt)).all()
    results = []
    for lease, tenant, unit, prop in rows:
        results.append({
            "lease_id": lease.lease_id,
            "tenant_name": tenant.full_name,
            "tenant_email": tenant.email,
            "property_name": prop.name,
            "unit_number": unit.unit_number,
            "monthly_rent": lease.monthly_rent,
            "start_date": lease.start_date,
            "end_date": lease.end_date,
            "payment_status": lease.payment_status,
            "is_active": lease.is_active,
            "requires_executive_signoff": lease.requires_executive_signoff,
            "notes": lease.notes
        })
    return {"status": "success", "leases": results, "count": len(results)}


@router.post("/calculate-discount")
async def evaluate_lease_discount(req: DiscountEvaluationRequest):
    """Audit proposed rental discount against Cornerstone Master Policy."""
    audit = LeaseService.evaluate_discount_policy(req.base_rent, req.proposed_rent)
    return {"status": "success", "audit": audit}
