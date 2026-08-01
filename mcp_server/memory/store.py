import math
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

class MemoryRoutingDecision(BaseModel):
    reasoning: str
    destination: Literal["forget", "episodic"]
    event_summary: Optional[str] = None
    context: Optional[str] = None
    outcome: Optional[str] = None
    category: str = "preference"

    model_config = ConfigDict(extra="forbid")

def decide_memory_fate(turn_text: str) -> MemoryRoutingDecision:
    """
    Evaluates whether conversation turn contains a lasting preference, constraint,
    or medical/maintenance fact worth storing in episodic memory.
    """
    text_lower = turn_text.lower()
    if any(k in text_lower for k in ["prefer", "allergy", "allerg", "schedule", "work from home", "keycard", "contact method"]):
        return MemoryRoutingDecision(
            reasoning="Contains tenant lasting preference or medical/operational constraint.",
            destination="episodic",
            event_summary=turn_text,
            context="Reported during conversation turn",
            outcome="Saved to agent episodic memory",
            category="preference" if "prefer" in text_lower or "schedule" in text_lower else "medical_health"
        )
    return MemoryRoutingDecision(
        reasoning="Routine transient message, not worth persisting.",
        destination="forget"
    )

class EpisodicMemoryStore:
    """Stores and retrieves tenant-scoped episodic memories using BM25 and entity isolation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.memories: List[Dict[str, Any]] = []

    def record_memory(
        self,
        tenant_id: int,
        event_summary: str,
        context: Optional[str] = None,
        outcome: Optional[str] = None,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Record a structured memory record scoped to a specific tenant ID."""
        mem_id = f"mem_{tenant_id}_{len(self.memories) + 1}"
        record = {
            "memory_id": mem_id,
            "tenant_id": tenant_id,
            "event_summary": event_summary,
            "context": context or "General record",
            "outcome": outcome or "Stored in episodic memory",
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.memories.append(record)
        return record

    def recall_memories(self, tenant_id: int, query: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """Recall relevant past memories scoped to tenant_id using BM25 term relevance."""
        tenant_mems = [m for m in self.memories if m["tenant_id"] == tenant_id]
        if not tenant_mems:
            return []

        if not query or not query.strip():
            # Return latest memories sorted by timestamp if query is empty
            sorted_mems = sorted(tenant_mems, key=lambda x: x["timestamp"], reverse=True)
            return sorted_mems[:top_k]

        query_terms = tokenize(query)
        if not query_terms:
            return tenant_mems[:top_k]

        N = len(tenant_mems)
        doc_tokens = [tokenize(m["event_summary"] + " " + m.get("context", "") + " " + m.get("category", "")) for m in tenant_mems]
        doc_lengths = [len(t) for t in doc_tokens]
        avg_len = sum(doc_lengths) / (N or 1)

        scores = [0.0] * N
        for term in query_terms:
            df = sum(1 for tokens in doc_tokens if term in tokens)
            if df == 0:
                continue
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            for i, tokens in enumerate(doc_tokens):
                tf = tokens.count(term)
                if tf > 0:
                    d_len = doc_lengths[i]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / (avg_len or 1.0)))
                    scores[i] += idf * (tf * (self.k1 + 1.0) / denom)

        scored = [
            {**tenant_mems[i], "relevance_score": round(scores[i], 4)}
            for i in range(N)
            if scores[i] > 0.0
        ]
        # Sort by relevance score descending, then timestamp descending
        scored.sort(key=lambda x: (x["relevance_score"], x["timestamp"]), reverse=True)
        return scored[:top_k]

# Global agent memory store instance
memory_store = EpisodicMemoryStore()

def seed_cornerstone_memories():
    """Seed initial episodic memories for showcase demonstration."""
    if len(memory_store.memories) > 0:
        return

    # Tenant Persona (ID: 1): Amr Hassan
    memory_store.record_memory(
        tenant_id=1,
        event_summary="Tenant prefers morning maintenance appointments (9:00 AM - 11:00 AM) due to work-from-home schedule.",
        context="Reported during AC maintenance scheduling call",
        outcome="Preference logged for maintenance dispatch",
        category="preference"
    )
    memory_store.record_memory(
        tenant_id=1,
        event_summary="Requested additional building access keycard for spouse; request verified and issued.",
        context="Front desk visit on 2025-02-10",
        outcome="Keycard #KC-101-2 issued",
        category="access"
    )
    memory_store.record_memory(
        tenant_id=1,
        event_summary="Tenant has a shy pet Golden Retriever; requested technicians knock gently before entering.",
        context="Tenant profile update",
        outcome="Noted on tenant entry profile",
        category="preference"
    )

    # Tenant (ID: 2): Noha El-Sayed
    memory_store.record_memory(
        tenant_id=2,
        event_summary="Tenant has severe dust & mold allergy; requires hypoallergenic HVAC air filters during routine maintenance.",
        context="Reported during lease onboarding interview",
        outcome="High-efficiency MERV-13 filter requirement added to tenant profile",
        category="health_medical"
    )

    # Property Manager Persona (ID: 3): Tarek Mahmoud
    memory_store.record_memory(
        tenant_id=3,
        event_summary="Property Manager priority focus for Q3: Alexandria Beachfront Towers occupancy and HVAC maintenance audit.",
        context="Manager strategy meeting",
        outcome="High priority flag set for Alexandria maintenance",
        category="operational"
    )
    memory_store.record_memory(
        tenant_id=3,
        event_summary="Pre-approved emergency plumbing repair budget up to 15,000 EGP per ticket for rapid dispatch.",
        context="Emergency policy update",
        outcome="Fast-track repair authorization enabled",
        category="approval"
    )

    # Executive Admin Persona (ID: 4): Laila Fouad
    memory_store.record_memory(
        tenant_id=4,
        event_summary="Executive Admin requires mandatory 2FA sign-off for any rent waiver or discount exceeding 100,000 EGP.",
        context="Executive compliance policy",
        outcome="Elicitation rule enforced",
        category="compliance"
    )
    memory_store.record_memory(
        tenant_id=4,
        event_summary="Authorized special corporate discount rate (up to 20%) for long-term multi-unit commercial leases.",
        context="Corporate policy update",
        outcome="Corporate discount matrix active",
        category="policy"
    )

seed_cornerstone_memories()
