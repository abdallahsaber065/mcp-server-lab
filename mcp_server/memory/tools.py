from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from mcp_server.memory.store import memory_store

class RecordMemoryInput(BaseModel):
    tenant_id: int = Field(..., description="Target tenant ID to scope memory record to.")
    event_summary: str = Field(..., description="Short structured summary of event, preference, or fact worth remembering.")
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
    """Record a new episodic memory record for a tenant."""
    try:
        parsed = RecordMemoryInput.model_validate(args or {})
    except Exception as err:
        return {
            "status": "validation_error",
            "message": f"Invalid arguments for record_tenant_memory: {str(err)}"
        }

    rec = memory_store.record_memory(
        tenant_id=parsed.tenant_id,
        event_summary=parsed.event_summary,
        context=parsed.context,
        outcome=parsed.outcome,
        category=parsed.category
    )

    return {
        "status": "success",
        "message": f"Recorded episodic memory for tenant #{parsed.tenant_id}",
        "memory_record": rec
    }

def recall_tenant_memories_handler(args: Dict[str, Any], session_role: str) -> Dict[str, Any]:
    """Recall relevant past memories for a tenant across sessions."""
    try:
        parsed = RecallMemoryInput.model_validate(args or {})
    except Exception as err:
        return {
            "status": "validation_error",
            "message": f"Invalid arguments for recall_tenant_memories: {str(err)}"
        }

    memories = memory_store.recall_memories(
        tenant_id=parsed.tenant_id,
        query=parsed.query,
        top_k=parsed.top_k
    )

    if not memories:
        return {
            "status": "no_memories",
            "message": f"No prior episodic memories found for tenant #{parsed.tenant_id}.",
            "tenant_id": parsed.tenant_id,
            "count": 0
        }

    return {
        "status": "success",
        "tenant_id": parsed.tenant_id,
        "count": len(memories),
        "memories": memories
    }
