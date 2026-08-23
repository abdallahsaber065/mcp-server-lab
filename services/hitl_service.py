"""
HITL Service (services/hitl_service.py)
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.hitl_repo import AsyncHITLRepository, HITLRepository


class HITLService:
    @staticmethod
    def create_task(session: Session, run_id: str, graph_id: str, node_name: str, reason: str, payload: Dict[str, Any]) -> str:
        repo = HITLRepository(session)
        return repo.create_task(run_id, graph_id, node_name, reason, payload)

    @staticmethod
    async def acreate_task(session: AsyncSession, run_id: str, graph_id: str, node_name: str, reason: str, payload: Dict[str, Any]) -> str:
        repo = AsyncHITLRepository(session)
        return await repo.create_task(run_id, graph_id, node_name, reason, payload)

    @staticmethod
    def list_pending_tasks(session: Session) -> List[Dict[str, Any]]:
        repo = HITLRepository(session)
        return repo.list_pending_tasks()

    @staticmethod
    async def alist_pending_tasks(session: AsyncSession) -> List[Dict[str, Any]]:
        repo = AsyncHITLRepository(session)
        return await repo.list_pending_tasks()

    @staticmethod
    def resolve_task(session: Session, task_id: str, decision: str, notes: str = "", decided_by: str = "Admin") -> bool:
        repo = HITLRepository(session)
        return repo.resolve_task(task_id, decision, notes, decided_by)

    @staticmethod
    async def aresolve_task(session: AsyncSession, task_id: str, decision: str, notes: str = "", decided_by: str = "Admin") -> bool:
        repo = AsyncHITLRepository(session)
        return await repo.resolve_task(task_id, decision, notes, decided_by)
