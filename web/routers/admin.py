"""
Admin Operations Router (web/routers/admin.py)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RAGDocument, Tenant
from db.session import get_async_db
from mcp_server.server import CornerstoneMCPServer
from services.hitl_service import HITLService
from services.ticket_service import TicketService
from services.tool_registry_service import ToolRegistryService
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
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager", "accountant", "chief_engineer", "legal_counsel", "finance_officer", "site_supervisor"])),
    db: AsyncSession = Depends(get_async_db)
):
    """List pending Human-in-the-Loop review tasks — role-filtered in UI, all visible here for demo."""
    tasks = await HITLService.alist_pending_tasks(db)
    return {"status": "success", "tasks": tasks}


class ResolveHITLRequest(BaseModel):
    decision: str  # approved, rejected, modified
    notes: Optional[str] = ""
    decided_by: Optional[str] = "Executive Admin"
    updated_payload: Optional[Dict[str, Any]] = None


@router.post("/hitl/tasks/{task_id}/resolve")
async def resolve_hitl_task(
    task_id: str,
    req: ResolveHITLRequest,
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager", "accountant", "chief_engineer", "legal_counsel", "finance_officer"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Resolve an HITL review task, store edits, and resume linked LangGraph via Command(resume)."""
    success = await HITLService.aresolve_task(db, task_id, req.decision, req.notes or "", req.decided_by or current_user.full_name, req.updated_payload)
    # Resume via native LangGraph interrupt protocol — distinct from ticket recovery
    if req.decision in ("approved", "modified"):
        try:
            from db.models import HITLTask
            task_row = await db.get(HITLTask, task_id)
            if task_row and not task_row.run_id.startswith("demo-"):
                resume_payload = req.updated_payload or {"approved": True, "decision": req.decision, "notes": req.notes}
                # Normalize accountant/engineer/counsel payloads for interrupt resume
                if task_row.node_name and "accountant" in task_row.node_name:
                    resume_payload.setdefault("confirmed", True)
                # Dispatch via native graph Command(resume=...)
                from web.routers.state_graph import GRAPHS
                from services.state_graph_service import StateGraphService
                graph_id = StateGraphService.canonical_id(task_row.graph_id) if task_row.graph_id else "commercial_lease_flow"
                graph = GRAPHS.get(graph_id) or GRAPHS.get("commercial_lease_flow")
                if graph is not None:
                    try:
                        from langgraph.types import Command as _Cmd
                    except Exception:
                        _Cmd = dict  # type: ignore
                    config = {"configurable": {"thread_id": task_row.run_id}}
                    # Fire-and-forget resume; don't block HITL response
                    try:
                        await graph.ainvoke(_Cmd(resume=resume_payload), config=config)  # type: ignore
                    except Exception as resume_err:
                        print(f"HITL resume invoke for {task_id}: {resume_err}")
        except Exception as e:
            print(f"HITL resume notice for {task_id}: {e}")
    return {"status": "success", "task_id": task_id, "decision": req.decision}


# --- Failure Ticket Recovery ---
@router.get("/tickets")
async def list_failure_tickets(
    status: Optional[str] = None,
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager", "accountant", "chief_engineer", "legal_counsel", "finance_officer", "site_supervisor"])),
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
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager", "accountant", "chief_engineer", "legal_counsel", "finance_officer", "site_supervisor"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark a failure ticket as resolved."""
    success = await TicketService.aresolve_ticket(db, ticket_id, req.notes or "", req.resolved_by or current_user.full_name)
    return {"status": "success", "ticket_id": ticket_id, "resolved": success}


# --- RAG Document Ingestion ---
class IngestDocumentRequest(BaseModel):
    doc_id: str
    title: str
    category: str = "policy"
    content: str
    metadata_json: Optional[str] = "{}"


@router.get("/rag/documents")
async def list_rag_documents(
    current_user: Tenant = Depends(require_roles(["executive_admin", "property_manager"])),
    db: AsyncSession = Depends(get_async_db)
):
    """List all ingested RAG documents in the knowledge base."""
    from sqlalchemy import select
    stmt = select(RAGDocument).order_by(RAGDocument.created_at.desc())
    docs = (await db.scalars(stmt)).all()
    return {
        "status": "success",
        "documents": [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "category": d.category,
                "content_preview": d.content[:200] + ("..." if len(d.content) > 200 else ""),
                "content": d.content,
                "created_at": d.created_at.isoformat() if d.created_at else "",
            }
            for d in docs
        ]
    }


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


@router.delete("/rag/documents/{doc_id}")
async def delete_rag_document(
    doc_id: str,
    current_user: Tenant = Depends(require_roles(["executive_admin"])),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a RAG document from the knowledge base."""
    from sqlalchemy import delete
    stmt = delete(RAGDocument).where(RAGDocument.doc_id == doc_id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "success", "doc_id": doc_id, "deleted": True}
