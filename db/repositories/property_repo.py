"""
Property & Unit Repository (db/repositories/property_repo.py)
Provides sync and async repository operations for luxury properties, units, and featured listings.
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from db.models import Property, Unit
from db.repositories.base import AsyncBaseRepository, BaseRepository


def _parse_json_field(val: Optional[str]) -> List[Any]:
    if not val:
        return []
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        return [val]


class PropertyRepository(BaseRepository[Property]):
    def __init__(self, session: Session):
        super().__init__(Property, session)

    def query_available_units(
        self,
        property_id: Optional[int] = None,
        city: Optional[str] = None,
        max_rent: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Query available units matching property/city/budget constraints."""
        stmt = select(Unit, Property).join(Property, Unit.property_id == Property.property_id)

        filters = [Unit.status == "available"]
        if property_id is not None:
            filters.append(Unit.property_id == property_id)
        if city and city.lower() != "all":
            filters.append(Property.city.ilike(f"%{city}%"))
        if max_rent is not None:
            filters.append(Unit.monthly_rent <= max_rent)

        stmt = stmt.where(and_(*filters))
        results = self.session.execute(stmt).all()

        output = []
        for unit, prop in results:
            output.append({
                "unit_id": unit.unit_id,
                "property_id": prop.property_id,
                "property_name": prop.name,
                "city": prop.city,
                "neighborhood": prop.neighborhood or prop.city,
                "unit_number": unit.unit_number,
                "title": unit.title or f"{prop.name} - Unit {unit.unit_number}",
                "description": unit.description or prop.description or "",
                "image_url": unit.image_url or prop.image_url or "/images/properties/nile_tower_ext.jpg",
                "images": _parse_json_field(unit.images) or _parse_json_field(prop.images),
                "monthly_rent": float(unit.monthly_rent),
                "bedrooms": unit.bedrooms,
                "bathrooms": float(unit.bathrooms),
                "square_feet": float(unit.square_feet or 0.0),
                "floor_number": unit.floor_number or 1,
                "features": _parse_json_field(unit.features),
                "amenities": _parse_json_field(prop.amenities),
                "pet_policy": unit.pet_policy or "Allowed",
                "virtual_tour_url": unit.virtual_tour_url or "",
                "is_high_value": unit.is_high_value,
                "status": unit.status
            })
        return output


class AsyncPropertyRepository(AsyncBaseRepository[Property]):
    def __init__(self, session: AsyncSession):
        super().__init__(Property, session)

    async def query_available_units(
        self,
        property_id: Optional[int] = None,
        city: Optional[str] = None,
        max_rent: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(Unit, Property).join(Property, Unit.property_id == Property.property_id)

        filters = [Unit.status == "available"]
        if property_id is not None:
            filters.append(Unit.property_id == property_id)
        if city and city.lower() != "all":
            filters.append(Property.city.ilike(f"%{city}%"))
        if max_rent is not None:
            filters.append(Unit.monthly_rent <= max_rent)

        stmt = stmt.where(and_(*filters))
        results = (await self.session.execute(stmt)).all()

        output = []
        for unit, prop in results:
            output.append({
                "unit_id": unit.unit_id,
                "property_id": prop.property_id,
                "property_name": prop.name,
                "city": prop.city,
                "neighborhood": prop.neighborhood or prop.city,
                "unit_number": unit.unit_number,
                "title": unit.title or f"{prop.name} - Unit {unit.unit_number}",
                "description": unit.description or prop.description or "",
                "image_url": unit.image_url or prop.image_url or "/images/properties/nile_tower_ext.jpg",
                "images": _parse_json_field(unit.images) or _parse_json_field(prop.images),
                "monthly_rent": float(unit.monthly_rent),
                "bedrooms": unit.bedrooms,
                "bathrooms": float(unit.bathrooms),
                "square_feet": float(unit.square_feet or 0.0),
                "floor_number": unit.floor_number or 1,
                "features": _parse_json_field(unit.features),
                "amenities": _parse_json_field(prop.amenities),
                "pet_policy": unit.pet_policy or "Allowed",
                "virtual_tour_url": unit.virtual_tour_url or "",
                "is_high_value": unit.is_high_value,
                "status": unit.status
            })
        return output

    async def get_featured_properties(self) -> List[Dict[str, Any]]:
        stmt = select(Property).options(selectinload(Property.units)).where(Property.is_featured.is_(True))
        props = (await self.session.scalars(stmt)).all()
        if not props:
            stmt = select(Property).options(selectinload(Property.units)).limit(6)
            props = (await self.session.scalars(stmt)).all()

        output = []
        for p in props:
            output.append({
                "property_id": p.property_id,
                "name": p.name,
                "address": p.address,
                "city": p.city,
                "neighborhood": p.neighborhood or p.city,
                "property_type": p.property_type,
                "description": p.description or "",
                "image_url": p.image_url or "/images/properties/nile_tower_ext.jpg",
                "images": _parse_json_field(p.images),
                "amenities": _parse_json_field(p.amenities),
                "year_built": p.year_built or 2024,
                "total_units": len(p.units) if p.units else p.total_units,
                "available_units": sum(1 for u in p.units if u.status == "available"),
                "starting_rent": min((u.monthly_rent for u in p.units), default=15000.0)
            })
        return output
