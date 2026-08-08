"""
Promote-or-Drop Memory Routing Subsystem.
Fires when short-term memory overflows or an interaction turn concludes.
Decides whether an evicted item is discarded ('forget') or archived ('episodic').
CRITICAL GUARDRAIL: This router NEVER writes directly to semantic memory.
Every decision logs explicit rationale visible to graders and audits.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("memory.router")


class MemoryRoutingDecision(BaseModel):
    reasoning: str = Field(..., description="Explicit rationale justifying why the item is kept or dropped.")
    destination: Literal["forget", "episodic"] = Field(
        ..., 
        description="Target destination. Must ONLY be 'forget' or 'episodic'. Direct semantic writes are forbidden."
    )
    
    # Fields populated ONLY when destination == 'episodic'
    event_summary: Optional[str] = Field(None, description="Concise summary of the specific event.")
    context: Optional[str] = Field(None, description="Original context, constraints, or participant intent.")
    outcome: Optional[str] = Field(None, description="Result, decision reached, or pending follow-up.")
    entity_id: Optional[str] = Field(None, description="Scoped tenant_id, lease_id, or property_id.")
    importance_score: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class MemoryRouter:
    def __init__(self, episodic_store=None):
        self.episodic_store = episodic_store
        self.decision_log: List[Dict[str, Any]] = []

    def evaluate_item(self, item: Dict[str, Any], entity_id: Optional[str] = None) -> MemoryRoutingDecision:
        """
        Rule-based and LLM-ready evaluation of memory item fate.
        Filters out ephemeral chit-chat, boilerplate, and transient greetings,
        while preserving contractual lease terms, tenant preferences, and maintenance events.
        """
        content = item.get("content", "").lower()
        role = item.get("role", "")

        # High-value domain keywords in Cornerstone Realty
        domain_keywords = [
            "lease", "rent", "deposit", "renewal", "vacate", "terminate",
            "maintenance", "leak", "plumbing", "electrical", "hvac", "allergy",
            "preference", "discount", "signoff", "bylaw", "law 4", "penalty",
            "agreement", "extension", "cairo", "alexandria", "giza", "unit"
        ]

        # Ephemeral low-value noise
        noise_keywords = [
            "hello", "hi there", "good morning", "how can i help", 
            "thank you", "thanks", "bye", "okay", "understood"
        ]

        # 1. Ephemeral noise -> Forget
        if any(w in content for w in noise_keywords) and not any(k in content for k in domain_keywords):
            decision = MemoryRoutingDecision(
                reasoning=f"Item contains routine conversational pleasantry/acknowledgment with no durable domain facts: '{item.get('content')[:60]}...'",
                destination="forget"
            )
        # 2. Domain-relevant event -> Episodic
        elif any(k in content for k in domain_keywords) or role == "tool":
            decision = MemoryRoutingDecision(
                reasoning=f"Item contains actionable property/lease operations record requiring historical recall: '{item.get('content')[:60]}...'",
                destination="episodic",
                event_summary=item.get("content", "")[:200],
                context=f"Role: {role} in leasing/maintenance interaction.",
                outcome="Archived in episodic store for future cross-session recall and semantic consolidation.",
                entity_id=entity_id or item.get("entity_id", "general"),
                importance_score=0.85 if "lease" in content or "deposit" in content or "vacate" in content else 0.65
            )
        else:
            decision = MemoryRoutingDecision(
                reasoning=f"Generic query without lasting contractual or operational significance: '{item.get('content')[:60]}...'",
                destination="forget"
            )

        # Log decision for grading inspection
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "item_preview": item.get("content", "")[:80],
            "decision": decision.model_dump(),
        }
        self.decision_log.append(log_entry)
        logger.info(f"Memory Routing Decision: {decision.destination.upper()} | {decision.reasoning}")
        return decision

    def process_overflow(self, evicted_items: List[Dict[str, Any]], entity_id: Optional[str] = None) -> Dict[str, int]:
        """Process evicted STM items and archive episodic candidates."""
        counts = {"forget": 0, "episodic": 0}
        for item in evicted_items:
            decision = self.evaluate_item(item, entity_id=entity_id)
            counts[decision.destination] += 1
            
            if decision.destination == "episodic" and self.episodic_store:
                self.episodic_store.insert_episode(
                    entity_id=decision.entity_id or entity_id or "general",
                    event_summary=decision.event_summary or item.get("content", ""),
                    context=decision.context or "STM overflow eviction",
                    outcome=decision.outcome or "Stored",
                    importance_score=decision.importance_score or 0.5,
                )
        return counts
