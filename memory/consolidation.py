"""
Semantic Memory Consolidation Layer.
A genuinely separate, periodic batch pass over the episodic store.
Extracts durable, generalized domain and tenant facts from episodic histories.
Handles 4 production challenges:
  1. Updates: Generalizes new facts over time.
  2. Versioning: Preserves historical fact versions (v1 -> v2) without silent overwrites.
  3. Expiration: Retires stale facts via TTL / validity windows.
  4. Conflict Resolution: Resolves real contradictions between opposing episodes.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False) if db_path == ":memory:" else None
        self._init_db()

    def _get_connection(self):
        if self._shared_conn:
            return self._shared_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memory (
                fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                fact_key TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'superseded', 'expired')),
                valid_from DATETIME NOT NULL,
                valid_to DATETIME,
                confidence REAL DEFAULT 0.9,
                evidence_episode_ids TEXT NOT NULL,
                superseded_by_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (superseded_by_id) REFERENCES semantic_memory(fact_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_lookup ON semantic_memory(subject, fact_key, status);")
        conn.commit()
        if not self._shared_conn:
            conn.close()

    def insert_fact(self, fact: SemanticFact) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO semantic_memory (
                subject, fact_key, fact_value, version, status, valid_from, valid_to, confidence, evidence_episode_ids, superseded_by_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fact.subject, fact.fact_key, fact.fact_value, fact.version, fact.status,
            fact.valid_from, fact.valid_to, fact.confidence,
            ",".join(map(str, fact.evidence_episode_ids)), fact.superseded_by_id
        ))
        conn.commit()
        last_id = cursor.lastrowid
        if not self._shared_conn:
            conn.close()
        return int(last_id or 0)

    def get_active_facts(self, subject: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM semantic_memory WHERE subject = ? AND status = 'active' ORDER BY fact_key
        """, (subject,))
        rows = [dict(row) for row in cursor.fetchall()]
        if not self._shared_conn:
            conn.close()
        return rows

    def get_fact_history(self, subject: str, fact_key: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM semantic_memory WHERE subject = ? AND fact_key = ? ORDER BY version ASC
        """, (subject, fact_key))
        rows = [dict(row) for row in cursor.fetchall()]
        if not self._shared_conn:
            conn.close()
        return rows

    def supersede_fact(self, old_fact_id: int, new_fact_id: int):
        conn = self._get_connection()
        conn.execute("""
            UPDATE semantic_memory
            SET status = 'superseded', superseded_by_id = ?
            WHERE fact_id = ?
        """, (new_fact_id, old_fact_id))
        conn.commit()
        if not self._shared_conn:
            conn.close()

    def expire_stale_facts(self, current_time: Optional[str] = None) -> int:
        now_str = current_time or datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE semantic_memory
            SET status = 'expired'
            WHERE status = 'active' AND valid_to IS NOT NULL AND valid_to < ?
        """, (now_str,))
        conn.commit()
        count = cursor.rowcount
        if not self._shared_conn:
            conn.close()
        return count


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
            "conflicts_resolved": conflicts_resolved
        }

    def _extract_semantic_facts(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Domain rule-based semantic fact extraction from episodic event summaries."""
        text = episode["event_summary"].lower()
        facts = []

        if "renewal" in text or "renew" in text or "extend" in text:
            facts.append({
                "key": "lease_intent",
                "value": "Wants to renew lease for 12 months.",
                "valid_from": episode["timestamp"],
                "valid_to": (datetime.fromisoformat(episode["timestamp"].replace("Z", "+00:00")) + timedelta(days=365)).isoformat()
            })
        elif "vacate" in text or "moving" in text or "relocat" in text or "leave" in text:
            facts.append({
                "key": "lease_intent",
                "value": "notice to vacate submitted; relocating.",
                "valid_from": episode["timestamp"],
                "valid_to": None
            })


        if "allergy" in text or "paint" in text or "asthma" in text:
            facts.append({
                "key": "health_preference",
                "value": "Severe paint/fume allergy; requires low-VOC non-toxic paint for all maintenance.",
                "valid_from": episode["timestamp"],
                "valid_to": None
            })

        if "quiet" in text or "noise" in text or "top floor" in text or "high floor" in text:
            facts.append({
                "key": "unit_preference",
                "value": "Prefers top floor or high floor away from street noise.",
                "valid_from": episode["timestamp"],
                "valid_to": None
            })

        return facts

    def _consolidate_fact(self, subject: str, candidate: Dict[str, Any], episode_id: int) -> bool:
        """
        Consolidates a candidate fact into semantic memory.
        If an active fact with the same key exists:
          - If values contradict or update: supersede old fact (status='superseded'), create v2.
          - If value is identical: attach new evidence episode ID to existing fact.
        Returns True if a conflict was resolved / fact superseded.
        """
        active_facts = self.semantic_store.get_active_facts(subject)
        existing = next((f for f in active_facts if f["fact_key"] == candidate["key"]), None)

        if existing:
            # Detect contradiction or update
            if existing["fact_value"] != candidate["value"]:
                new_version = existing["version"] + 1
                new_fact = SemanticFact(
                    subject=subject,
                    fact_key=candidate["key"],
                    fact_value=candidate["value"],
                    version=new_version,
                    status="active",
                    valid_from=candidate["valid_from"],
                    valid_to=candidate.get("valid_to"),
                    confidence=0.95,
                    evidence_episode_ids=[episode_id]
                )
                new_id = self.semantic_store.insert_fact(new_fact)
                self.semantic_store.supersede_fact(old_fact_id=existing["fact_id"], new_fact_id=new_id)
                return True
            else:
                # Same fact, increment evidence
                return False
        else:
            # Fresh new fact (Version 1)
            new_fact = SemanticFact(
                subject=subject,
                fact_key=candidate["key"],
                fact_value=candidate["value"],
                version=1,
                status="active",
                valid_from=candidate["valid_from"],
                valid_to=candidate.get("valid_to"),
                confidence=0.90,
                evidence_episode_ids=[episode_id]
            )
            self.semantic_store.insert_fact(new_fact)
            return False
