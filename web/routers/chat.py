"""
Chat Router (web/routers/chat.py)
Handles chat session lifecycle, multi-turn message persistence, SSE agent streaming, and elicitation.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import os
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent.planning_agent import PlanningAgent
from db.models import ChatMessage, ChatSession
from db.repositories.chat_repo import AsyncChatRepository
from db.session import get_async_db
from mcp_server.server import CornerstoneMCPServer
from memory.consolidation import SemanticMemoryStore
from memory.episodic_store import EpisodicStore
from rag.agentic_rag import AgenticRAGRouter
from rag.graph_rag import PropertyPolicyKnowledgeGraph
from rag.hybrid_rag import HybridSearchEngine
from rag.naive_rag import naive_rag_search
from rag.pgvector_rag import pgvector_rag_store
from rag.pipeline import build_and_seed_vector_store
from rag.self_rag import SelfRAGVerifier
from web.deps import get_optional_user
from web.llm_engine import MCPLLMEngine, create_langchain_llm
from web.services.chat import build_memory_payload, build_rag_payload, dispatch_confirmed_action
from web.services.prompt_builder import build_system_prompt

logger = logging.getLogger("mcp_chat_router")

router = APIRouter(prefix="/api", tags=["Chat & Agent Streaming"])

mcp_server = CornerstoneMCPServer()
llm_engine = MCPLLMEngine(default_model="gemini/gemini-3.1-flash-lite")

# RAG Engines
rag_store = build_and_seed_vector_store()
hybrid_engine = HybridSearchEngine(vector_store=rag_store)
agentic_router = AgenticRAGRouter(hybrid_engine=hybrid_engine)
graph_rag = PropertyPolicyKnowledgeGraph()
self_rag_verifier = SelfRAGVerifier()

# Memory Stores (Unified central database)
episodic_store = EpisodicStore(db_path="central")
semantic_store = SemanticMemoryStore(db_path="central")


class CreateSessionRequest(BaseModel):
    title: str = "New conversation"
    role: Optional[str] = None


class UpdateSessionRoleRequest(BaseModel):
    role: str


class UpdateSessionTitleRequest(BaseModel):
    title: str


class StreamChatRequest(BaseModel):
    session_id: str
    user_message: Optional[str] = None
    message: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    model: str = "gemini/gemini-3.1-flash-lite"
    role: Optional[str] = None
    user_email: Optional[str] = None
    tenant_id: Optional[int] = None
    rag_strategy: str = "naive"
    chat_mode: str = "standard"
    conversation_history: List[Dict[str, Any]] = []

    def get_message(self) -> str:
        return self.user_message or self.message or ""

    def get_images(self) -> List[str]:
        if self.image_urls:
            return self.image_urls
        if self.image_url:
            return [self.image_url]
        return []


class ElicitationResponse(BaseModel):
    session_id: str
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12


@router.post("/chat/upload")
async def upload_chat_file(files: Optional[List[UploadFile]] = File(None), file: Optional[UploadFile] = File(None)):
    """Upload one or multiple receipt photos, bank slips, or property inspection images for multimodal agent verification."""
    os.makedirs("web/static/uploads/receipts", exist_ok=True)
    incoming_files = files or ([file] if file else [])
    if not incoming_files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    saved_urls = []
    saved_names = []

    for f in incoming_files:
        clean_name = f"{uuid.uuid4().hex[:8]}_{f.filename.replace(' ', '_')}"
        target_path = os.path.join("web/static/uploads/receipts", clean_name)
        with open(target_path, "wb") as buffer:
            content = await f.read()
            buffer.write(content)
        public_url = f"/static/uploads/receipts/{clean_name}"
        saved_urls.append(public_url)
        saved_names.append(clean_name)

    return {
        "status": "success",
        "image_urls": saved_urls,
        "image_url": saved_urls[0] if saved_urls else "",
        "filenames": saved_names
    }


@router.get("/chats")
async def list_chats(request: Request, db: AsyncSession = Depends(get_async_db)):
    """List chat sessions for the currently authenticated user (scoped by JWT)."""
    user = await get_optional_user(request, db)
    user_id = user.tenant_id if user else None
    repo = AsyncChatRepository(db)
    return await repo.get_all_chat_sessions(user_id=user_id)


@router.post("/chats")
async def create_chat(req: CreateSessionRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    """Create a new persistent chat session in the database, owned by the authenticated user."""
    user = await get_optional_user(request, db)
    user_id = user.tenant_id if user else None
    effective_role = req.role or (user.role if user else "prospect")
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    repo = AsyncChatRepository(db)
    return await repo.create_chat_session(session_id=session_id, title=req.title, role=effective_role, user_id=user_id)


@router.get("/chats/{session_id}")
async def get_chat(session_id: str, db: AsyncSession = Depends(get_async_db)):
    """Retrieve full message history and role for a chat session."""
    repo = AsyncChatRepository(db)
    messages = await repo.get_chat_messages(session_id)
    role = await repo.get_chat_session_role(session_id)
    return {"session_id": session_id, "role": role, "messages": messages}


@router.patch("/chats/{session_id}/title")
async def update_session_title(session_id: str, req: UpdateSessionTitleRequest, db: AsyncSession = Depends(get_async_db)):
    """Update title of a chat session."""
    repo = AsyncChatRepository(db)
    success = await repo.update_chat_session_title(session_id, req.title)
    return {"status": "success" if success else "error", "session_id": session_id, "title": req.title}


@router.patch("/chats/{session_id}/role")
async def update_session_role(session_id: str, req: UpdateSessionRoleRequest, db: AsyncSession = Depends(get_async_db)):
    """Update active persona role for a chat session."""
    repo = AsyncChatRepository(db)
    success = await repo.update_chat_session_role(session_id, req.role)
    return {"status": "success" if success else "error", "session_id": session_id, "role": req.role}


@router.delete("/chats/{session_id}")
async def delete_chat(session_id: str, db: AsyncSession = Depends(get_async_db)):
    """Delete a chat session and all associated messages."""
    repo = AsyncChatRepository(db)
    success = await repo.delete_chat_session(session_id)
    return {"status": "success" if success else "error"}


@router.post("/chat/stream")
async def chat_stream_endpoint(req: StreamChatRequest, request: Request, db: AsyncSession = Depends(get_async_db)):
    """SSE streaming endpoint for multi-turn autonomous agent execution with multimodal vision support."""
    user = await get_optional_user(request, db)
    repo = AsyncChatRepository(db)
    msg_text = req.get_message()

    effective_email = req.user_email or (user.email if user else None)
    effective_tenant_id = req.tenant_id or (user.tenant_id if user else None)
    effective_role = req.role or (user.role if user else "prospect")

    # Retrieve prior history for LLM multi-turn context
    prior_messages = await repo.get_chat_messages(req.session_id)
    history_for_llm = []
    for m in prior_messages:
        if m.get("type") == "user" and m.get("content"):
            history_for_llm.append({"role": "user", "content": m["content"]})
        elif m.get("type") == "assistant" and m.get("content"):
            history_for_llm.append({"role": "assistant", "content": m["content"]})

    # Save user message to database (with multiple image references if provided)
    uploaded_images = req.get_images()
    saved_msg_content = msg_text
    if uploaded_images:
        images_md = "\n".join([f"![Uploaded Document]({url})" for url in uploaded_images])
        saved_msg_content = f"{msg_text}\n\n{images_md}" if msg_text else images_md

    await repo.update_chat_session_role(req.session_id, effective_role)
    await repo.save_chat_message(session_id=req.session_id, msg_type="user", content=saved_msg_content, user_id=effective_tenant_id)

    # Build dynamic, persona-grounded system prompt
    system_prompt = build_system_prompt(
        role=effective_role,
        user_email=effective_email,
        tenant_id=effective_tenant_id,
        semantic_store=semantic_store,
        episodic_store=episodic_store
    )

    # 1. Extract memory context payload
    memory_payload = build_memory_payload(
        tenant_id=effective_tenant_id,
        user_email=effective_email,
        semantic_store=semantic_store,
        episodic_store=episodic_store,
    )

    # 2. Inject RAG context based on selected strategy
    rag_snippet, self_rag_payload = build_rag_payload(
        msg_text=msg_text,
        rag_strategy=req.rag_strategy,
        rag_store=rag_store,
        hybrid_engine=hybrid_engine,
        agentic_router=agentic_router,
        graph_rag=graph_rag,
        pgvector_rag_store=pgvector_rag_store,
        role=effective_role,
        tenant_id=effective_tenant_id,
    )
    system_prompt += rag_snippet

    stream_gen = llm_engine.execute_agent_loop_stream(
        mcp_server_instance=mcp_server,
        user_message=msg_text,
        system_prompt=system_prompt,
        conversation_history=history_for_llm,
        model=req.model,
        role=req.role,
        image_urls=uploaded_images
    )

    async def sse_wrapper():
        full_assistant_text = ""

        # Graph-agent mode: bypass Standard RAG/memory, run intake + background
        is_graph_mode = req.chat_mode in ("lease_onboarding", "maintenance_tender", "arrears_mediation")
        if is_graph_mode:
            # Load existing slots and last run from history
            existing_slots = {}
            last_run_id = None
            last_graph_id = None
            for m in prior_messages:
                if m.get("type") == "state_graph_slots":
                    try:
                        c = json.loads(m.get("content", "{}"))
                        existing_slots.update(c.get("slots", {}))
                    except Exception:
                        pass
                if m.get("type") in ("state_graph_launching", "state_graph_update"):
                    try:
                        c = json.loads(m.get("content", "{}"))
                        if c.get("run_id"):
                            last_run_id = c.get("run_id")
                            last_graph_id = c.get("graph_id") or last_graph_id
                    except Exception:
                        pass
            # Progress/status query — synthesize whole-graph context via LLM (not canned), user-friendly not technical
            lower_msg = (msg_text or "").lower().strip()
            status_keywords = [
                "progress", "status", "stasut", "stauts", "statue", "where", "update", "how is",
                "what's happening", "whats happening", "where is my", "is it done", "how long",
                "when will", "follow up", "what happened", "state", "approved", "rejected"
            ]
            is_progress_query = any(kw in lower_msg for kw in status_keywords) or (last_run_id and any(q in lower_msg for q in ["?", "what", "is", "now", "هل", "ماذا", "أين", "حال"]))
            if is_progress_query and last_run_id:
                try:
                    from sqlalchemy import select as _select
                    from db.models import GraphCheckpoint as _GC
                    rows = (await db.scalars(_select(_GC).where(_GC.run_id == last_run_id).order_by(_GC.step_number.asc()))).all()
                    latest = rows[-1] if rows else None
                    if latest:
                        import json as _j2
                        latest_data = _j2.loads(latest.state_json) if isinstance(latest.state_json, str) else (latest.state_json or {})
                        checkpoint_obj = latest_data.get("checkpoint", {}) if isinstance(latest_data, dict) else {}
                        channel_vals = checkpoint_obj.get("channel_values", {}) if isinstance(checkpoint_obj, dict) else {}
                        variables = channel_vals or latest_data.get("variables", {}) or {}
                        pending = latest_data.get("pending_hitl") or checkpoint_obj.get("pending_hitl")
                        status = str(variables.get("status") or variables.get("lease_status") or latest.status)
                        node = latest.node_name

                        ans = None
                        try:
                            import litellm as _lit
                            sys_prompt = (
                                "You are Cornerstone Realty's concierge customer assistant. Summarize the request's current status in 2-3 short sentences, "
                                "warm, professional, and clear. Never mention internal node names, run_id, or graph_id. "
                                "If the lease was rejected or declined, explain politely that the proposed rate was not approved and offer alternatives. "
                                "If awaiting accounting or executive review, explain that the documents/concessions are currently being finalized. "
                                "Focus on what matters to the customer (unit, price, timeline, next step)."
                            )
                            user_prompt = (
                                f"Graph: {last_graph_id}, status: {status}, current step: {node}, "
                                f"key vars: {json.dumps({k: str(variables[k])[:100] for k in list(variables)[:8]}, ensure_ascii=False)}, "
                                f"pending: {json.dumps(pending, ensure_ascii=False) if pending else 'none'}. "
                                f"User asked: '{msg_text}'. Give an accurate, helpful update."
                            )
                            resp = await _lit.acompletion(
                                model="gemini/gemini-3.1-flash-lite",
                                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                                temperature=1.0,
                                max_tokens=260
                            )
                            ans = (resp.choices[0].message.content or "").strip()
                        except Exception as ex:
                            logger.warning("LLM progress synthesis fallback: %s", ex)
                            ans = None

                        if not ans:
                            unit = variables.get("unit_id", 301)
                            if status in ("REJECTED", "rejected") or variables.get("executive_decision") in ("REJECT", "REJECTED"):
                                ans = f"Your lease request for Unit {unit} was reviewed, but the proposed concession was not approved at this time. Our leasing team would be delighted to assist you with standard terms or explore alternative suites."
                            elif status in ("ACTIVE", "COMPLETED", "completed"):
                                ans = f"Great news! Your request for Unit {unit} has been **approved and finalized**. Our operations team is preparing the formal handover."
                            elif status in ("PAUSED_HITL", "AWAITING_WEBHOOK") or "accountant" in node or "executive" in node:
                                ans = f"Your request for Unit {unit} is currently with our management team for final review. We will notify you right here as soon as the review is complete."
                            else:
                                ans = f"Your request for Unit {unit} is progressing through the review stages. We are actively finalizing the details for you."

                        await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=ans)
                        yield f"data: {json.dumps({'type': 'token', 'content': ans}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'final_answer': ans}, ensure_ascii=False)}\n\n"
                        return
                    else:
                        ans = "I don’t see an active request for this chat yet. Would you like to explore available units or start an application?"
                        await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=ans)
                        yield f"data: {json.dumps({'type': 'token', 'content': ans}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'final_answer': ans}, ensure_ascii=False)}\n\n"
                        return
                except Exception as e:
                    ans = f"We are currently reviewing your request. Please check back shortly or check the timeline tab."
                    yield f"data: {json.dumps({'type': 'token', 'content': ans}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'final_answer': ans}, ensure_ascii=False)}\n\n"
                    return
            from services.chat_intake_service import ChatIntakeService
            from services.state_graph_background import run_graph_in_background
            logger.info("chat graph_mode=%s session=%s user=%s slots_in=%s msg=%.120s", req.chat_mode, req.session_id, effective_tenant_id, existing_slots, msg_text)
            intake = await ChatIntakeService.run_intake_turn(
                db, effective_tenant_id, req.session_id, req.chat_mode, history_for_llm, msg_text, uploaded_images, existing_slots
            )
            logger.info("chat intake out ready=%s slots=%s graph=%s", intake["ready_to_launch"], intake["slots"], intake["graph_id"])
            # Persist slots
            await repo.save_chat_message(session_id=req.session_id, msg_type="state_graph_slots", content=json.dumps({"mode": req.chat_mode, "slots": intake["slots"], "graph_id": intake["graph_id"]}, ensure_ascii=False))
            yield f"data: {json.dumps({'type': 'state_graph_slots', 'mode': req.chat_mode, 'slots': intake['slots'], 'graph_id': intake['graph_id']}, ensure_ascii=False)}\n\n"
            if not intake["ready_to_launch"]:
                # Ask for next slot
                q = intake["next_question"]
                await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=q)
                yield f"data: {json.dumps({'type': 'token', 'content': q}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'final_answer': q}, ensure_ascii=False)}\n\n"
                return
            else:
                # Ready to launch — fire background
                import uuid as _uuid
                run_id = f"run-{_uuid.uuid4().hex[:8]}"
                launch_vars = intake["launch_variables"] or {}
                # Ensure session and user tracking in variables
                launch_vars["origin_session_id"] = req.session_id
                launch_vars["origin_user_id"] = effective_tenant_id
                # Customer-service launch message — no technical IDs
                graph_labels = {
                    "commercial_lease_flow": "lease onboarding",
                    "renovation_permit_flow": "maintenance",
                    "rent_arrears_settlement_flow": "payment assistance",
                }
                label = graph_labels.get(intake['graph_id'], "request")
                launch_msg = f"Thank you! Your {label} request has been received and is now being reviewed by our team. We’ll update you right here when the next step is ready — you don’t need to stay in this chat or keep it open. You can also check progress anytime from your chat history." 
                await repo.save_chat_message(session_id=req.session_id, msg_type="state_graph_launching", content=json.dumps({"graph_id": intake["graph_id"], "run_id": run_id, "session_id": req.session_id, "variables": launch_vars}, ensure_ascii=False))
                yield f"data: {json.dumps({'type': 'state_graph_launching', 'graph_id': intake['graph_id'], 'run_id': run_id, 'session_id': req.session_id}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'content': launch_msg}, ensure_ascii=False)}\n\n"
                logger.info("chat launch graph=%s run_id=%s vars=%s", intake["graph_id"], run_id, json.dumps(launch_vars, ensure_ascii=False, default=str)[:800])
                # Fire-and-forget in daemon thread — never blocks SSE stream or event loop
                try:
                    from services.state_graph_background import fire_and_forget_graph
                    fire_and_forget_graph(run_id, intake["graph_id"], launch_vars, effective_tenant_id, req.session_id)
                    logger.info("chat background thread launched run_id=%s", run_id)
                except Exception as e:
                    logger.exception("chat background launch failed run_id=%s err=%s", run_id, e)
                await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=launch_msg)
                yield f"data: {json.dumps({'type': 'done', 'final_answer': launch_msg}, ensure_ascii=False)}\n\n"
                return

        # Step 1: Run Mistral Intent Classification Router (Standard mode)
        intent_res = await llm_engine.classify_intent(msg_text)
        intent_event = {
            "type": "intent_routed",
            "intent": intent_res["intent"],
            "rationale": intent_res["rationale"]
        }
        await repo.save_chat_message(
            session_id=req.session_id,
            msg_type="intent_routed",
            content=json.dumps(intent_event, ensure_ascii=False)
        )
        yield f"data: {json.dumps(intent_event)}\n\n"

        # Step 1.5: Emit Memory Context & RAG Grounding Verification Events
        if memory_payload:
            await repo.save_chat_message(
                session_id=req.session_id,
                msg_type="memory_context",
                content=json.dumps(memory_payload, ensure_ascii=False)
            )
            yield f"data: {json.dumps(memory_payload)}\n\n"

        if self_rag_payload:
            await repo.save_chat_message(
                session_id=req.session_id,
                msg_type="self_rag",
                content=json.dumps(self_rag_payload, ensure_ascii=False)
            )
            yield f"data: {json.dumps(self_rag_payload)}\n\n"

        # STATE_GRAPH invitation (minimal chat surface — Studio owns execution)
        if intent_res["intent"] == "STATE_GRAPH":
            gid = intent_res.get("graph_id") or "commercial_lease_flow"
            # normalize via service aliases
            try:
                from services.state_graph_service import StateGraphService
                gid = StateGraphService.canonical_id(gid)
            except Exception:
                pass
            catalog = {
                "commercial_lease_flow": {"label": "Graph 1: Lease Onboarding & Receipt Verification", "narrative": "Suite-301 (60k→48k), 144k escrow, Gemini Vision OCR + accountant + executive HITL", "variables": {"unit_id": 301, "proposed_rent": 48000, "base_rent": 60000}},
                "renovation_permit_flow": {"label": "Graph 2: Maintenance & Contractor Tender", "narrative": "Cornerstone Heights — RAG Law 4/1996 + LATS 3 contractors + engineer HITL", "variables": {"location": "Cornerstone Heights - Zamalek"}},
                "rent_arrears_settlement_flow": {"label": "Graph 3: Arrears Mediation", "narrative": "90k arrears — ToT 3 strategies + tenant counter 9mo cycle + counsel HITL", "variables": {"tenant_id": 1, "unpaid_months": 3, "monthly_rent": 40000}},
            }
            info = catalog.get(gid, catalog["commercial_lease_flow"])
            invitation = {"type": "state_graph_invitation", "graph_id": gid, "label": info["label"], "narrative": info["narrative"], "variables_prefill": info["variables"], "deep_link": f"/stateGraph?graph={gid}"}
            await repo.save_chat_message(session_id=req.session_id, msg_type="state_graph_invitation", content=json.dumps(invitation, ensure_ascii=False))
            yield f"data: {json.dumps(invitation, ensure_ascii=False)}\n\n"
            # short helper token
            helper = f"Detected stateful workflow — **{info['label']}**. Open State Graph Studio to run the full live graph with streaming, checkpoints, and HITL. [Open Studio]({invitation['deep_link']})"
            yield f"data: {json.dumps({'type': 'token', 'content': helper}, ensure_ascii=False)}\n\n"
            await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=helper)
            yield f"data: {json.dumps({'type': 'done', 'final_answer': helper}, ensure_ascii=False)}\n\n"
            return

        # Step 2: Planning Agent Execution (if classified as PLANNING)
        if intent_res["intent"] == "PLANNING":
            try:
                planning_llm = create_langchain_llm(req.model or "gemini/gemini-3.1-flash-lite")
                agent = PlanningAgent(llm=planning_llm, mode="dynamic")
                agent.environment.mode = "grounded"

                queue = asyncio.Queue()
                loop = asyncio.get_running_loop()

                def on_subtask_complete(st_data):
                    routing = st_data.get("routing", {})
                    sub_event = {
                        "type": "planning_subtask",
                        "instruction": st_data.get("instruction", ""),
                        "method": routing.get("method") or st_data.get("method") or "PS",
                        "output": routing.get("output", "")
                    }
                    asyncio.run_coroutine_threadsafe(
                        repo.save_chat_message(
                            session_id=req.session_id,
                            msg_type="planning_subtask",
                            content=json.dumps(sub_event, ensure_ascii=False)
                        ),
                        loop
                    )
                    loop.call_soon_threadsafe(queue.put_nowait, sub_event)

                fut = loop.run_in_executor(None, agent.execute_request, msg_text, on_subtask_complete)

                while not fut.done() or not queue.empty():
                    try:
                        sub_event = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield f"data: {json.dumps(sub_event)}\n\n"
                    except asyncio.TimeoutError:
                        pass

                res = await fut
                summary_text = res.get("summary", "")

                for char_batch in [summary_text[i:i+8] for i in range(0, len(summary_text), 8)]:
                    yield f"data: {json.dumps({'type': 'token', 'content': char_batch})}\n\n"
                    await asyncio.sleep(0.01)

                await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=summary_text)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
            except Exception as e:
                logger.error(f"Planning execution error in SSE chat stream: {e}")

        # Step 3: Standard Tool Execution Stream
        async for chunk in stream_gen:
            yield chunk

            if chunk.startswith("data: "):
                try:
                    payload = json.loads(chunk[6:].strip())
                    chunk_type = payload.get("type")

                    if chunk_type == "token":
                        full_assistant_text += payload.get("content", "")
                    elif chunk_type == "tool_call":
                        await repo.save_chat_message(
                            session_id=req.session_id,
                            msg_type="tool_call",
                            tool_name=payload.get("tool"),
                            tool_args=payload.get("args"),
                            tool_result=payload.get("result")
                        )
                    elif chunk_type in ("action_confirmation", "confirmation_required"):
                        await repo.save_chat_message(
                            session_id=req.session_id,
                            msg_type="action_confirmation",
                            content=json.dumps(payload.get("payload") or payload, ensure_ascii=False)
                        )
                    elif chunk_type in ("elicitation_required", "elicitation"):
                        await repo.save_chat_message(
                            session_id=req.session_id,
                            msg_type="elicitation",
                            elicitation_payload=payload.get("payload")
                        )
                    elif chunk_type == "fallback":
                        full_assistant_text = payload.get("content", "")
                    elif chunk_type == "done" and payload.get("final_answer"):
                        full_assistant_text = payload.get("final_answer")
                except Exception:
                    pass

        # Persist final assistant text response
        if full_assistant_text:
            await repo.save_chat_message(
                session_id=req.session_id,
                msg_type="assistant",
                content=full_assistant_text
            )

    return StreamingResponse(sse_wrapper(), media_type="text/event-stream")


class ActionConfirmRequest(BaseModel):
    session_id: str
    action_type: str  # "schedule_tour" | "apply_lease" | "submit_maintenance" | "modify_lease"
    payload: Dict[str, Any]
    approved: bool


@router.post("/chat/action/confirm")
async def confirm_chat_action(req: ActionConfirmRequest, db: AsyncSession = Depends(get_async_db)):
    """Handles human confirmation/modification for high-consequence real estate actions."""
    repo = AsyncChatRepository(db)

    if not req.approved:
        final_answer = f"Action Cancelled: The proposed {req.action_type.replace('_', ' ')} was declined by the user."
        await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=final_answer)
        return {"status": "cancelled", "final_answer": final_answer}

    final_answer = dispatch_confirmed_action(req.action_type, req.payload)
    await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=final_answer)
    return {"status": "success", "final_answer": final_answer}


@router.post("/elicitation/respond")
async def respond_to_elicitation(req: ElicitationResponse, db: AsyncSession = Depends(get_async_db)):
    """Handles human manager / executive approval for elicited lease modifications."""
    repo = AsyncChatRepository(db)
    if req.approved:
        final_answer = (
            f"Elicitation Approved. Executive sign-off granted for Lease #{req.lease_id} "
            f"at proposed monthly rent {req.proposed_rent:,.2f} EGP."
        )
    else:
        final_answer = (
            f"Elicitation Rejected. Executive denied the proposed rent change for Lease #{req.lease_id}."
        )

    await repo.save_chat_message(session_id=req.session_id, msg_type="assistant", content=final_answer)
    return {"status": "success", "final_answer": final_answer}
