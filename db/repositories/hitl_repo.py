"""
HITL Task Repository (db/repositories/hitl_repo.py)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import HITLTask
from db.repositories.base import AsyncBaseRepository, BaseRepository


class HITLRepository(BaseRepository[HITLTask]):
    def __init__(self, session: Session):
        super().__init__(HITLTask, session)

    def create_task(self, run_id: str, graph_id: str, node_name: str, reason: str, payload: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        task = HITLTask(
            task_id=task_id,
            run_id=run_id,
            graph_id=graph_id,
            node_name=node_name,
            reason=reason,
            payload_json=json.dumps(payload),
            task_status="pending"
        )
        self.session.add(task)
        self.session.commit()
        return task_id

    def list_pending_tasks(self) -> List[Dict[str, Any]]:
        stmt = select(HITLTask).where(HITLTask.task_status == "pending").order_by(HITLTask.created_at.desc())
        rows = self.session.scalars(stmt).all()
        return [
            {
                "task_id": r.task_id,
                "run_id": r.run_id,
                "graph_id": r.graph_id,
                "node": r.node_name,
                "reason": r.reason,
                "payload": json.loads(r.payload_json),
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in rows
        ]

    def resolve_task(self, task_id: str, decision: str, notes: str = "", decided_by: str = "Admin", updated_payload: dict | None = None) -> bool:
        task = self.session.get(HITLTask, task_id)
        if task:
            task.task_status = decision
            task.decision_notes = notes
            task.decided_by = decided_by
            task.resolved_at = datetime.now(timezone.utc)
            if updated_payload:
                try:
                    existing = json.loads(task.payload_json) if task.payload_json else {}
                    existing.update(updated_payload)
                    # keep original for audit, store merged
                    task.payload_json = json.dumps(existing, ensure_ascii=False)
                    if decision == "approved":
                        task.task_status = "modified"
                except Exception:
                    pass
            self.session.commit()
            return True
        return False


class AsyncHITLRepository(AsyncBaseRepository[HITLTask]):
    def __init__(self, session: AsyncSession):
        super().__init__(HITLTask, session)

    async def create_task(self, run_id: str, graph_id: str, node_name: str, reason: str, payload: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        task = HITLTask(
            task_id=task_id,
            run_id=run_id,
            graph_id=graph_id,
            node_name=node_name,
            reason=reason,
            payload_json=json.dumps(payload),
            task_status="pending"
        )
        self.session.add(task)
        await self.session.commit()
        return task_id

    async def list_pending_tasks(self) -> List[Dict[str, Any]]:
        stmt = select(HITLTask).where(HITLTask.task_status == "pending").order_by(HITLTask.created_at.desc())
        result = await self.session.scalars(stmt)
        rows = result.all()
        return [
            {
                "task_id": r.task_id,
                "run_id": r.run_id,
                "graph_id": r.graph_id,
                "node": r.node_name,
                "reason": r.reason,
                "payload": json.loads(r.payload_json),
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in rows
        ]

    async def resolve_task(self, task_id: str, decision: str, notes: str = "", decided_by: str = "Admin", updated_payload: dict | None = None) -> bool:
        task = await self.session.get(HITLTask, task_id)
        if task:
            task.task_status = decision
            task.decision_notes = notes
            task.decided_by = decided_by
            task.resolved_at = datetime.now(timezone.utc)
            if updated_payload:
                try:
                    existing = json.loads(task.payload_json) if task.payload_json else {}
                    existing.update(updated_payload)
                    task.payload_json = json.dumps(existing, ensure_ascii=False)
                    if decision == "approved":
                        task.task_status = "modified"
                except Exception:
                    pass
            await self.session.commit()
            return True
        return False
