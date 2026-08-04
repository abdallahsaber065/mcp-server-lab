import os
import sys
import json
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger("mcp_web_app")

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.server import CornerstoneMCPServer
# from mcp_server.rag import knowledge_store  # Week 3: removed — needs update to use top-level rag/
# from mcp_server.memory import memory_store, RecordMemoryInput  # Week 3: removed — needs update to use top-level memory/
from mcp_server.db_helpers import (
    create_chat_session, get_all_chat_sessions, get_chat_messages,
    save_chat_message, delete_chat_session
)
from web.llm_engine import MCPLLMEngine, AVAILABLE_MODELS

app = FastAPI(
    title="Cornerstone Realty Group — MCP Autonomous Portal",
    description="Interactive Web UI & FastAPI backend for MCP Server Lab (Session 2)",
    version="3.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE FOR EVALUATION:
# The FastAPI Web Server, Interactive Chat UI, and LLM Web Engine in this folder are
# BONUS showcase enhancements created to present, test, and demonstrate the MCP Server
# in an end-to-end interactive portal. The core MCP protocol implementation and server
# components reside in `mcp_server/`.

mcp_server = CornerstoneMCPServer()
llm_engine = MCPLLMEngine(default_model="gemini/gemini-3.1-flash-lite")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

FIXED_PERSONAS: Dict[str, Dict[str, Any]] = {
    "tenant": {
        "name": "Amr Hassan",
        "tenant_id": 1,
        "email": "amr.hassan@example.com",
        "phone": "+201001234567",
        "role": "tenant",
        "unit_number": "A-101 (Cornerstone Heights, Cairo)",
        "lease_id": 1,
        "description": "Active tenant residing in unit A-101"
    },
    "property_manager": {
        "name": "Tarek Mahmoud",
        "tenant_id": 3,
        "email": "tarek.m@cornerstonerealty.eg",
        "phone": "+201223334444",
        "role": "property_manager",
        "description": "Property Manager handling unit searches, maintenance dispatch, and standard lease operations"
    },
    "executive_admin": {
        "name": "Laila Fouad",
        "tenant_id": 4,
        "email": "laila.fouad@cornerstonerealty.eg",
        "phone": "+201000000001",
        "role": "executive_admin",
        "description": "Executive Admin authorized for high-value lease sign-offs (>50,000 EGP) and policy overrides"
    }
}

class CreateSessionRequest(BaseModel):
    title: str = "محادثة جديدة"
    role: str = "property_manager"

class StreamChatRequest(BaseModel):
    session_id: str
    user_message: str
    model: str = "gemini/gemini-3.1-flash-lite"
    role: str = "property_manager"
    conversation_history: List[Dict[str, Any]] = []

class ElicitationResponse(BaseModel):
    session_id: str
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12

def build_system_prompt(role: str) -> str:
    persona = FIXED_PERSONAS.get(role, FIXED_PERSONAS["property_manager"])
    
    prompt = (
        f"You are the Cornerstone Realty Autonomous AI Assistant.\n"
        f"CURRENT AUTHENTICATED USER PERSONA:\n"
        f"- Name: {persona['name']}\n"
        f"- Role: {persona['role'].upper()}\n"
        f"- Email: {persona['email']}\n"
        f"- Phone: {persona['phone']}\n"
        f"- Tenant ID: {persona['tenant_id']}\n"
    )
    
    if role == "tenant":
        prompt += (
            f"- Assigned Unit: {persona['unit_number']}\n"
            f"- Active Lease ID: {persona['lease_id']}\n\n"
            "TENANT PERSONA BEHAVIOR:\n"
            "Whenever the user asks about 'my lease', 'my apartment', 'my unit', or 'my maintenance requests', "
            f"automatically use tenant_id={persona['tenant_id']} or email='{persona['email']}' in your MCP tool calls.\n\n"
        )
    elif role == "executive_admin":
        prompt += (
            "\nEXECUTIVE ADMIN BEHAVIOR:\n"
            "You have full authority to approve high-value lease agreements (>50,000 EGP/month) requiring executive sign-off, "
            "review company-wide lease terms, and override constraints.\n\n"
        )
    else:
        prompt += (
            "\nPROPERTY MANAGER BEHAVIOR:\n"
            "You manage property operations, unit search/lookup, maintenance dispatch, and standard tenant communication.\n\n"
        )

    # Week 3: Episodic memory recall disabled — mcp_server/memory removed, needs update to top-level memory/
    # tenant_id = persona.get("tenant_id", 1)
    # recalled_mems = memory_store.recall_memories(tenant_id=tenant_id, query="", top_k=3)
    # if recalled_mems:
    #     prompt += "RECALLED EPISODIC MEMORIES FOR THIS TENANT (Option B Memory):\n"
    #     for m in recalled_mems:
    #         prompt += f"- [{m['category'].upper()}] {m['event_summary']} (Recorded: {m['timestamp'][:10]})\n"
    #     prompt += "\n"

    prompt += (
        "CRITICAL MULTI-TOOL & REASONING RULES:\n"
        "1. Whenever answering a request, you MUST invoke the appropriate MCP tool(s) to fetch real database facts before responding.\n"
        "2. To search unstructured policy documents, quiet hours, early termination, or emergency procedures, call `search_knowledge_base` (RAG Tool - Option A).\n"
        "3. To recall or record tenant-specific preferences, medical constraints, or past notes, call `recall_tenant_memories` or `record_tenant_memory` (Memory Tools - Option B).\n"
        "4. If a request requires multiple actions (e.g. searching for available units THEN drafting a lease or checking tenant history), "
        "execute multiple MCP tool calls iteratively before generating your final response.\n"
        "5. Do NOT make up unit prices, lease numbers, or maintenance statuses.\n\n"
        "OUTPUT FORMAT INSTRUCTIONS:\n"
        "Format your final text responses strictly using clean, semantic HTML tags without markdown codeblock wrappers (no ```html). "
        "Use <h3> for section titles, <p> for text, <ul>/<li> for lists, <strong> for emphasis, and <table>/<thead>/<tbody>/<tr>/<th>/<td> for structured tables. "
        "This ensures rich rendering inside the portal interface."
    )
    return prompt

@app.get("/api/personas")
async def list_personas():
    return FIXED_PERSONAS
@app.get("/api/rag/documents")
async def list_rag_documents():
    """Week 3: Disabled — mcp_server/rag removed, needs update to use top-level rag/ package."""
    return {"status": "disabled", "message": "RAG endpoint needs migration to top-level rag/ package (Week 3)."}


@app.get("/api/memory/{tenant_id}")
async def get_tenant_memories_endpoint(tenant_id: int):
    """Week 3: Disabled — mcp_server/memory removed, needs update to use top-level memory/ package."""
    return {"status": "disabled", "message": "Memory endpoint needs migration to top-level memory/ package (Week 3).", "tenant_id": tenant_id}


@app.post("/api/memory/record")
async def record_memory_endpoint(req: dict):
    """Week 3: Disabled — mcp_server/memory removed, needs update to use top-level memory/ package."""
    return {"status": "disabled", "message": "Memory recording needs migration to top-level memory/ package (Week 3)."}
@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cornerstone MCP Portal Initialized</h1>")

@app.get("/api/chats")
async def list_chats():
    return get_all_chat_sessions()

@app.post("/api/chats")
async def create_chat(req: CreateSessionRequest):
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_data = create_chat_session(session_id=session_id, title=req.title, role=req.role)
    return session_data

@app.get("/api/chats/{session_id}")
async def get_chat(session_id: str):
    messages = get_chat_messages(session_id)
    return {"session_id": session_id, "messages": messages}

@app.delete("/api/chats/{session_id}")
async def delete_chat(session_id: str):
    success = delete_chat_session(session_id)
    return {"status": "success" if success else "error"}

@app.get("/api/models")
async def get_models():
    return {"models": AVAILABLE_MODELS, "default": "gemini/gemini-2.5-flash"}

@app.get("/api/capabilities")
async def get_capabilities():
    return mcp_server.get_capabilities()

@app.get("/api/tools")
async def list_tools(role: str = "property_manager"):
    return mcp_server.list_tools(role=role)

@app.get("/api/resources")
async def list_resources():
    return mcp_server.list_resources()

@app.get("/api/resource/read")
async def read_resource(uri: str = "realty://policies/lease_terms"):
    try:
        return mcp_server.read_resource(uri)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: StreamChatRequest):
    # Fetch prior history from SQLite for multi-turn context
    prior_db_messages = get_chat_messages(req.session_id)
    history_for_llm = []
    for m in prior_db_messages:
        if m["type"] == "user" and m.get("content"):
            history_for_llm.append({"role": "user", "content": m["content"]})
        elif m["type"] == "assistant" and m.get("content"):
            history_for_llm.append({"role": "assistant", "content": m["content"]})

    # Save current user prompt to SQLite
    save_chat_message(session_id=req.session_id, msg_type="user", content=req.user_message)
    system_prompt = build_system_prompt(req.role)
    
    stream_gen = llm_engine.execute_agent_loop_stream(
        mcp_server_instance=mcp_server,
        user_message=req.user_message,
        system_prompt=system_prompt,
        conversation_history=history_for_llm,
        model=req.model,
        role=req.role
    )
    
    async def sse_wrapper():
        full_assistant_text = ""
        async for chunk in stream_gen:
            yield chunk
            if chunk.startswith("data: "):
                try:
                    event = json.loads(chunk[6:].strip())
                    if event.get("type") == "tool_call":
                        save_chat_message(
                            session_id=req.session_id,
                            msg_type="tool_trace",
                            tool_name=event["tool"],
                            tool_args=event["args"],
                            tool_result=event["result"]
                        )
                    elif event.get("type") == "elicitation_required":
                        save_chat_message(
                            session_id=req.session_id,
                            msg_type="elicitation",
                            elicitation_payload=event["payload"]
                        )
                    elif event.get("type") == "token":
                        full_assistant_text += event["content"]
                    elif event.get("type") == "done":
                        if full_assistant_text:
                            save_chat_message(session_id=req.session_id, msg_type="assistant", content=full_assistant_text)
                except Exception as e:
                    logger.error(f"Error parsing/saving SSE event to DB: {e}")

    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

@app.post("/api/elicitation/respond")
async def respond_elicitation(req: ElicitationResponse):
    res = mcp_server.call_tool("modify_lease_terms", {
        "lease_id": req.lease_id,
        "new_monthly_rent": req.proposed_rent,
        "duration_months": req.duration_months,
        "executive_approval_given": req.approved
    })
    
    if req.approved:
        answer_text = f"<h3>✅ Executive Sign-off CONFIRMED</h3><p>Lease #{req.lease_id} rent updated to <strong>EGP {req.proposed_rent}</strong>.</p>"
    else:
        answer_text = f"<h3>❌ Executive Sign-off REJECTED</h3><p>Lease #{req.lease_id} rent remains unchanged.</p>"

    save_chat_message(session_id=req.session_id, msg_type="assistant", content=answer_text)

    return {
        "status": "success",
        "final_answer": answer_text,
        "result": res
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("web.app:app", host=host, port=port)

