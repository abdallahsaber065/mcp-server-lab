"""
User Repository (db/repositories/user_repo.py)
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Tenant
from db.repositories.base import BaseRepository, AsyncBaseRepository


class UserRepository(BaseRepository[Tenant]):
    def __init__(self, session: Session):
        super().__init__(Tenant, session)

    def get_by_email(self, email: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.email == email)
        return self.session.scalars(stmt).first()

    def update_refresh_token(self, user_id: int, refresh_token: Optional[str]) -> bool:
        user = self.get_by_id(user_id)
        if user:
            user.refresh_token = refresh_token
            self.session.commit()
            return True
        return False


class AsyncUserRepository(AsyncBaseRepository[Tenant]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def get_by_email(self, email: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.email == email)
        result = await self.session.scalars(stmt)
        return result.first()

    async def update_refresh_token(self, user_id: int, refresh_token: Optional[str]) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            user.refresh_token = refresh_token
            await self.session.commit()
            return True
        return False

    async def create_user(self, full_name: str, email: str, hashed_password: str, phone: Optional[str] = None, role: str = "tenant") -> Tenant:
        user = Tenant(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
            phone=phone,
            role=role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
