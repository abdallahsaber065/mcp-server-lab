"""
Main Application Entrypoint (web/app.py)
Modular, decoupled FastAPI gateway routing through dedicated domain routers.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure root workspace is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv()

from db.session import init_async_db
from web.routers import (
    admin_router,
    auth_router,
    chat_router,
    leases_router,
    maintenance_router,
    mcp_protocol_router,
    memory_router,
    properties_router,
    showcase_router,
    state_graph_router,
)

logger = logging.getLogger("cornerstone_platform")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and graceful shutdown."""
    logger.info("Starting Cornerstone Autonomous Realty MCP Server...")
    await init_async_db()
    yield
    logger.info("Cornerstone Autonomous Realty MCP Server shutting down.")


app = FastAPI(
    title="Cornerstone Realty Group — MCP Autonomous Platform",
    description="Enterprise Multi-Agent Realty Platform with MCP Protocol, RAG & Memory Architectures",
    version="4.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular domain routers
app.include_router(auth_router)
app.include_router(properties_router)
app.include_router(leases_router)
app.include_router(maintenance_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(mcp_protocol_router)
app.include_router(showcase_router)
app.include_router(state_graph_router)
app.include_router(admin_router)

# Mount frontend production dist assets
dist_dir = os.path.join(os.path.dirname(__file__), "dist")
static_dir = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Fallback handler serving Single Page Application index.html."""
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return {"error": "Endpoint not found"}

    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)

    static_index = os.path.join(static_dir, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)

    return {"message": "Cornerstone Autonomous Realty Platform API"}


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
