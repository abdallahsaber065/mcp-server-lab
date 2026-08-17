"""
Property Service (services/property_service.py)
Encapsulates property and unit domain operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.property_repo import PropertyRepository, AsyncPropertyRepository


class PropertyService:
    @staticmethod
    def query_available_units(
        session: Session,
        property_id: Optional[int] = None,
        city: Optional[str] = None,
        max_rent: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        repo = PropertyRepository(session)
        return repo.query_available_units(property_id=property_id, city=city, max_rent=max_rent)

    @staticmethod
    async def aquery_available_units(
        session: AsyncSession,
        property_id: Optional[int] = None,
        city: Optional[str] = None,
        max_rent: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        repo = AsyncPropertyRepository(session)
        return await repo.query_available_units(property_id=property_id, city=city, max_rent=max_rent)
