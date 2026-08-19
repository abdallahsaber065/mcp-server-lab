"""
Episodic Memory Store.
Persists timestamped, context-rich historical events and conversations using SQLAlchemy ORM.
Answers: What happened? Who was involved? When did it happen? Why did it happen?
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, EpisodicMemoryRecord
from db.session import SyncSessionLocal, sync_engine


class EpisodicStore:
    def __init__(self, db_path: str = ":memory:", session: Optional[Session] = None):
        """
        Initialize EpisodicStore.
        If db_path == ':memory:' (default), creates an isolated in-memory SQLite engine for tests.
        Otherwise, uses the application's central SQLAlchemy database (Postgres/SQLite).
        """
        if session:
            self._external_session = True
            self.session = session
            self._session_factory = None
        elif db_path == ":memory:":
            self._external_session = False
            engine = create_engine("sqlite:///:memory:", echo=False)
            Base.metadata.create_all(engine)
            self._session_factory = sessionmaker(bind=engine)
            self.session = None
        else:
            self._external_session = False
            self._session_factory = SyncSessionLocal
            self.session = None

    def _get_session(self) -> Session:
        if self._external_session and self.session:
            return self.session
        assert self._session_factory is not None
        return self._session_factory()

    def insert_episode(
        self,
        entity_id: str,
        event_summary: str,
        context: Optional[str] = None,
        outcome: Optional[str] = None,
        session_id: str = "default",
        importance_score: float = 0.5,
        timestamp: Optional[str] = None,
    ) -> int:
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        session = self._get_session()
        try:
            record = EpisodicMemoryRecord(
                entity_id=entity_id,
                session_id=session_id,
                timestamp=dt,
                event_summary=event_summary,
                context=context,
                outcome=outcome,
                importance_score=importance_score,
                consolidated=0
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.episode_id
        finally:
            if not self._external_session:
                session.close()

    def query_episodes(self, entity_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            stmt = select(EpisodicMemoryRecord)
            if entity_id:
                stmt = stmt.where(EpisodicMemoryRecord.entity_id == entity_id)
            stmt = stmt.order_by(EpisodicMemoryRecord.timestamp.desc()).limit(limit)

            rows = session.scalars(stmt).all()
            return [
                {
                    "episode_id": r.episode_id,
                    "entity_id": r.entity_id,
                    "session_id": r.session_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "event_summary": r.event_summary,
                    "context": r.context,
                    "outcome": r.outcome,
                    "importance_score": r.importance_score,
                    "consolidated": r.consolidated
                }
                for r in rows
            ]
        finally:
            if not self._external_session:
                session.close()

    def get_unconsolidated_episodes(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            stmt = select(EpisodicMemoryRecord).where(EpisodicMemoryRecord.consolidated == 0)
            if entity_id:
                stmt = stmt.where(EpisodicMemoryRecord.entity_id == entity_id)
            stmt = stmt.order_by(EpisodicMemoryRecord.timestamp.asc())

            rows = session.scalars(stmt).all()
            return [
                {
                    "episode_id": r.episode_id,
                    "entity_id": r.entity_id,
                    "session_id": r.session_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "event_summary": r.event_summary,
                    "context": r.context,
                    "outcome": r.outcome,
                    "importance_score": r.importance_score,
                    "consolidated": r.consolidated
                }
                for r in rows
            ]
        finally:
            if not self._external_session:
                session.close()

    def mark_consolidated(self, episode_ids: List[int]):
        if not episode_ids:
            return
        session = self._get_session()
        try:
            stmt = (
                update(EpisodicMemoryRecord)
                .where(EpisodicMemoryRecord.episode_id.in_(episode_ids))
                .values(consolidated=1)
            )
            session.execute(stmt)
            session.commit()
        finally:
            if not self._external_session:
                session.close()
