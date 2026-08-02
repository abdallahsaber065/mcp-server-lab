from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from mcp_server.memory.store import memory_store, maybe_remember, load_memory_context, decide_memory_fate

class RecordMemoryInput(BaseModel):
    tenant_id: int = Field(..., description="Target tenant ID to scope memory record to.")
    event_summary: str = Field(..., description="Short structured summary or turn text of event, preference, or fact worth remembering.")
    context: Optional[str] = Field(default=None, description="Context or scenario when this event occurred.")
    outcome: Optional[str] = Field(default=None, description="Outcome, resolution, or resulting action taken.")
    category: str = Field(default="general", description="Category tag (e.g. preference, health_medical, access, maintenance).")

    model_config = ConfigDict(extra="forbid")  # Strict MCP defensive Pydantic spec

class RecallMemoryInput(BaseModel):
    tenant_id: int = Field(..., description="Tenant ID to scope recall search to.")
    query: str = Field(default="", description="Search query or keyword to find relevant past records.")
    top_k: int = Field(default=3, ge=1, le=10, description="Max memory items to recall.")

    model_config = ConfigDict(extra="forbid")  # Strict MCP defensive Pydantic spec

def record_tenant_memory_handler(args: Dict[str, Any], session_role: str) -> Dict[str, Any]:
    """
    Record path handler calling `maybe_remember` (Option B write path).
    Evaluates memory fate decision and upserts to episodic store if destination == 'episodic'.
    """
    try:
        parsed = RecordMemoryInput.model_validate(args or {})
    except Exception as err:
        return {
            "status": "validation_error",
            "message": f"Invalid arguments for record_tenant_memory: {str(err)}"
        }

    # Direct call to Option B write path function `maybe_remember`
    entity_str = f"tenant_{parsed.tenant_id}"
    rec = maybe_remember(turn_text=parsed.event_summary, entity_id=entity_str)

    if not rec:
        decision = decide_memory_fate(parsed.event_summary)
        return {
            "status": "forgotten",
            "reasoning": decision.reasoning,
            "message": f"Turn evaluated as transient ('forget'). No record added for {entity_str}."
        }

    return {
        "status": "success",
        "message": f"Recorded episodic memory for tenant #{parsed.tenant_id}",
        "memory_record": rec
    }

def recall_tenant_memories_handler(args: Dict[str, Any], session_role: str) -> Dict[str, Any]:
    """
    Read path handler calling `load_memory_context` (Option B read path).
    Loads relevant past memory records and returns formatted context string + structured memories.
    """
    try:
        parsed = RecallMemoryInput.model_validate(args or {})
    except Exception as err:
        return {
            "status": "validation_error",
            "message": f"Invalid arguments for recall_tenant_memories: {str(err)}"
        }

    entity_str = f"tenant_{parsed.tenant_id}"
    # Direct call to Option B read path function `load_memory_context`
    context_text = load_memory_context(entity_id=entity_str, opening_message=parsed.query, top_k=parsed.top_k)
    memories = memory_store.recall_memories(tenant_id=parsed.tenant_id, query=parsed.query, top_k=parsed.top_k)

    return {
        "status": "success",
        "entity_id": entity_str,
        "context_text": context_text,
        "count": len(memories),
        "memories": memories
    }
