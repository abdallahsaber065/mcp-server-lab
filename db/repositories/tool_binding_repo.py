"""
Agent Tool Binding Repository (db/repositories/tool_binding_repo.py)
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import AgentToolBinding
from db.repositories.base import BaseRepository, AsyncBaseRepository


class ToolBindingRepository(BaseRepository[AgentToolBinding]):
    def __init__(self, session: Session):
        super().__init__(AgentToolBinding, session)

    def get_agent_bindings(self, agent_id: str) -> Dict[str, bool]:
        stmt = select(AgentToolBinding).where(AgentToolBinding.agent_id == agent_id)
        rows = self.session.scalars(stmt).all()
        return {r.tool_name: bool(r.is_enabled) for r in rows}

    def set_tool_status(self, agent_id: str, tool_name: str, is_enabled: bool) -> bool:
        stmt = select(AgentToolBinding).where(
            AgentToolBinding.agent_id == agent_id,
            AgentToolBinding.tool_name == tool_name
        )
        binding = self.session.scalars(stmt).first()
        if binding:
            binding.is_enabled = is_enabled
            binding.updated_at = datetime.utcnow()
        else:
            binding = AgentToolBinding(agent_id=agent_id, tool_name=tool_name, is_enabled=is_enabled)
            self.session.add(binding)
        self.session.commit()
        return True


class AsyncToolBindingRepository(AsyncBaseRepository[AgentToolBinding]):
    def __init__(self, session: AsyncSession):
        super().__init__(AgentToolBinding, session)

    async def get_agent_bindings(self, agent_id: str) -> Dict[str, bool]:
        stmt = select(AgentToolBinding).where(AgentToolBinding.agent_id == agent_id)
        result = await self.session.scalars(stmt)
        rows = result.all()
        return {r.tool_name: bool(r.is_enabled) for r in rows}

    async def set_tool_status(self, agent_id: str, tool_name: str, is_enabled: bool) -> bool:
        stmt = select(AgentToolBinding).where(
            AgentToolBinding.agent_id == agent_id,
            AgentToolBinding.tool_name == tool_name
        )
        result = await self.session.scalars(stmt)
        binding = result.first()
        if binding:
            binding.is_enabled = is_enabled
            binding.updated_at = datetime.utcnow()
        else:
            binding = AgentToolBinding(agent_id=agent_id, tool_name=tool_name, is_enabled=is_enabled)
            self.session.add(binding)
        await self.session.commit()
        return True
