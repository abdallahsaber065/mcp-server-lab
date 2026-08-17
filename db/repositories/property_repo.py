"""
Property & Unit Repository (db/repositories/property_repo.py)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Property, Unit
from db.repositories.base import BaseRepository, AsyncBaseRepository


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
        if city:
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
                "unit_number": unit.unit_number,
                "monthly_rent": unit.monthly_rent,
                "bedrooms": unit.bedrooms,
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
        if city:
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
                "unit_number": unit.unit_number,
                "monthly_rent": unit.monthly_rent,
                "bedrooms": unit.bedrooms,
                "is_high_value": unit.is_high_value,
                "status": unit.status
            })
        return output
