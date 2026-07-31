import os
import sys
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.server import CornerstoneMCPServer
from mcp_server.llm_engine import MCPLLMEngine, AVAILABLE_MODELS
from mcp_server.db_helpers import (
    create_chat_session, get_all_chat_sessions, get_chat_messages,
    save_chat_message, delete_chat_session
)

app = FastAPI(
    title="Cornerstone Realty Group — MCP Autonomous Portal",
    description="Interactive Web UI & FastAPI backend for MCP Server Lab (Session 2)",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp_server = CornerstoneMCPServer()
llm_engine = MCPLLMEngine(default_model="gemini/gemini-2.5-flash")

static_dir = os.path.join(os.path.dirname(__file__), "web_static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class CreateSessionRequest(BaseModel):
    title: str = "محادثة جديدة"
    role: str = "property_manager"

class StreamChatRequest(BaseModel):
    session_id: str
    user_message: str
    model: str = "gemini/gemini-2.5-flash"
    role: str = "property_manager"
    conversation_history: List[Dict[str, Any]] = []

class ElicitationResponse(BaseModel):
    session_id: str
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12

def build_system_prompt(role: str) -> str:
    return (
        f"You are the Cornerstone Realty Autonomous AI Assistant for role '{role}'. "
        "Help property managers and tenants lookup available units, active lease agreements, "
        "submit maintenance requests, and modify lease terms using available MCP tools. "
        "Adhere strictly to Cornerstone Master Leasing Policy.\n\n"
        "OUTPUT FORMAT INSTRUCTIONS:\n"
        "Format your responses strictly using clean, semantic skeleton HTML tags without markdown block wrappers or <html>/<body> boilerplate. "
        "Use <h3> for titles, <p> for paragraphs, <ul>/<li> for lists, <strong> for emphasis, and <table>/<thead>/<tbody>/<tr>/<th>/<td> for structured data tables. "
        "This ensures rich visual rendering inside the portal chat interface."
    )

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cornerstone MCP Portal Initialized</h1>")

# --- SQLITE CHAT SESSION MANAGEMENT ENDPOINTS ---

@app.get("/api/chats")
async def list_chats():
    """List all saved chat sessions from SQLite database."""
    return get_all_chat_sessions()

@app.post("/api/chats")
async def create_chat(req: CreateSessionRequest):
    """Create a new chat session in SQLite DB."""
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_data = create_chat_session(session_id=session_id, title=req.title, role=req.role)
    return session_data

@app.get("/api/chats/{session_id}")
async def get_chat(session_id: str):
    """Load messages for a specific chat session from SQLite DB."""
    messages = get_chat_messages(session_id)
    return {"session_id": session_id, "messages": messages}

@app.delete("/api/chats/{session_id}")
async def delete_chat(session_id: str):
    """Delete a chat session and its messages from SQLite DB."""
    success = delete_chat_session(session_id)
    return {"status": "success" if success else "error"}

@app.get("/api/models")
async def get_models():
    """Return available free LLM models."""
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
    """SSE Streaming Chat Endpoint with SQLite message persistence."""
    # 1. Save user prompt to SQLite
    save_chat_message(session_id=req.session_id, msg_type="user", content=req.user_message)
    
    system_prompt = build_system_prompt(req.role)
    
    stream_gen = llm_engine.execute_agent_loop_stream(
        mcp_server_instance=mcp_server,
        user_message=req.user_message,
        system_prompt=system_prompt,
        conversation_history=req.conversation_history,
        model=req.model,
        role=req.role
    )
    
    async def sse_wrapper():
        full_assistant_text = ""
        async for chunk in stream_gen:
            yield chunk
            # Parse event chunk to save tool calls / assistant text to DB
            if chunk.startswith("data: "):
                try:
                    event = json.loads(chunk[6:].trim() if hasattr(chunk[6:], 'trim') else chunk[6:].strip())
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
                except Exception:
                    pass

    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

@app.post("/api/elicitation/respond")
async def respond_elicitation(req: ElicitationResponse):
    """Resume tool execution after human sign-off decision."""
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
    uvicorn.run("mcp_server.web_app:app", host="127.0.0.1", port=8000, reload=True)
