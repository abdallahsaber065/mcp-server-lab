"""
Maintenance Router (web/routers/maintenance.py)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MaintenanceRequest, Property, Tenant, Unit
from db.repositories.maintenance_repo import AsyncMaintenanceRepository
from db.session import get_async_db
from services.maintenance_service import MaintenanceService
from web.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


class CreateMaintenanceRequest(BaseModel):
    unit_id: int
    issue_type: str = Field(..., description="plumbing, electrical, hvac, structural, general")
    priority: str = Field("medium", description="emergency, high, medium, low")
    description: str = Field(..., min_length=5, description="Detailed repair description")
    estimated_cost: Optional[float] = 0.0


@router.get("")
async def list_maintenance_requests(
    current_user: Tenant = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List maintenance requests (Tenants see own requests; Managers/Admins see all)."""
    stmt = (
        select(MaintenanceRequest, Unit, Property, Tenant)
        .join(Unit, MaintenanceRequest.unit_id == Unit.unit_id)
        .join(Property, Unit.property_id == Property.property_id)
        .join(Tenant, MaintenanceRequest.tenant_id == Tenant.tenant_id)
    )
    if current_user.role == "tenant":
        stmt = stmt.where(MaintenanceRequest.tenant_id == current_user.tenant_id)

    stmt = stmt.order_by(MaintenanceRequest.submitted_at.desc())
    rows = (await db.execute(stmt)).all()

    requests = []
    for req, unit, prop, tenant in rows:
        requests.append({
            "request_id": req.request_id,
            "unit_id": unit.unit_id,
            "unit_number": unit.unit_number,
            "property_name": prop.name,
            "tenant_name": tenant.full_name,
            "issue_type": req.issue_type,
            "priority": req.priority,
            "description": req.description,
            "status": req.status,
            "estimated_cost": req.estimated_cost,
            "contractor_name": req.contractor_name,
            "submitted_at": req.submitted_at.isoformat() if req.submitted_at else ""
        })
    return {"status": "success", "requests": requests, "count": len(requests)}


@router.post("")
async def submit_maintenance(
    req: CreateMaintenanceRequest,
    current_user: Tenant = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """File a new maintenance repair request."""
    ticket = await MaintenanceService.asubmit_maintenance_ticket(
        session=db,
        unit_id=req.unit_id,
        tenant_id=current_user.tenant_id,
        issue_type=req.issue_type,
        priority=req.priority,
        description=req.description,
        estimated_cost=req.estimated_cost or 0.0
    )
    return {"status": "success", "ticket": ticket}
