"""
Episodic Memory Store.
Persists timestamped, context-rich historical events and conversations.
Answers: What happened? Who was involved? When did it happen? Why did it happen?
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional


class EpisodicStore:
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
            CREATE TABLE IF NOT EXISTS episodic_memory (
                episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                session_id TEXT DEFAULT 'default',
                timestamp DATETIME NOT NULL,
                event_summary TEXT NOT NULL,
                context TEXT,
                outcome TEXT,
                importance_score REAL DEFAULT 0.5,
                consolidated INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_episodic_entity ON episodic_memory(entity_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memory(timestamp);")
        conn.commit()
        if not self._shared_conn:
            conn.close()

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
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO episodic_memory (entity_id, session_id, timestamp, event_summary, context, outcome, importance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entity_id, session_id, ts, event_summary, context, outcome, importance_score))
        conn.commit()
        last_id = cursor.lastrowid
        if not self._shared_conn:
            conn.close()
        return last_id

    def query_episodes(self, entity_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if entity_id:
            cursor.execute("""
                SELECT * FROM episodic_memory WHERE entity_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (entity_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM episodic_memory ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        if not self._shared_conn:
            conn.close()
        return rows

    def get_unconsolidated_episodes(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if entity_id:
            cursor.execute("""
                SELECT * FROM episodic_memory WHERE consolidated = 0 AND entity_id = ? ORDER BY timestamp ASC
            """, (entity_id,))
        else:
            cursor.execute("""
                SELECT * FROM episodic_memory WHERE consolidated = 0 ORDER BY timestamp ASC
            """)
        rows = [dict(row) for row in cursor.fetchall()]
        if not self._shared_conn:
            conn.close()
        return rows

    def mark_consolidated(self, episode_ids: List[int]):
        if not episode_ids:
            return
        placeholders = ",".join("?" for _ in episode_ids)
        conn = self._get_connection()
        conn.execute(f"UPDATE episodic_memory SET consolidated = 1 WHERE episode_id IN ({placeholders})", episode_ids)
        conn.commit()
        if not self._shared_conn:
            conn.close()
