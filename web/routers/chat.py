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

from fastapi import APIRouter, Depends, HTTPException, Request
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
    model: str = "gemini/gemini-3.1-flash-lite"
    role: Optional[str] = None
    user_email: Optional[str] = None
    tenant_id: Optional[int] = None
    rag_strategy: str = "naive"
    conversation_history: List[Dict[str, Any]] = []

    def get_message(self) -> str:
        return self.user_message or self.message or ""


class ElicitationResponse(BaseModel):
    session_id: str
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12


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
    """SSE streaming endpoint for multi-turn autonomous agent execution."""
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

    # Save user message to database (auto-renames default session title)
    await repo.update_chat_session_role(req.session_id, effective_role)
    await repo.save_chat_message(session_id=req.session_id, msg_type="user", content=msg_text, user_id=effective_tenant_id)

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
        role=req.role
    )

    async def sse_wrapper():
        full_assistant_text = ""

        # Step 1: Run Mistral Intent Classification Router
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
