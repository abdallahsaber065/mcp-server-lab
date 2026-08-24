"""Logs Router — tail platform.log and per-run graph traces for debugging."""
import pathlib
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/logs", tags=["Logs & Debugging"])
LOG_FILE = pathlib.Path(__file__).resolve().parent.parent.parent / "logs" / "platform.log"

@router.get("")
async def tail_logs(lines: int = Query(200, ge=1, le=2000), level: Optional[str] = None, graph_id: Optional[str] = None, run_id: Optional[str] = None):
    """Tail last N lines of platform.log, optionally filtered."""
    if not LOG_FILE.exists():
        return {"status": "empty", "lines": [], "path": str(LOG_FILE)}
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    filtered = all_lines
    if level:
        lvl = level.upper()
        filtered = [l for l in filtered if f"[{lvl}]" in l or lvl in l]
    if graph_id:
        filtered = [l for l in filtered if graph_id in l]
    if run_id:
        filtered = [l for l in filtered if run_id in l]
    tail = filtered[-lines:]
    return {"status": "success", "path": str(LOG_FILE), "total_lines": len(all_lines), "returned": len(tail), "lines": [l.rstrip("\n") for l in tail]}

@router.get("/graph/{run_id}")
async def graph_trace(run_id: str):
    """Combined trace for one run: checkpoints + recent log lines."""
    # Checkpoints via LangGraph
    checkpoints = []
    try:
        from web.routers.state_graph import GRAPHS
        graph = GRAPHS.get("commercial_lease_flow")
        cfg = {"configurable": {"thread_id": run_id}}
        for snap in graph.get_state_history(cfg):
            checkpoints.append({"step": snap.metadata.get("step"), "next": list(snap.next), "values_keys": list(snap.values.keys()) if isinstance(snap.values, dict) else []})
            if len(checkpoints) >= 20:
                break
    except Exception:
        pass
    log_lines = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                log_lines = [l.rstrip("\n") for l in f.readlines() if run_id in l][-80:]
        except Exception:
            pass
    return {"run_id": run_id, "checkpoints": checkpoints, "log_lines": log_lines}
