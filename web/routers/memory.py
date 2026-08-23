"""
Memory Router (web/routers/memory.py)
Handles tenant memory queries, event recording, router demos, and semantic consolidation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Tenant
from db.session import get_async_db
from memory.consolidation import SemanticConsolidationEngine, SemanticMemoryStore
from memory.episodic_store import EpisodicStore
from memory.router import MemoryRouter
from web.deps import get_current_user

router = APIRouter(prefix="/api/memory", tags=["Memory"])

# Global memory instances for FastAPI endpoints (Unified central database)
episodic_store = EpisodicStore(db_path="central")
semantic_store = SemanticMemoryStore(db_path="central")
consolidation_engine = SemanticConsolidationEngine(episodic_store, semantic_store)
memory_router = MemoryRouter(episodic_store)


@router.get("/me")
async def get_my_memories(current_user: Tenant = Depends(get_current_user)):
    """Retrieve consolidated active semantic facts and episodic history for logged-in user."""
    return await get_tenant_memories(current_user.tenant_id)


@router.get("/{tenant_id}")
async def get_tenant_memories(tenant_id: int):
    """Retrieve consolidated active semantic facts and episodic history for a given tenant."""
    subject = f"tenant_{tenant_id}"
    active_facts = semantic_store.get_active_facts(subject=subject)
    episodes = episodic_store.query_episodes(entity_id=subject, limit=5)

    formatted_memories = []
    for f in active_facts:
        formatted_memories.append({
            "category": f["fact_key"],
            "event_summary": f"{f['fact_value']} (v{f['version']})",
            "version": f["version"],
            "status": f["status"]
        })
    for ep in episodes:
        formatted_memories.append({
            "category": "episodic",
            "event_summary": ep["event_summary"],
            "timestamp": ep["timestamp"]
        })

    return {
        "tenant_id": tenant_id,
        "facts_count": len(active_facts),
        "episodes_count": len(episodes),
        "memories": formatted_memories
    }


@router.post("/record")
async def record_memory(req: dict):
    """Route an event via MemoryRouter, persist to EpisodicStore, and trigger semantic consolidation."""
    tenant_id = req.get("tenant_id", 1)
    event_text = req.get("event_summary", "")
    decision = memory_router.evaluate_item(
        {"content": event_text, "role": "user"},
        entity_id=f"tenant_{tenant_id}"
    )
    consolidation_result = consolidation_engine.run_periodic_consolidation(subject=f"tenant_{tenant_id}")
    return {
        "status": "success",
        "routing_decision": decision,
        "consolidation": consolidation_result
    }


@router.post("/demo_route")
async def demo_route(req: Optional[dict] = None):
    """Interactive demo of promote-or-drop router with logged reasoning."""
    if req is None:
        req = {}
    content = req.get("content", "Tenant Dr. Tarek El-Mahdy reported severe paint allergy; requested low-VOC maintenance.")
    entity_id = req.get("entity_id", "tenant_1")
    decision = memory_router.evaluate_item(
        item={"content": content, "role": "user"},
        entity_id=entity_id
    )
    history = memory_router.decision_log
    return {
        "input_content": content,
        "entity_id": entity_id,
        "decision": decision.model_dump(),
        "reasoning": decision.reasoning,
        "destination": decision.destination,
        "recent_router_logs": history[-3:] if history else []
    }


@router.post("/demo_consolidate")
async def demo_consolidate(req: Optional[dict] = None):
    """Interactive demo of semantic consolidation & real contradiction resolution."""
    if req is None:
        req = {}
    tenant_id = req.get("tenant_id", 1)
    subject = f"tenant_{tenant_id}"

    if req.get("trigger_conflict", True):
        episodic_store.insert_episode(
            entity_id=subject,
            event_summary="Tenant submitted formal notice to vacate and relocate at lease end; cancelled renewal interest.",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    result = consolidation_engine.run_periodic_consolidation(subject=subject)
    active_facts = semantic_store.get_active_facts(subject=subject)
    history_facts = semantic_store.get_fact_history(subject=subject, fact_key="lease_intent")
    return {
        "subject": subject,
        "consolidation_result": result,
        "active_facts": active_facts,
        "full_history_including_superseded": history_facts,
        "conflict_resolved": any(f["status"] == "superseded" for f in history_facts)
    }
