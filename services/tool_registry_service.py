"""
Tool Registry Service (services/tool_registry_service.py)
Encapsulates runtime dynamic tool permission toggling and MCP list_changed notifications.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.tool_binding_repo import ToolBindingRepository, AsyncToolBindingRepository
from mcp_server.notifications import dispatcher, ToolListChangedNotification


class ToolRegistryService:
    @staticmethod
    def get_agent_tools(session: Session, agent_id: str) -> Dict[str, bool]:
        repo = ToolBindingRepository(session)
        return repo.get_agent_bindings(agent_id)

    @staticmethod
    async def aget_agent_tools(session: AsyncSession, agent_id: str) -> Dict[str, bool]:
        repo = AsyncToolBindingRepository(session)
        return await repo.get_agent_bindings(agent_id)

    @staticmethod
    def toggle_tool(
        session: Session,
        agent_id: str,
        tool_name: str,
        is_enabled: bool,
        current_role: str = "property_manager",
        active_tools: List[str] = None
    ) -> bool:
        repo = ToolBindingRepository(session)
        success = repo.set_tool_status(agent_id, tool_name, is_enabled)
        if success:
            notif = ToolListChangedNotification(
                previous_role=current_role,
                new_role=current_role,
                available_tools=active_tools or []
            )
            dispatcher.dispatch(notif.to_dict())
        return success

    @staticmethod
    async def atoggle_tool(
        session: AsyncSession,
        agent_id: str,
        tool_name: str,
        is_enabled: bool,
        current_role: str = "property_manager",
        active_tools: List[str] = None
    ) -> bool:
        repo = AsyncToolBindingRepository(session)
        success = await repo.set_tool_status(agent_id, tool_name, is_enabled)
        if success:
            notif = ToolListChangedNotification(
                previous_role=current_role,
                new_role=current_role,
                available_tools=active_tools or []
            )
            dispatcher.dispatch(notif.to_dict())
        return success
