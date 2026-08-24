"""
State Graph Background Runner — native LangGraph, full logging, persistent notify.
"""
import asyncio
import json
import logging
import traceback
import uuid
from typing import Dict, Any, Optional

from db.session import AsyncSessionLocal
from db.repositories.chat_repo import AsyncChatRepository
from services.notification_service import NotificationService
from services.state_graph_service import StateGraphService

logger = logging.getLogger("state_graph.background")
logger.setLevel(logging.INFO)
# Use root handlers from web/app.py (platform.log + stdout); do not add duplicate handler
logger.propagate = True

CUSTOMER_MESSAGES = {
    "commercial_lease_flow": {
        "launch": "Your lease request for {unit_label} has been received. Our team is reviewing your details and verifying the documents — you’ll be updated here as soon as the next step is ready.",
        "accountant": "Your documents for {unit_label} are now with our accounting team for verification. We’ll notify you once the review is complete.",
        "executive": "Your lease for {unit_label} is awaiting final approval from our executive team. We’ll let you know the decision shortly.",
        "completed": "Great news — your lease for {unit_label} has been approved and activated. Our team will contact you with next steps.",
        "rejected": "Your lease request for {unit_label} was not approved at this time. Please contact our leasing team for alternatives.",
        "failed": "We encountered an issue processing your lease for {unit_label}. Our support team has been notified and will reach out shortly.",
    },
    "renovation_permit_flow": {
        "launch": "Your maintenance request for {location} has been received. We’re assessing the issue and sourcing the best repair options.",
        "engineer": "Your repair request for {location} is with our chief engineer for approval. We’ll update you once it’s authorized.",
        "tenant_wait": "Repair work for {location} is scheduled. We’ll notify you to confirm completion and share your feedback.",
        "completed": "Your maintenance for {location} is complete and the ticket has been closed. Thank you for your patience!",
        "failed": "We had a delay with your maintenance for {location}. We’ve assigned an alternate contractor and will update you soon.",
    },
    "maintenance_dispatch_flow": {
        "launch": "Your maintenance request for {location} has been received. We’re assessing the issue and sourcing the best repair options.",
        "engineer": "Your repair request for {location} is with our chief engineer for approval. We’ll update you once it’s authorized.",
        "tenant_wait": "Repair work for {location} is scheduled. We’ll notify you to confirm completion and share your feedback.",
        "completed": "Your maintenance for {location} is complete and the ticket has been closed. Thank you for your patience!",
        "failed": "We had a delay with your maintenance for {location}. We’ve assigned an alternate contractor and will update you soon.",
    },
    "rent_arrears_settlement_flow": {
        "launch": "We’ve received your request for payment assistance. Our team is reviewing your account and preparing personalized settlement options.",
        "tenant_choice": "We’ve prepared settlement options for your account. Please review them here and let us know your preference — we’re here to help.",
        "counsel": "Your selected plan is now with our legal and finance team for final review. We’ll confirm activation shortly.",
        "completed": "Your payment plan has been activated. You’ll receive the updated schedule and next steps in this chat.",
        "failed": "We couldn’t finalize your plan automatically. Our team will contact you directly to assist further.",
    },
    "arrears_care_flow": {
        "launch": "We’ve received your request for payment assistance. Our team is reviewing your account and preparing personalized settlement options.",
        "tenant_choice": "We’ve prepared settlement options for your account. Please review them here and let us know your preference — we’re here to help.",
        "counsel": "Your selected plan is now with our legal and finance team for final review. We’ll confirm activation shortly.",
        "completed": "Your payment plan has been activated. You’ll receive the updated schedule and next steps in this chat.",
        "failed": "We couldn’t finalize your plan automatically. Our team will contact you directly to assist further.",
    },
}

def _unit_label(variables: Dict[str, Any]) -> str:
    unit = variables.get("unit_id") or variables.get("unit_number") or "your unit"
    if isinstance(unit, int):
        return f"Unit {unit}"
    return str(unit)

def _customer_message(graph_id: str, status: str, node: str, variables: Dict[str, Any]) -> str:
    tpl = CUSTOMER_MESSAGES.get(graph_id, {}) or CUSTOMER_MESSAGES.get(StateGraphService.canonical_id(graph_id), {})
    unit_label = _unit_label(variables)
    location = variables.get("location") or variables.get("property_name") or "your property"
    # HITL branch uses node name
    if status in ("PAUSED_HITL", "AWAITING_WEBHOOK") or (node and status not in ("COMPLETED", "FAILED_TICKET")):
        if "commercial_lease_flow" in graph_id or graph_id == "commercial_lease_flow":
            if "accountant" in (node or ""):
                return tpl.get("accountant", "").format(unit_label=unit_label, location=location)
            if "executive" in (node or "").lower():
                return tpl.get("executive", "").format(unit_label=unit_label, location=location)
        if "maintenance" in graph_id or "renovation" in graph_id:
            if "engineer" in (node or ""):
                return tpl.get("engineer", "").format(location=location, unit_label=unit_label)
            if "tenant" in (node or "").lower():
                return tpl.get("tenant_wait", "").format(location=location, unit_label=unit_label)
        if "arrears" in graph_id or "rent_arrears" in graph_id:
            if "await_tenant" in (node or ""):
                return tpl.get("tenant_choice", "").format(location=location, unit_label=unit_label)
            if "counsel" in (node or "") or "finance" in (node or "") or "legal" in (node or ""):
                return tpl.get("counsel", "").format(location=location, unit_label=unit_label)
        return f"Your request for {unit_label if 'commercial_lease' in graph_id else location} is awaiting the next review step. We’ll notify you as soon as it’s ready."
    if status == "COMPLETED":
        return tpl.get("completed", f"Your request for {unit_label if 'commercial_lease' in graph_id else location} has been completed. Thank you!").format(unit_label=unit_label, location=location)
    if status in ("FAILED_TICKET", "failed"):
        return tpl.get("failed", f"We had an issue with your request for {location}. Our team will follow up shortly.").format(unit_label=unit_label, location=location)
    if status == "launch":
        return tpl.get("launch", "").format(unit_label=unit_label, location=location)
    return ""

async def run_graph_in_background(
    run_id: str,
    graph_id: str,
    variables: Dict[str, Any],
    user_id: Optional[int],
    session_id: str,
):
    """Native LangGraph background runner with full logging and durable HITL/ticket paths."""
    if not run_id:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
    variables = dict(variables or {})
    variables["origin_user_id"] = user_id
    variables["origin_session_id"] = session_id
    variables["origin_graph_id"] = graph_id
    canonical = StateGraphService.canonical_id(graph_id)
    logger.info("BG start run_id=%s graph_id=%s canonical=%s session=%s user=%s vars=%s", run_id, graph_id, canonical, session_id, user_id, json.dumps({k: str(v)[:200] for k, v in variables.items()}, ensure_ascii=False))
    notified_keys = set()
    # Do NOT hold DB session during LLM/tool execution — only open for persist
    try:
        graph = StateGraphService.get_native_graph(canonical)
        config = {"configurable": {"thread_id": run_id}}
        logger.info("BG graph compiled run_id=%s nodes=%s", run_id, list(getattr(graph, "nodes", {}).keys()) if hasattr(graph, "nodes") else "native")
        stream_interrupt_payload = None
        # Stream native events — capture __interrupt__ for HITL detection
        try:
            async for evt in graph.astream(variables, config):
                logger.info("BG evt run_id=%s evt=%s", run_id, json.dumps(evt, ensure_ascii=False, default=str)[:1200])
                if isinstance(evt, dict) and "__interrupt__" in evt:
                    try:
                        raw = evt["__interrupt__"]
                        if isinstance(raw, (list, tuple)) and len(raw) > 0:
                            first = raw[0]
                            if isinstance(first, dict) and "value" in first:
                                stream_interrupt_payload = first["value"]
                            elif hasattr(first, "value"):
                                stream_interrupt_payload = first.value  # type: ignore
                            else:
                                stream_interrupt_payload = first
                        else:
                            stream_interrupt_payload = raw
                        logger.info("BG captured interrupt run_id=%s payload=%s", run_id, json.dumps(stream_interrupt_payload, ensure_ascii=False, default=str)[:600] if stream_interrupt_payload else "None")
                    except Exception as ie:
                        logger.warning("BG interrupt parse failed run_id=%s err=%s", run_id, ie)
                    continue
                if isinstance(evt, dict):
                    for node_name, node_out in evt.items():
                        if node_name == "__interrupt__":
                            continue
                        logger.info("BG node_complete run_id=%s node=%s out_keys=%s", run_id, node_name, list(node_out.keys()) if isinstance(node_out, dict) else str(type(node_out)))
        except Exception as stream_err:
            from langgraph.errors import GraphInterrupt  # type: ignore
            if isinstance(stream_err, GraphInterrupt):
                logger.info("BG interrupt exception run_id=%s interrupts=%s", run_id, getattr(stream_err, "args", [])[:1])
                # Try to extract payload from exception
                try:
                    if stream_err.args and isinstance(stream_err.args[0], list):
                        stream_interrupt_payload = stream_err.args[0][0].get("value") if isinstance(stream_err.args[0][0], dict) else stream_err.args[0][0]
                except Exception:
                    pass
            else:
                raise

        # After stream, inspect snapshot + stream interrupt to decide PAUSED_HITL vs COMPLETED
        snapshot = graph.get_state(config)
        snapshot_next = list(snapshot.next) if snapshot and snapshot.next else []
        snapshot_values = snapshot.values if snapshot and snapshot.values else {}
        snapshot_tasks = snapshot.tasks if snapshot else []
        has_interrupt = stream_interrupt_payload is not None
        interrupt_payload = stream_interrupt_payload
        if not has_interrupt:
            try:
                if isinstance(snapshot_values, dict) and "__interrupt__" in snapshot_values:
                    has_interrupt = True
                    interrupt_payload = snapshot_values["__interrupt__"]
                elif snapshot_tasks and any(getattr(t, "interrupts", None) for t in snapshot_tasks):
                    has_interrupt = True
                    for t in snapshot_tasks:
                        if getattr(t, "interrupts", None):
                            interrupt_payload = t.interrupts[0].value
                            break
            except Exception:
                pass
        logger.info("BG snapshot run_id=%s next=%s has_interrupt=%s values_keys=%s tasks=%s", run_id, snapshot_next, has_interrupt, list(snapshot_values.keys())[:14] if isinstance(snapshot_values, dict) else str(type(snapshot_values)), len(snapshot_tasks) if snapshot_tasks else 0)

        status = "UNKNOWN"
        node = ""
        pending_hitl = None
        customer_msg = ""
        if snapshot_next or has_interrupt:
            if snapshot_next:
                node = snapshot_next[0]
            elif isinstance(interrupt_payload, list) and interrupt_payload:
                raw_role = str(interrupt_payload[0].get("role_required", "")) if isinstance(interrupt_payload[0], dict) else ""
                if "accountant" in raw_role:
                    node = "accountant_verification"
                elif "executive" in raw_role:
                    node = "executive_concession"
                elif "engineer" in raw_role:
                    node = "engineer_approval"
                elif "legal" in raw_role or "counsel" in raw_role or "finance" in raw_role:
                    node = "finance_legal_approval"
                else:
                    node = "awaiting_review"
            elif isinstance(interrupt_payload, dict):
                raw_role = str(interrupt_payload.get("role_required", ""))
                if "accountant" in raw_role:
                    node = "accountant_verification"
                elif "executive" in raw_role:
                    node = "executive_concession"
                elif "engineer" in raw_role:
                    node = "engineer_approval"
                elif "legal" in raw_role or "counsel" in raw_role or "finance" in raw_role:
                    node = "finance_legal_approval"
                elif "tenant" in raw_role:
                    node = "await_tenant_response" if "arrears" in canonical else "tenant_rating"
                else:
                    node = "awaiting_review"
            # Fallback: infer from graph_id if still empty
            if not node:
                node = {"commercial_lease_flow": "accountant_verification", "maintenance_dispatch_flow": "engineer_approval", "arrears_care_flow": "await_tenant_response"}.get(canonical, "awaiting_review")
            status = "PAUSED_HITL"
            try:
                if stream_interrupt_payload is not None:
                    pending_hitl = stream_interrupt_payload
                elif snapshot_tasks and getattr(snapshot_tasks[0], "interrupts", None):
                    pending_hitl = snapshot_tasks[0].interrupts[0].value
                elif has_interrupt and interrupt_payload:
                    pending_hitl = interrupt_payload[0] if isinstance(interrupt_payload, list) else interrupt_payload
                else:
                    pending_hitl = snapshot_values.get("pending_hitl") if isinstance(snapshot_values, dict) else None
            except Exception:
                pending_hitl = None
            customer_msg = _customer_message(canonical, status, node, snapshot_values if isinstance(snapshot_values, dict) else variables)
            logger.info("BG PAUSED_HITL run_id=%s node=%s pending=%s msg=%s", run_id, node, json.dumps(pending_hitl, ensure_ascii=False, default=str)[:600] if pending_hitl else "None", customer_msg[:200])
        else:
            if isinstance(snapshot_values, dict) and snapshot_values.get("status") == "COMPLETED":
                status = "COMPLETED"
            elif not snapshot_next and snapshot_values:
                status = "COMPLETED"
            else:
                status = "COMPLETED"
            customer_msg = _customer_message(canonical, status, node, snapshot_values if isinstance(snapshot_values, dict) else variables)
            logger.info("BG COMPLETED run_id=%s msg=%s", run_id, customer_msg[:200])

        if customer_msg and status in ("PAUSED_HITL", "COMPLETED"):
            dedup_key = f"{run_id}:{node}:{status}"
            if dedup_key not in notified_keys:
                notified_keys.add(dedup_key)
                notify_payload = {
                    "type": "state_graph_update",
                    "run_id": run_id,
                    "graph_id": canonical,
                    "session_id": session_id,
                    "status": status,
                    "node": node,
                    "message": customer_msg,
                    "variables": snapshot_values if isinstance(snapshot_values, dict) else variables,
                    "pending_hitl": pending_hitl,
                }
                logger.info("BG notify run_id=%s status=%s node=%s", run_id, status, node)
                async with AsyncSessionLocal() as db:
                    repo = AsyncChatRepository(db)
                    task_id = None
                    if status == "PAUSED_HITL":
                        try:
                            from services.hitl_service import HITLService
                            reason_str = (
                                pending_hitl.get("reason")
                                if isinstance(pending_hitl, dict) and pending_hitl.get("reason")
                                else f"Sign-off required at node '{node}'"
                            )
                            task_payload = {
                                **(pending_hitl if isinstance(pending_hitl, dict) else {}),
                                "session_id": session_id,
                                "user_id": user_id,
                                "node": node,
                                "variables": snapshot_values if isinstance(snapshot_values, dict) else variables,
                            }
                            task_id = await HITLService.acreate_task(
                                session=db,
                                run_id=run_id,
                                graph_id=canonical,
                                node_name=node,
                                reason=reason_str,
                                payload=task_payload,
                            )
                            notify_payload["task_id"] = task_id
                            logger.info("BG HITLTask saved to DB task_id=%s run_id=%s node=%s", task_id, run_id, node)
                        except Exception as he:
                            logger.warning("BG HITLTask creation failed run_id=%s err=%s", run_id, he)
                    try:
                        await repo.save_chat_message(session_id=session_id, msg_type="state_graph_update", content=json.dumps(notify_payload, ensure_ascii=False, default=str), user_id=user_id)
                        logger.info("BG persisted state_graph_update session=%s", session_id)
                    except Exception as e:
                        logger.exception("BG persist failed run_id=%s err=%s", run_id, e)
                    if user_id is not None:
                        await NotificationService.publish(user_id, notify_payload)
                    # Role-targeted HITL notify
                    try:
                        target_role = None
                        if "accountant" in (node or ""):
                            target_role = "accountant"
                        elif "engineer" in (node or ""):
                            target_role = "chief_engineer"
                        elif "counsel" in (node or "") or "finance" in (node or "") or "legal" in (node or ""):
                            target_role = "legal_counsel"
                        elif "executive" in (node or ""):
                            target_role = "executive_admin"
                        if target_role:
                            from sqlalchemy import text as _text
                            async with AsyncSessionLocal() as _rdb:
                                res = await _rdb.execute(_text("SELECT tenant_id FROM tenants WHERE role=:r LIMIT 10"), {"r": target_role})
                                for row in res.fetchall():
                                    rid = row[0]
                                    if rid != user_id:
                                        await NotificationService.publish(int(rid), notify_payload)
                                        logger.info("BG role notify run_id=%s role=%s rid=%s", run_id, target_role, rid)
                    except Exception as e:
                        logger.warning("BG role notify failed run_id=%s err=%s", run_id, e)

    except Exception as e:
        logger.exception("BG FAILED_TICKET run_id=%s graph_id=%s err=%s trace=%s", run_id, graph_id, e, traceback.format_exc()[:2000])
        # Persist ticket in DB (distinct from HITL)
        try:
            from db.session import AsyncSessionLocal as _ASL2
            from services.ticket_service import TicketService
            async with _ASL2() as tdb:
                try:
                    await TicketService.aopen_ticket(tdb, run_id, canonical, (node if 'node' in locals() and node else "background"), e, variables)  # type: ignore[arg-type]
                    await tdb.commit()
                    logger.info("BG ticket created run_id=%s", run_id)
                except Exception as te:
                    logger.warning("BG ticket create failed run_id=%s err=%s", run_id, te)
        except Exception:
            pass
        try:
            async with AsyncSessionLocal() as db2:
                repo2 = AsyncChatRepository(db2)
                customer_msg = _customer_message(canonical, "FAILED_TICKET", node if 'node' in locals() else "", variables)
                err_evt = {
                    "type": "state_graph_failed",
                    "run_id": run_id,
                    "graph_id": canonical,
                    "session_id": session_id,
                    "status": "FAILED_TICKET",
                    "message": customer_msg,
                    "error": str(e),
                    "trace": traceback.format_exc()[:1500],
                }
                await repo2.save_chat_message(session_id=session_id, msg_type="state_graph_update", content=json.dumps(err_evt, ensure_ascii=False), user_id=user_id)
                if user_id is not None:
                    await NotificationService.publish(user_id, err_evt)
                logger.info("BG FAILED_TICKET notified run_id=%s", run_id)
        except Exception as ne:
            logger.exception("BG FAILED_TICKET notify failed run_id=%s err=%s", run_id, ne)

def fire_and_forget_graph(
    run_id: str,
    graph_id: str,
    variables: Dict[str, Any],
    user_id: Optional[int],
    session_id: str,
):
    """Non-blocking launch: runs in daemon thread so main event loop (SSE/chat) never blocks on LLM/tool work."""
    logger.info("BG fire_and_forget run_id=%s graph_id=%s session=%s", run_id, graph_id, session_id)
    import threading

    def _thread_target():
        try:
            asyncio.run(run_graph_in_background(run_id, graph_id, variables, user_id, session_id))
        except Exception as e:
            logger.exception("BG thread failed run_id=%s err=%s", run_id, e)

    t = threading.Thread(target=_thread_target, daemon=True, name=f"bg-{run_id}")
    t.start()
    logger.info("BG thread started run_id=%s thread=%s", run_id, t.name)
