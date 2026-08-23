"""
Semantic Memory Consolidation Layer.
A genuinely separate, periodic batch pass over the episodic store using SQLAlchemy ORM.
Extracts durable, generalized domain and tenant facts from episodic histories.
Handles 4 production challenges:
  1. Updates: Generalizes new facts over time.
  2. Versioning: Preserves historical fact versions (v1 -> v2) without silent overwrites.
  3. Expiration: Retires stale facts via TTL / validity windows.
  4. Conflict Resolution: Resolves real contradictions between opposing episodes.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, SemanticFactRecord
from db.session import SyncSessionLocal, sync_engine


class SemanticFact(BaseModel):
    fact_id: Optional[int] = None
    subject: str = Field(..., description="Tenant ID, Unit ID, or Property Name")
    fact_key: str = Field(..., description="E.g., 'lease_renewal_intent', 'floor_preference', 'paint_allergy'")
    fact_value: str = Field(..., description="The consolidated semantic fact statement")
    version: int = Field(default=1, description="Version number of the fact")
    status: str = Field(default="active", description="'active', 'superseded', or 'expired'")
    valid_from: str
    valid_to: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence_episode_ids: List[int] = Field(default_factory=list)
    superseded_by_id: Optional[int] = None


class SemanticMemoryStore:
    def __init__(self, db_path: str = ":memory:", session: Optional[Session] = None):
        """
        Initialize SemanticMemoryStore.
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

    def insert_fact(self, fact: SemanticFact) -> int:
        session = self._get_session()
        try:
            ev_str = ",".join(map(str, fact.evidence_episode_ids))
            record = SemanticFactRecord(
                subject=fact.subject,
                fact_key=fact.fact_key,
                fact_value=fact.fact_value,
                version=fact.version,
                status=fact.status,
                valid_from=fact.valid_from,
                valid_to=fact.valid_to,
                confidence=fact.confidence,
                evidence_episode_ids=ev_str,
                superseded_by_id=fact.superseded_by_id
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.fact_id
        finally:
            if not self._external_session:
                session.close()

    def get_active_facts(self, subject: str) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            stmt = (
                select(SemanticFactRecord)
                .where(SemanticFactRecord.subject == subject, SemanticFactRecord.status == "active")
                .order_by(SemanticFactRecord.fact_key.asc())
            )
            rows = session.scalars(stmt).all()
            return [
                {
                    "fact_id": r.fact_id,
                    "subject": r.subject,
                    "fact_key": r.fact_key,
                    "fact_value": r.fact_value,
                    "version": r.version,
                    "status": r.status,
                    "valid_from": r.valid_from,
                    "valid_to": r.valid_to,
                    "confidence": r.confidence,
                    "evidence_episode_ids": r.evidence_episode_ids or "",
                    "superseded_by_id": r.superseded_by_id
                }
                for r in rows
            ]
        finally:
            if not self._external_session:
                session.close()

    def get_fact_history(self, subject: str, fact_key: str) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            stmt = (
                select(SemanticFactRecord)
                .where(SemanticFactRecord.subject == subject, SemanticFactRecord.fact_key == fact_key)
                .order_by(SemanticFactRecord.version.asc())
            )
            rows = session.scalars(stmt).all()
            return [
                {
                    "fact_id": r.fact_id,
                    "subject": r.subject,
                    "fact_key": r.fact_key,
                    "fact_value": r.fact_value,
                    "version": r.version,
                    "status": r.status,
                    "valid_from": r.valid_from,
                    "valid_to": r.valid_to,
                    "confidence": r.confidence,
                    "evidence_episode_ids": r.evidence_episode_ids or "",
                    "superseded_by_id": r.superseded_by_id
                }
                for r in rows
            ]
        finally:
            if not self._external_session:
                session.close()

    def supersede_fact(self, old_fact_id: int, new_fact_id: int):
        session = self._get_session()
        try:
            stmt = (
                update(SemanticFactRecord)
                .where(SemanticFactRecord.fact_id == old_fact_id)
                .values(status="superseded", superseded_by_id=new_fact_id)
            )
            session.execute(stmt)
            session.commit()
        finally:
            if not self._external_session:
                session.close()

    def expire_stale_facts(self, current_time: Optional[str] = None) -> int:
        now_str = current_time or datetime.now(timezone.utc).isoformat()
        session = self._get_session()
        try:
            stmt = (
                update(SemanticFactRecord)
                .where(
                    SemanticFactRecord.status == "active",
                    SemanticFactRecord.valid_to.is_not(None),
                    SemanticFactRecord.valid_to < now_str
                )
                .values(status="expired")
            )
            res = session.execute(stmt)
            session.commit()
            return int(getattr(res, "rowcount", 0) or 0)
        finally:
            if not self._external_session:
                session.close()


class SemanticConsolidationEngine:
    def __init__(self, episodic_store, semantic_store: SemanticMemoryStore):
        self.episodic_store = episodic_store
        self.semantic_store = semantic_store

    def run_periodic_consolidation(self, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Main consolidation pass.
        Reads unconsolidated episodes, detects fact updates, resolves contradictions,
        and creates versioned semantic memory entries.
        """
        unconsolidated = self.episodic_store.get_unconsolidated_episodes(entity_id=subject)
        if not unconsolidated:
            return {"consolidated_episodes": 0, "facts_created": 0, "conflicts_resolved": 0}

        conflicts_resolved = 0
        facts_created = 0
        episodes_by_subject: Dict[str, List[Dict[str, Any]]] = {}

        for ep in unconsolidated:
            episodes_by_subject.setdefault(ep["entity_id"], []).append(ep)

        for subj, episodes in episodes_by_subject.items():
            # Process episodes chronologically
            episodes.sort(key=lambda x: x["timestamp"])
            for ep in episodes:
                extracted_facts = self._extract_semantic_facts(ep)
                for candidate in extracted_facts:
                    resolved = self._consolidate_fact(subj, candidate, ep["episode_id"])
                    if resolved:
                        conflicts_resolved += 1
                    facts_created += 1

        self.episodic_store.mark_consolidated([ep["episode_id"] for ep in unconsolidated])
        return {
            "consolidated_episodes": len(unconsolidated),
            "facts_created": facts_created,
            "conflicts_resolved": conflicts_resolved,
        }

    def _extract_semantic_facts(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule-based and LLM-ready semantic fact extractor.
        Extracts durable tenant preferences, lease intents, and operational facts.
        """
        summary = episode.get("event_summary", "").lower()
        context = episode.get("context", "") or ""
        text = f"{summary} {context}".lower()

        facts = []
        now_iso = datetime.now(timezone.utc).isoformat()
        # Default validity: 1 year for preferences, 90 days for renewal intents
        default_valid_to = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

        # 1. Floor preference
        if "high floor" in text or "top floor" in text:
            facts.append({
                "fact_key": "floor_preference",
                "fact_value": "Prefers high floors / penthouse levels with unobstructed views.",
                "valid_to": default_valid_to,
                "confidence": 0.95
            })
        elif "ground floor" in text or "low floor" in text:
            facts.append({
                "fact_key": "floor_preference",
                "fact_value": "Prefers ground floor or garden-accessible units.",
                "valid_to": default_valid_to,
                "confidence": 0.95
            })

        # 2. Allergy & Health Notes
        if "allergy" in text or "allergic" in text:
            if "paint" in text or "chemical" in text or "voc" in text:
                facts.append({
                    "fact_key": "health_restriction",
                    "fact_value": "Severe paint/VOC sensitivity. Requires low-VOC odorless materials and 48hr ventilation.",
                    "valid_to": None,  # Indefinite
                    "confidence": 0.98
                })

        # 3. Lease Renewal Intent
        if "renew" in text or "renewal" in text or "vacate" in text or "move out" in text or "moving out" in text:
            valid_to_renewal = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
            if "not renewing" in text or "moving out" in text or "will not renew" in text or "vacate" in text or "notice to vacate" in text:
                facts.append({
                    "fact_key": "lease_intent",
                    "fact_value": "Submitted formal notice to vacate; preparing move-out inspection.",
                    "valid_to": valid_to_renewal,
                    "confidence": 0.90
                })
            else:
                facts.append({
                    "fact_key": "lease_intent",
                    "fact_value": "Expressed active intent to renew lease for multi-year term.",
                    "valid_to": valid_to_renewal,
                    "confidence": 0.90
                })

        # 4. Budget / Concession sensitivity
        if "discount" in text or "concession" in text or "budget constraint" in text:
            facts.append({
                "fact_key": "commercial_negotiation",
                "fact_value": "Sensitive to rate increases; requested 10% loyalty concession during renewal discussion.",
                "valid_to": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
                "confidence": 0.85
            })

        return facts

    def _consolidate_fact(self, subject: str, candidate: Dict[str, Any], episode_id: int) -> bool:
        """
        Consolidates a candidate fact into semantic memory with versioning and conflict resolution.
        Returns True if a prior conflicting/superseded fact was replaced.
        """
        active_facts = self.semantic_store.get_active_facts(subject)
        existing = next((f for f in active_facts if f["fact_key"] == candidate["fact_key"]), None)

        now_iso = datetime.now(timezone.utc).isoformat()
        conflict_resolved = False

        if existing:
            # If value is unchanged, skip duplicate versioning
            if existing["fact_value"].strip().lower() == candidate["fact_value"].strip().lower():
                return False

            # Conflict / Update detected: Create vN+1 and supersede vN
            new_version = existing["version"] + 1
            new_fact = SemanticFact(
                subject=subject,
                fact_key=candidate["fact_key"],
                fact_value=candidate["fact_value"],
                version=new_version,
                status="active",
                valid_from=now_iso,
                valid_to=candidate.get("valid_to"),
                confidence=candidate.get("confidence", 0.90),
                evidence_episode_ids=[episode_id],
                superseded_by_id=None
            )
            new_fact_id = self.semantic_store.insert_fact(new_fact)
            self.semantic_store.supersede_fact(existing["fact_id"], new_fact_id)
            conflict_resolved = True
        else:
            # New fact (v1)
            new_fact = SemanticFact(
                subject=subject,
                fact_key=candidate["fact_key"],
                fact_value=candidate["fact_value"],
                version=1,
                status="active",
                valid_from=now_iso,
                valid_to=candidate.get("valid_to"),
                confidence=candidate.get("confidence", 0.90),
                evidence_episode_ids=[episode_id],
                superseded_by_id=None
            )
            self.semantic_store.insert_fact(new_fact)

        return conflict_resolved
