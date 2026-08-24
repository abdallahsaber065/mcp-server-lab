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
    notifications_router,
    properties_router,
    showcase_router,
    state_graph_router,
    logs_router,
)

import pathlib
LOG_DIR = pathlib.Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "platform.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
    force=True,
)
logger = logging.getLogger("cornerstone_platform")
logger.info("Logging to %s", LOG_FILE)


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
app.include_router(notifications_router)
app.include_router(logs_router)

# Mount frontend production dist assets and static directories
dist_dir = os.path.join(os.path.dirname(__file__), "dist")
static_dir = os.path.join(os.path.dirname(__file__), "static")
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "platform", "public")

# 1. Assets from Vite bundle
if os.path.exists(os.path.join(dist_dir, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

# 2. Images directory (dist/images or platform/public/images or static/images)
if os.path.exists(os.path.join(dist_dir, "images")):
    app.mount("/images", StaticFiles(directory=os.path.join(dist_dir, "images")), name="dist_images")
elif os.path.exists(os.path.join(public_dir, "images")):
    app.mount("/images", StaticFiles(directory=os.path.join(public_dir, "images")), name="public_images")
elif os.path.exists(os.path.join(static_dir, "images")):
    app.mount("/images", StaticFiles(directory=os.path.join(static_dir, "images")), name="static_images")

# 3. Receipts directory
if os.path.exists(os.path.join(static_dir, "uploads", "receipts")):
    app.mount("/receipts", StaticFiles(directory=os.path.join(static_dir, "uploads", "receipts")), name="receipts_uploads")
elif os.path.exists(os.path.join(dist_dir, "receipts")):
    app.mount("/receipts", StaticFiles(directory=os.path.join(dist_dir, "receipts")), name="dist_receipts")
elif os.path.exists(os.path.join(public_dir, "receipts")):
    app.mount("/receipts", StaticFiles(directory=os.path.join(public_dir, "receipts")), name="public_receipts")

# 4. Uploads directory
if os.path.exists(os.path.join(static_dir, "uploads")):
    app.mount("/uploads", StaticFiles(directory=os.path.join(static_dir, "uploads")), name="uploads")

# 5. Static root
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Fallback handler serving Single Page Application index.html or raw static assets."""
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return {"error": "Endpoint not found"}

    # 1. Check if the exact requested file exists in dist_dir (e.g. images/properties/1.jpg, favicon.ico)
    file_in_dist = os.path.join(dist_dir, full_path)
    if os.path.isfile(file_in_dist):
        return FileResponse(file_in_dist)

    # 2. Check if the file exists in static_dir (e.g. static/images, receipts, uploads)
    file_in_static = os.path.join(static_dir, full_path)
    if os.path.isfile(file_in_static):
        return FileResponse(file_in_static)

    # 3. Check stripped prefix e.g. "static/..." or "receipts/..." or "images/..."
    if full_path.startswith("static/"):
        file_sub = os.path.join(static_dir, full_path[len("static/"):])
        if os.path.isfile(file_sub):
            return FileResponse(file_sub)

    if full_path.startswith("receipts/"):
        for r_dir in [
            os.path.join(static_dir, "uploads", "receipts"),
            os.path.join(static_dir, "uploads"),
            os.path.join(dist_dir, "receipts"),
            os.path.join(public_dir, "receipts"),
        ]:
            r_path = os.path.join(r_dir, os.path.basename(full_path))
            if os.path.isfile(r_path):
                return FileResponse(r_path)

    if full_path.startswith("images/"):
        for i_dir in [
            dist_dir,
            public_dir,
            static_dir,
        ]:
            i_path = os.path.join(i_dir, full_path)
            if os.path.isfile(i_path):
                return FileResponse(i_path)

    # 4. If an image or media asset was requested by file extension but not found, DO NOT return index.html!
    ext = os.path.splitext(full_path)[1].lower()
    if ext in {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".ico", ".pdf", ".map", ".css", ".js", ".woff", ".woff2", ".ttf"}:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Static asset not found", "path": full_path}, status_code=404)

    # 5. Otherwise return SPA index.html for client-side routing
    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)

    static_index = os.path.join(static_dir, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)

    return {"message": "Cornerstone Autonomous Realty Platform API"}


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True, timeout_graceful_shutdown=2)

