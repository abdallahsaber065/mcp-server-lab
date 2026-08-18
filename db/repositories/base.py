"""
Generic Repository Base Classes (db/repositories/base.py)
Provides clean async and sync CRUD operations over SQLAlchemy 2.0 ORM models.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import Base

ModelType = TypeVar("ModelType", bound=Any)


class BaseRepository(Generic[ModelType]):
    """Synchronous Base Repository for MCP tools and sync contexts."""

    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        return self.session.get(self.model, id_val)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, id_val: Any, **kwargs) -> Optional[ModelType]:
        instance = self.get_by_id(id_val)
        if instance:
            for k, v in kwargs.items():
                setattr(instance, k, v)
            self.session.commit()
            self.session.refresh(instance)
        return instance

    def delete(self, id_val: Any) -> bool:
        instance = self.get_by_id(id_val)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False


class AsyncBaseRepository(Generic[ModelType]):
    """Asynchronous Base Repository for FastAPI and Async StateGraph workflows."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        return await self.session.get(self.model, id_val)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id_val: Any, **kwargs) -> Optional[ModelType]:
        instance = await self.get_by_id(id_val)
        if instance:
            for k, v in kwargs.items():
                setattr(instance, k, v)
            await self.session.commit()
            await self.session.refresh(instance)
        return instance

    async def delete(self, id_val: Any) -> bool:
        instance = await self.get_by_id(id_val)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        return False
