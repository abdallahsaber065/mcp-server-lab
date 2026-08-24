"""
State Graph Router — Native LangGraph with SQLite/SQLAlchemy Checkpoints
Supports:
  - Graph Discovery (/graphs)
  - Run / Resume (/run, /run/stream)
  - Snapshot & Checkpoint Time-Travel (/status, /history, /checkpoint/{step})
  - Time-Travel Rollback & State Patching (/rollback/{step})
"""
import json
import logging
import traceback
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger("state_graph.router")

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GraphCheckpoint
from db.session import get_async_db
from services.state_graph_service import StateGraphService
from state_graph.checkpoint import SQLAlchemyLangGraphCheckpointer
from state_graph.graphs.lease_flow import build_lease_flow_graph
from state_graph.graphs.maintenance_flow import build_maintenance_flow_graph
from state_graph.graphs.arrears_flow import build_arrears_flow_graph

try:
    from langgraph.types import Command
except Exception:
    Command = dict  # type: ignore

router = APIRouter(prefix="/api/state-graph", tags=["State Graph"])
checkpointer = SQLAlchemyLangGraphCheckpointer()

GRAPHS = {
    "commercial_lease_flow": build_lease_flow_graph(checkpointer),
    "maintenance_dispatch_flow": build_maintenance_flow_graph(checkpointer),
    "arrears_care_flow": build_arrears_flow_graph(checkpointer),
    # Backward compatibility aliases
    "renovation_permit_flow": build_maintenance_flow_graph(checkpointer),
    "rent_arrears_settlement_flow": build_arrears_flow_graph(checkpointer),
    "lease_flow": build_lease_flow_graph(checkpointer),
    "maintenance_flow": build_maintenance_flow_graph(checkpointer),
    "arrears_flow": build_arrears_flow_graph(checkpointer),
}


class RunGraphRequest(BaseModel):
    graph_id: str
    run_id: Optional[str] = None
    variables: Dict[str, Any] = {}
    resume_value: Optional[Dict[str, Any]] = None


def _resolve_graph(graph_id: str):
    canonical = StateGraphService.canonical_id(graph_id)
    return GRAPHS.get(canonical) or GRAPHS.get(graph_id)


@router.get("/graphs")
async def list_graphs():
    return {"status": "success", "graphs": StateGraphService.list_graphs()}


@router.post("/run")
async def run_graph_endpoint(req: RunGraphRequest):
    logger.info("POST /run graph_id=%s run_id=%s vars=%s resume=%s", req.graph_id, req.run_id, list(req.variables.keys()), bool(req.resume_value))
    graph = _resolve_graph(req.graph_id)
    if not graph:
        raise HTTPException(status_code=400, detail=f"Unknown graph '{req.graph_id}'")

    thread_id = req.run_id or f"run-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        if req.resume_value is not None:
            state_output = await graph.ainvoke(Command(resume=req.resume_value), config=config)
        else:
            state_output = await graph.ainvoke(req.variables, config=config)
    except Exception as e:
        logger.exception("Graph execution exception thread=%s: %s", thread_id, e)
        raise HTTPException(status_code=500, detail=f"{e}\n{traceback.format_exc()[:1500]}")

    snapshot = graph.get_state(config)
    is_paused = bool(snapshot.next) if snapshot else False
    status_str = "PAUSED_HITL" if is_paused else "COMPLETED"
    int_val = None
    if snapshot and snapshot.tasks:
        for t in snapshot.tasks:
            ints = getattr(t, "interrupts", []) or []
            if ints:
                first_i = ints[0]
                int_val = first_i.value if hasattr(first_i, "value") else first_i
                break

    return {
        "status": "success",
        "graph_status": status_str,
        "run_id": thread_id,
        "is_paused": is_paused,
        "next_nodes": list(snapshot.next) if snapshot else [],
        "values": snapshot.values if snapshot else state_output,
        "tasks": [t.interrupts for t in snapshot.tasks if getattr(t, "interrupts", None)] if snapshot else [],
        "pending_hitl": int_val,
        "raw_output": state_output,
    }



@router.post("/run/stream")
async def run_graph_stream(req: RunGraphRequest):
    logger.info("POST /run/stream graph_id=%s run_id=%s vars=%s resume=%s", req.graph_id, req.run_id, list(req.variables.keys()), bool(req.resume_value))
    graph = _resolve_graph(req.graph_id)
    if not graph:
        raise HTTPException(status_code=400, detail=f"Unknown graph '{req.graph_id}'")

    thread_id = req.run_id or f"run-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    async def event_gen():
        step = 0
        try:
            import asyncio
            stream_input = Command(resume=req.resume_value) if req.resume_value is not None else req.variables
            async for evt in graph.astream(stream_input, config=config):
                if isinstance(evt, dict):
                    for node_name, node_out in evt.items():
                        if node_name == "__interrupt__":
                            int_payload = node_out[0].value if node_out and hasattr(node_out[0], "value") else node_out
                            role_req = int_payload.get("role_required") if isinstance(int_payload, dict) else "admin"
                            target_node = "accountant_verification" if "accountant" in str(role_req) else ("engineer_approval" if "engineer" in str(role_req) else "executive_concession")
                            yield f"data: {json.dumps({'type': 'node_complete', 'node': target_node, 'status': 'PAUSE_HITL', 'pending_hitl': int_payload, 'step': step}, ensure_ascii=False)}\n\n"
                            yield f"data: {json.dumps({'type': 'final', 'graph_status': 'PAUSED_HITL', 'run_id': thread_id, 'pending_hitl': int_payload}, ensure_ascii=False)}\n\n"
                        else:
                            step += 1
                            yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'step': step}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.3)
                            vars_dict = node_out if isinstance(node_out, dict) else {}
                            yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name, 'status': 'CONTINUE', 'variables': vars_dict, 'step': step, 'message': f'Completed {node_name}'}, ensure_ascii=False)}\n\n"

            snap = graph.get_state(config)
            if snap and not snap.next:
                yield f"data: {json.dumps({'type': 'final', 'graph_status': 'COMPLETED', 'run_id': thread_id, 'variables': snap.values}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("Stream execution exception thread=%s: %s", thread_id, e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")



@router.get("/{run_id}")
async def get_state_graph_status(run_id: str, graph_id: Optional[str] = None, db: AsyncSession = Depends(get_async_db)):
    config = {"configurable": {"thread_id": run_id}}
    target_graphs = [_resolve_graph(graph_id)] if graph_id else [GRAPHS["commercial_lease_flow"], GRAPHS["maintenance_dispatch_flow"], GRAPHS["arrears_care_flow"]]

    for g in target_graphs:
        if g:
            try:
                snap = g.get_state(config)
                if snap and snap.values:
                    return {"status": "success", "run_id": run_id, "state": snap.values, "next": list(snap.next)}
            except Exception:
                pass

    state = await StateGraphService.aload_latest_state(db, run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return {"status": "success", "run_id": run_id, "state": state.model_dump()}


@router.get("/{run_id}/history")
async def get_state_graph_history(run_id: str, graph_id: Optional[str] = None, db: AsyncSession = Depends(get_async_db)):
    config = {"configurable": {"thread_id": run_id}}
    target_graphs = [_resolve_graph(graph_id)] if graph_id else [GRAPHS["commercial_lease_flow"], GRAPHS["maintenance_dispatch_flow"], GRAPHS["arrears_care_flow"]]

    for g in target_graphs:
        if g:
            try:
                history = []
                for snap in g.get_state_history(config):
                    history.append({
                        "checkpoint_id": snap.config["configurable"].get("checkpoint_id"),
                        "step": snap.metadata.get("step", 0),
                        "node": snap.metadata.get("node") or snap.metadata.get("source", "node"),
                        "values": snap.values,
                        "next": list(snap.next),
                    })
                if history:
                    return {"status": "success", "run_id": run_id, "checkpoints": history}
            except Exception:
                pass

    stmt = select(GraphCheckpoint).where(GraphCheckpoint.run_id == run_id).order_by(GraphCheckpoint.step_number.asc())
    rows = (await db.scalars(stmt)).all()
    checkpoints = [
        {"checkpoint_id": r.checkpoint_id, "step": r.step_number, "node": r.node_name, "status": r.status}
        for r in rows
    ]
    return {"status": "success", "run_id": run_id, "checkpoints": checkpoints}


@router.get("/{run_id}/checkpoint/{step}")
async def get_checkpoint_at_step(run_id: str, step: int, graph_id: Optional[str] = None, db: AsyncSession = Depends(get_async_db)):
    config = {"configurable": {"thread_id": run_id}}
    target_graphs = [_resolve_graph(graph_id)] if graph_id else [GRAPHS["commercial_lease_flow"], GRAPHS["maintenance_dispatch_flow"], GRAPHS["arrears_care_flow"]]

    for g in target_graphs:
        if g:
            try:
                for snap in g.get_state_history(config):
                    if snap.metadata.get("step") == step:
                        return {"status": "success", "run_id": run_id, "step": step, "values": snap.values}
            except Exception:
                pass

    stmt = select(GraphCheckpoint).where(GraphCheckpoint.run_id == run_id, GraphCheckpoint.step_number == step).limit(1)
    row = (await db.scalars(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Checkpoint step {step} for run '{run_id}' not found.")
    state = json.loads(row.state_json)
    return {"status": "success", "run_id": run_id, "step": step, "checkpoint_id": row.checkpoint_id, "node": row.node_name, "state": state}


@router.post("/{run_id}/rollback/{step}")
async def rollback_to_step(run_id: str, step: int, graph_id: Optional[str] = None):
    config = {"configurable": {"thread_id": run_id}}
    target_graphs = [_resolve_graph(graph_id)] if graph_id else [GRAPHS["commercial_lease_flow"], GRAPHS["maintenance_dispatch_flow"], GRAPHS["arrears_care_flow"]]

    for g in target_graphs:
        if g:
            try:
                target_snap = None
                for snap in g.get_state_history(config):
                    if snap.metadata.get("step") == step:
                        target_snap = snap
                        break
                if target_snap is not None:
                    g.update_state(target_snap.config, target_snap.values)
                    int_val = None
                    if target_snap.tasks:
                        for t in target_snap.tasks:
                            ints = getattr(t, "interrupts", []) or []
                            if ints:
                                first_i = ints[0]
                                int_val = first_i.value if hasattr(first_i, "value") else first_i
                                break
                    return {
                        "status": "success",
                        "run_id": run_id,
                        "rolled_back_to": step,
                        "node": target_snap.metadata.get("node") or target_snap.metadata.get("source", "node"),
                        "state": target_snap.values,
                        "next": list(target_snap.next),
                        "tasks": [t.interrupts for t in target_snap.tasks if getattr(t, "interrupts", None)],
                        "pending_hitl": int_val,
                        "target_config": target_snap.config
                    }
            except Exception:
                pass

    raise HTTPException(status_code=404, detail=f"Checkpoint step {step} for run '{run_id}' not found.")


