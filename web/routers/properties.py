"""
Properties & Units Router (web/routers/properties.py)
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_async_db
from db.models import Property, Unit
from db.repositories.property_repo import AsyncPropertyRepository
from services.cache_service import cache_service

router = APIRouter(prefix="/api/properties", tags=["Properties"])


@router.get("")
async def list_properties(db: AsyncSession = Depends(get_async_db)):
    """List all real estate properties with aggregate unit stats."""
    cached = await cache_service.get_json("catalog:properties:all")
    if cached:
        return {"status": "success", "properties": cached, "cached": True}

    stmt = select(Property)
    rows = (await db.scalars(stmt)).all()
    properties = []
    for p in rows:
        properties.append({
            "property_id": p.property_id,
            "name": p.name,
            "address": p.address,
            "city": p.city,
            "property_type": p.property_type,
            "total_units": p.total_units,
            "occupancy_rate": p.occupancy_rate
        })

    await cache_service.set_json("catalog:properties:all", properties, expire_seconds=60)
    return {"status": "success", "properties": properties, "cached": False}


@router.get("/units/available")
async def list_available_units(
    property_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    max_rent: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """Query available units matching search criteria with Redis caching."""
    cache_key = f"catalog:units:available:{property_id}:{city}:{max_rent}"
    cached = await cache_service.get_json(cache_key)
    if cached:
        return {"status": "success", "units": cached, "count": len(cached), "cached": True}

    repo = AsyncPropertyRepository(db)
    units = await repo.query_available_units(property_id=property_id, city=city, max_rent=max_rent)

    await cache_service.set_json(cache_key, units, expire_seconds=60)
    return {"status": "success", "units": units, "count": len(units), "cached": False}
