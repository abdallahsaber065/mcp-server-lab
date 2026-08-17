"""
Admin Operations Router (web/routers/admin.py)
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_db
from db.models import Tenant, RAGDocument
from services.tool_registry_service import ToolRegistryService
from services.hitl_service import HITLService
from services.ticket_service import TicketService
from mcp_server.server import CornerstoneMCPServer
from web.deps import require_roles

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

mcp_server = CornerstoneMCPServer()


# --- Tool Matrix ---
@router.get("/agents/{agent_id}/tools")
async def get_agent_tools(agent_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get active tool permissions for a given agent persona."""
    bindings = await ToolRegistryService.aget_agent_tools(db, agent_id)
    all_tools = mcp_server.list_tools(role="executive_admin")
    result = []
    for t in all_tools:
        result.append({
            "name": t["name"],
            "description": t["description"],
            "is_enabled": bindings.get(t["name"], True)
        })
    return {"status": "success", "agent_id": agent_id, "tools": result}


class ToggleToolRequest(BaseModel):
    tool_name: str
    is_enabled: bool


@router.post("/agents/{agent_id}/tools/toggle")
async def toggle_agent_tool(
    agent_id: str,
    req: ToggleToolRequest,
    current_user: Tenant = Depends(require_roles(["executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Dynamically enable/disable a tool for an agent and emit listChanged."""
    success = await ToolRegistryService.atoggle_tool(
        session=db,
        agent_id=agent_id,
        tool_name=req.tool_name,
        is_enabled=req.is_enabled
    )
    return {"status": "success", "agent_id": agent_id, "tool_name": req.tool_name, "is_enabled": req.is_enabled}


# --- HITL Review Queue ---
@router.get("/hitl/tasks")
async def list_hitl_tasks(
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager"])),
    db: AsyncSession = Depends(get_async_db)
):
    """List pending Human-in-the-Loop review tasks."""
    tasks = await HITLService.alist_pending_tasks(db)
    return {"status": "success", "tasks": tasks}


class ResolveHITLRequest(BaseModel):
    decision: str  # approved, rejected, modified
    notes: Optional[str] = ""
    decided_by: Optional[str] = "Executive Admin"


@router.post("/hitl/tasks/{task_id}/resolve")
async def resolve_hitl_task(
    task_id: str,
    req: ResolveHITLRequest,
    current_user: Tenant = Depends(require_roles(["executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Resolve an HITL review task and unblock state graph."""
    success = await HITLService.aresolve_task(db, task_id, req.decision, req.notes, req.decided_by)
    return {"status": "success", "task_id": task_id, "decision": req.decision}


# --- Failure Ticket Recovery ---
@router.get("/tickets")
async def list_failure_tickets(
    status: Optional[str] = None,
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager"])),
    db: AsyncSession = Depends(get_async_db)
):
    """List captured state graph node failure tickets."""
    tickets = await TicketService.alist_tickets(db, status=status)
    return {"status": "success", "tickets": tickets}


class ResolveTicketRequest(BaseModel):
    notes: Optional[str] = ""
    resolved_by: Optional[str] = "Executive Admin"


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    req: ResolveTicketRequest,
    current_user: Tenant = Depends(require_roles(["executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark a failure ticket as resolved."""
    success = await TicketService.aresolve_ticket(db, ticket_id, req.notes or "", req.resolved_by or "Executive Admin")
    return {"status": "success", "ticket_id": ticket_id, "resolved": success}


# --- RAG Document Ingestion ---
class IngestDocumentRequest(BaseModel):
    doc_id: str
    title: str
    category: str = "policy"
    content: str
    metadata_json: Optional[str] = "{}"


@router.post("/rag/documents")
async def ingest_rag_document(
    req: IngestDocumentRequest,
    current_user: Tenant = Depends(require_roles(["executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Upload and dynamically index a regulatory policy or municipal document."""
    doc = RAGDocument(
        doc_id=req.doc_id,
        title=req.title,
        category=req.category,
        content=req.content,
        metadata_json=req.metadata_json or "{}"
    )
    db.add(doc)
    await db.commit()
    return {"status": "success", "doc_id": req.doc_id, "title": req.title, "indexed": True}
