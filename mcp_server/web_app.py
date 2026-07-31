import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.server import CornerstoneMCPServer
from mcp_server.llm_engine import MCPLLMEngine

app = FastAPI(
    title="Cornerstone Realty Group — MCP Autonomous Portal",
    description="Interactive Web UI & FastAPI backend for MCP Server Lab (Session 2)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP Server & AI Engine instances
mcp_server = CornerstoneMCPServer()
llm_engine = MCPLLMEngine(default_model="gemini/gemini-1.5-flash")

# Serve static frontend files
static_dir = os.path.join(os.path.dirname(__file__), "web_static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ChatRequest(BaseModel):
    user_message: str
    model: str = "gemini/gemini-1.5-flash"
    role: str = "property_manager"
    conversation_history: List[Dict[str, Any]] = []

class ElicitationResponse(BaseModel):
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cornerstone MCP Portal Initialized</h1>")

@app.get("/api/capabilities")
async def get_capabilities():
    """Return declared MCP server capabilities."""
    return mcp_server.get_capabilities()

@app.get("/api/tools")
async def list_tools(role: str = "property_manager"):
    """Return available tools for authenticated role."""
    return mcp_server.list_tools(role=role)

@app.get("/api/resources")
async def list_resources():
    """Return exposed static resources."""
    return mcp_server.list_resources()

@app.get("/api/resource/read")
async def read_resource(uri: str = "realty://policies/lease_terms"):
    """Read static policy resource."""
    try:
        return mcp_server.read_resource(uri)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Multi-turn Chat Endpoint with MCP Function Calling & Elicitation Interception."""
    system_prompt = (
        f"You are the Cornerstone Realty Autonomous AI Assistant for role '{req.role}'. "
        "Help property managers and tenants lookup units, active leases, submit maintenance requests, "
        "and update lease terms using available MCP tools. Adhere strictly to Cornerstone Master Leasing Policy."
    )
    
    result = await llm_engine.execute_agent_loop(
        mcp_server_instance=mcp_server,
        user_message=req.user_message,
        system_prompt=system_prompt,
        conversation_history=req.conversation_history,
        model=req.model,
        role=req.role
    )
    return JSONResponse(content=result)

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
        answer_text = f"✅ Executive Sign-off CONFIRMED for Lease #{req.lease_id}. Rent updated to EGP {req.proposed_rent}."
    else:
        answer_text = f"❌ Executive Sign-off REJECTED for Lease #{req.lease_id}. Rent remains unchanged."

    return {
        "status": "success",
        "final_answer": answer_text,
        "result": res
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server.web_app:app", host="127.0.0.1", port=8000, reload=True)
