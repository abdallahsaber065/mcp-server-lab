"""
MCP Protocol Router (web/routers/mcp_protocol.py)
Handles MCP tools, capabilities, resources, prompts, and model registry.
"""

from fastapi import APIRouter, HTTPException

from mcp_server.server import CornerstoneMCPServer
from web.llm_engine import AVAILABLE_MODELS

router = APIRouter(prefix="/api", tags=["MCP Protocol"])
mcp_server = CornerstoneMCPServer()


@router.get("/models")
async def get_models():
    """Returns available LLM reasoning models."""
    return {"models": AVAILABLE_MODELS, "default": "gemini/gemini-3.1-flash-lite"}


@router.get("/capabilities")
async def get_capabilities():
    """Returns MCP Server capabilities matrix."""
    return mcp_server.get_capabilities()


@router.get("/tools")
async def list_tools(role: str = "property_manager"):
    """Lists MCP tools scoped by persona role."""
    return mcp_server.list_tools(role=role)


@router.get("/resources")
async def list_resources():
    """Lists MCP resources registered in the system."""
    return mcp_server.list_resources()


@router.get("/resource/read")
async def read_resource(uri: str = "realty://policies/lease_terms"):
    """Reads content of a specified MCP resource URI."""
    try:
        return mcp_server.read_resource(uri)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prompts")
async def list_prompts():
    """Lists predefined MCP prompt templates."""
    return mcp_server.list_prompts()


@router.get("/prompt/get")
async def get_prompt(
    name: str = "draft_lease_notice",
    tenant_email: str = "tarek.mahdy@cairomed.org",
    proposed_rent: str = "15000"
):
    """Retrieves formatted MCP prompt template."""
    try:
        return mcp_server.get_prompt(name, {"tenant_email": tenant_email, "proposed_rent": proposed_rent})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
