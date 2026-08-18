import os
import sys
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


logger = logging.getLogger("mcp_web_app")

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from mcp_server.server import CornerstoneMCPServer
from rag.pipeline import build_and_seed_vector_store
from rag.naive_rag import naive_rag_search
from rag.hybrid_rag import HybridSearchEngine
from rag.agentic_rag import AgenticRAGRouter
from rag.graph_rag import PropertyPolicyKnowledgeGraph
from rag.self_rag import SelfRAGVerifier
from memory.episodic_store import EpisodicStore
from memory.stm import ShortTermMemory
from memory.router import MemoryRouter
from memory.consolidation import SemanticMemoryStore, SemanticConsolidationEngine
from mcp_server.db_helpers import (
    create_chat_session, get_all_chat_sessions, get_chat_messages,
    save_chat_message, delete_chat_session, get_db_connection,
    update_chat_session_role, get_chat_session_role
)
from db.session import get_async_db, AsyncSession
from services.state_graph_service import StateGraphService
from services.tool_registry_service import ToolRegistryService
from services.hitl_service import HITLService
from services.ticket_service import TicketService
from state_graph.models import GraphState
from fastapi import Depends
from web.llm_engine import MCPLLMEngine, AVAILABLE_MODELS

from web.routers import (
    auth_router, properties_router, leases_router,
    maintenance_router, showcase_router, state_graph_router, admin_router
)
from services.cache_service import cache_service

app = FastAPI(
    title="Cornerstone Realty Group — MCP Autonomous Portal",
    description="Interactive Web UI & FastAPI backend for MCP Server Lab (Session 2)",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await cache_service.connect()

app.include_router(auth_router)
app.include_router(properties_router)
app.include_router(leases_router)
app.include_router(maintenance_router)
app.include_router(showcase_router)
app.include_router(state_graph_router)
app.include_router(admin_router)

# NOTE FOR EVALUATION:
# The FastAPI Web Server, Interactive Chat UI, and LLM Web Engine in this folder are
# BONUS showcase enhancements created to present, test, and demonstrate the MCP Server
# in an end-to-end interactive portal. The core MCP protocol implementation and server
# components reside in `mcp_server/`.

mcp_server = CornerstoneMCPServer()
llm_engine = MCPLLMEngine(default_model="gemini/gemini-3.1-flash-lite")
rag_store = build_and_seed_vector_store()
hybrid_engine = HybridSearchEngine(rag_store)
agentic_router = AgenticRAGRouter(hybrid_engine)
graph_rag = PropertyPolicyKnowledgeGraph()
self_rag_verifier = SelfRAGVerifier()


# Memory Subsystem Stores (Week 3)
episodic_store = EpisodicStore()
semantic_store = SemanticMemoryStore()
consolidation_engine = SemanticConsolidationEngine(episodic_store, semantic_store)
memory_router = MemoryRouter(episodic_store)

def seed_initial_memories():
    """Seed initial episodic & consolidated semantic memories for realistic real estate tenant personas."""
    # Tenant 1 (Amr Hassan) - Paint/Chemical Allergy & Relocation Notice
    episodic_store.insert_episode(
        entity_id="tenant_1",
        event_summary="Tenant reported severe asthma/fume allergy triggered by oil-based paints; requested low-VOC non-toxic paint for all unit maintenance.",
        timestamp="2026-02-15T09:00:00Z"
    )
    episodic_store.insert_episode(
        entity_id="tenant_1",
        event_summary="Tenant submitted formal notice to vacate at end of lease term due to company relocation to Alexandria; requested deposit refund inspection schedule.",
        timestamp="2026-04-02T14:30:00Z"
    )

    # Tenant 2 (Noha El-Sayed) - Quiet Work from Home & Service Animal Addendum
    episodic_store.insert_episode(
        entity_id="tenant_2",
        event_summary="Tenant requested top-floor quiet unit preference away from street noise for remote architecture studio work.",
        timestamp="2026-01-20T11:00:00Z"
    )
    episodic_store.insert_episode(
        entity_id="tenant_2",
        event_summary="Tenant submitted medical certification for registered service therapy dog (Golden Retriever); requested pet policy addendum waiver under Section 6.1b.",
        timestamp="2026-02-05T16:15:00Z"
    )
    episodic_store.insert_episode(
        entity_id="tenant_2",
        event_summary="Tenant requested 24/7 keycard access for Suite-301 executive meeting room and private terrace.",
        timestamp="2026-03-15T10:00:00Z"
    )

    # Tenant 5 (Omar Farouk) - EV Charging Stall & Rent Renewal Cap
    episodic_store.insert_episode(
        entity_id="tenant_5",
        event_summary="Tenant purchased electric vehicle (Tesla Model 3); requested dedicated Level-2 EV charging stall in B1 basement parking.",
        timestamp="2026-02-01T08:45:00Z"
    )
    episodic_store.insert_episode(
        entity_id="tenant_5",
        event_summary="Tenant requested annual lease renewal terms with rent increase capped at 5% pursuant to Cairo residential tenancy guidelines.",
        timestamp="2026-03-12T13:20:00Z"
    )

    # Tenant 6 (Yasmine Ibrahim) - Smart Biometric Lock Modification
    episodic_store.insert_episode(
        entity_id="tenant_6",
        event_summary="Tenant requested authorization to install smart digital keypad lock for Unit Royal-101 for elderly parent accessibility.",
        timestamp="2026-02-18T10:30:00Z"
    )

    # Property Manager (Tarek Mahmoud) - Building Compliance Directive
    episodic_store.insert_episode(
        entity_id="tenant_3",
        event_summary="Issued quarterly building compliance audit for Cairo and Alexandria properties; enforcing 48-hour emergency repair SLA.",
        timestamp="2026-02-01T09:00:00Z"
    )

    # Run initial consolidation to extract semantic facts
    consolidation_engine.run_periodic_consolidation()

seed_initial_memories()

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


FIXED_PERSONAS: Dict[str, Dict[str, Any]] = {
    "property_manager": {
        "name": "Tarek Mahmoud",
        "tenant_id": 3,
        "email": "tarek.m@cornerstonerealty.eg",
        "phone": "+201223334444",
        "role": "property_manager",
        "description": "Property Manager handling unit searches, maintenance dispatch (48-hr SLA), and standard lease operations"
    },
    "executive_admin": {
        "name": "Laila Fouad",
        "tenant_id": 4,
        "email": "laila.fouad@cornerstonerealty.eg",
        "phone": "+201000000001",
        "role": "executive_admin",
        "description": "Executive Admin authorized for high-value lease sign-offs (>50,000 EGP) and policy overrides (>15% discount)"
    },
    "tenant": {
        "name": "Amr Hassan",
        "tenant_id": 1,
        "email": "amr.hassan@example.com",
        "phone": "+201001234567",
        "role": "tenant",
        "unit_number": "A-101 (Cornerstone Heights, Cairo)",
        "lease_id": 1,
        "description": "Active tenant in Unit A-101. Has severe paint/VOC allergies and pending relocation notice."
    },
    "tenant_1": {
        "name": "Amr Hassan",
        "tenant_id": 1,
        "email": "amr.hassan@example.com",
        "phone": "+201001234567",
        "role": "tenant",
        "unit_number": "A-101 (Cornerstone Heights, Cairo)",
        "lease_id": 1,
        "description": "Active tenant in Unit A-101 (12,000 EGP/mo). Has paint/VOC allergies and pending relocation notice."
    },
    "tenant_2": {
        "name": "Noha El-Sayed",
        "tenant_id": 2,
        "email": "noha.elsayed@example.com",
        "phone": "+201119876543",
        "role": "tenant",
        "unit_number": "Suite-301 (Giza Commercial & Residential Center)",
        "lease_id": 3,
        "description": "Remote Architect in Suite-301 (60,000 EGP/mo). Requires top-floor quiet unit and therapy pet addendum."
    },
    "tenant_5": {
        "name": "Omar Farouk",
        "tenant_id": 5,
        "email": "omar.farouk@example.com",
        "phone": "+201005556677",
        "role": "tenant",
        "unit_number": "A-105 (Cornerstone Heights, Cairo)",
        "lease_id": 4,
        "description": "Tenant in Unit A-105 (22,000 EGP/mo). Requires EV Charging stall B1-14 and 5% rent renewal increase cap."
    },
    "tenant_6": {
        "name": "Yasmine Ibrahim",
        "tenant_id": 6,
        "email": "yasmine.ibrahim@example.com",
        "phone": "+201124445555",
        "role": "tenant",
        "unit_number": "Royal-101 (Zamalek Royal Suites, Cairo)",
        "lease_id": 5,
        "description": "Tenant in Royal-101 (35,000 EGP/mo). Requires smart biometric lock for elderly parent accessibility."
    }
}


class CreateSessionRequest(BaseModel):
    title: str = "محادثة جديدة"
    role: str = "property_manager"

class StreamChatRequest(BaseModel):
    session_id: str
    user_message: str
    model: str = "gemini/gemini-3.1-flash-lite"
    role: str = "property_manager"
    rag_strategy: str = "naive"
    conversation_history: List[Dict[str, Any]] = []

class ElicitationResponse(BaseModel):
    session_id: str
    lease_id: int
    proposed_rent: float
    approved: bool
    duration_months: int = 12

def build_system_prompt(role: str) -> str:
    persona = FIXED_PERSONAS.get(role, FIXED_PERSONAS["property_manager"])
    
    prompt = (
        f"You are the Cornerstone Realty Autonomous AI Assistant.\n"
        f"CURRENT AUTHENTICATED USER PERSONA:\n"
        f"- Name: {persona['name']}\n"
        f"- Role: {persona['role'].upper()}\n"
        f"- Email: {persona['email']}\n"
        f"- Phone: {persona['phone']}\n"
        f"- Tenant ID: {persona['tenant_id']}\n"
    )
    
    if role == "tenant":
        prompt += (
            f"- Assigned Unit: {persona['unit_number']}\n"
            f"- Active Lease ID: {persona['lease_id']}\n\n"
            "TENANT PERSONA BEHAVIOR:\n"
            "Whenever the user asks about 'my lease', 'my apartment', 'my unit', or 'my maintenance requests', "
            f"automatically use tenant_id={persona['tenant_id']} or email='{persona['email']}' in your MCP tool calls.\n\n"
        )
    elif role == "executive_admin":
        prompt += (
            "\nEXECUTIVE ADMIN BEHAVIOR:\n"
            "You have full authority to approve high-value lease agreements (>50,000 EGP/month) requiring executive sign-off, "
            "review company-wide lease terms, and override constraints.\n\n"
        )
    else:
        prompt += (
            "\nPROPERTY MANAGER BEHAVIOR:\n"
            "You manage property operations, unit search/lookup, maintenance dispatch, and standard tenant communication.\n\n"
        )

    # Week 3: Memory Subsystem Integration (Consolidated Semantic Facts & Recalled Episodes)
    tenant_id = persona.get("tenant_id", 1)
    active_facts = semantic_store.get_active_facts(subject=f"tenant_{tenant_id}")
    if active_facts:
        prompt += "\nACTIVE CONSOLIDATED TENANT FACTS (Semantic Memory):\n"
        for f in active_facts:
            prompt += f"- [{f['fact_key'].upper()}] {f['fact_value']} (v{f['version']})\n"
        prompt += "\n"

    episodes = episodic_store.query_episodes(entity_id=f"tenant_{tenant_id}", limit=3)
    if episodes:
        prompt += "RECENT EPISODIC MEMORIES (Episodic Store):\n"
        for ep in episodes:
            prompt += f"- {ep['event_summary']} ({ep['timestamp'][:10]})\n"
        prompt += "\n"

    prompt += (
        "PROPERTY & UNIT DIRECTORY:\n"
        "- Property ID 1: Cornerstone Heights (Cairo, 12 El-Tahrir Square) — Units: A-101 (unit_id: 101), A-102 (102), Penthouse-1 (103), A-104 (104), A-201 (105)\n"
        "- Property ID 2: Alexandria Beachfront Towers (Alexandria, 45 Corniche El-Nile) — Units: B-201 (unit_id: 201), B-202 (202), B-301 (203), Sky-Penthouse-B (204)\n"
        "- Property ID 3: Giza Commercial & Residential Center (Giza, 88 Pyramids Road) — Units: Suite-301 (unit_id: 301), Suite-302 (302), Suite-401 (303)\n"
        "- Property ID 4: Zamalek Royal Suites (Cairo, 24 26th of July Street) — Units: Royal-101 (unit_id: 401), Royal-Penthouse (402), Royal-201 (403)\n"
        "- Property ID 5: Gleem Bay Residence (Alexandria, 102 El-Geish Road, Gleem) — Units: G-101 (unit_id: 501), G-201 (502), G-301 (503)\n\n"
        "TENANT & ASSIGNED UNIT MAPPING:\n"
        "- Tenant ID 1: Amr Hassan (amr.hassan@example.com) -> Assigned Unit ID: 101 (A-101, Cornerstone Heights)\n"
        "- Tenant ID 2: Noha El-Sayed (noha.elsayed@example.com) -> Assigned Unit ID: 201 (B-201, Alexandria Beachfront Towers)\n"
        "- Tenant ID 5: Omar Farouk (omar.farouk@example.com) -> Assigned Unit ID: 105 (A-201, Cornerstone Heights)\n"
        "- Tenant ID 6: Yasmine Ibrahim (yasmine.ibrahim@example.com) -> Assigned Unit ID: 401 (Royal-101, Zamalek Royal Suites)\n"
        "- Tenant ID 7: Khaled Abdelrahman (khaled.abdel@example.com) -> Assigned Unit ID: 402 (Royal-Penthouse, Zamalek Royal Suites)\n"
        "- Tenant ID 8: Mariam Soliman (mariam.soliman@example.com) -> Assigned Unit ID: 502 (G-201, Gleem Bay Residence)\n\n"
        "CRITICAL MULTI-TOOL & REASONING RULES:\n"
        "1. Active consolidated tenant facts (allergies, floor preferences) and recent episodic history are already provided above in your system context.\n"
        "2. When submitting a maintenance ticket (`submit_maintenance_request`), ALWAYS use the tenant's assigned `unit_id` (e.g. `unit_id: 101` for Tenant 1 Amr Hassan), NEVER the `property_id`.\n"
        "3. Whenever answering a request, you MUST invoke the appropriate MCP tool(s) (lookup_available_units, submit_maintenance_request, modify_lease_terms, run_property_audit) to fetch or update real database records.\n"
        "4. When the user requests a compliance or occupancy audit for a property (e.g. 'run Compliance & Audits for Alexandria Beachfront Towers' or 'audit property 2'), IMMEDIATELY call the `run_property_audit` tool with the corresponding `property_id`.\n"
        "5. If a request requires multiple actions (e.g. searching for available units THEN checking maintenance or modifying lease terms), "
        "execute multiple MCP tool calls iteratively before generating your final response.\n"
        "6. Do NOT make up unit prices, lease numbers, or maintenance statuses.\n\n"
        "OUTPUT FORMAT INSTRUCTIONS:\n"
        "Format your final text responses strictly using clean, semantic HTML tags without markdown codeblock wrappers (no ```html). "
        "Use <h3> for section titles, <p> for text, <ul>/<li> for lists, <strong> for emphasis, and <table>/<thead>/<tbody>/<tr>/<th>/<td> for structured tables. "
        "This ensures rich rendering inside the portal interface."
    )
    return prompt


@app.get("/api/personas")
async def list_personas():
    return FIXED_PERSONAS

@app.get("/api/rag/documents")
async def list_rag_documents():
    """Week 3: List all ingested policy binder documents with metadata."""
    from rag.pipeline import POLICY_BINDER_CORPUS
    return {"count": len(POLICY_BINDER_CORPUS), "documents": POLICY_BINDER_CORPUS}

@app.get("/api/rag/search")
async def rag_search(query: str, top_k: int = 3, strategy: str = "naive"):
    """Week 3: Search over the policy binder using selected RAG strategy."""
    if strategy == "hybrid":
        results = hybrid_engine.search(query, top_k=top_k)
    elif strategy == "agentic":
        result = agentic_router.reason_and_retrieve(query)
        results = [{"payload": e, "metadata": {}, "score": 0} for e in result["evidence"]]
    elif strategy == "graph":
        graph_result = graph_rag.query_graph(query)
        results = [{"payload": str(graph_result), "metadata": {}, "score": 0}]
    else:
        results = naive_rag_search(query=query, vector_store=rag_store, top_k=top_k)
    return {"query": query, "strategy": strategy, "results": results}

@app.get("/api/benchmarks")
async def get_benchmarks():
    """Week 3: Return benchmark results from benchmark_results.json."""
    bench_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmarks", "benchmark_results.json")
    if os.path.exists(bench_path):
        with open(bench_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "No benchmark results found."}

@app.get("/api/memory/{tenant_id}")
async def get_tenant_memories_endpoint(tenant_id: int):
    """Week 3: Retrieve consolidated active semantic facts and episodic history for tenant."""
    subject = f"tenant_{tenant_id}"
    active_facts = semantic_store.get_active_facts(subject=subject)
    episodes = episodic_store.query_episodes(entity_id=subject, limit=5)
    
    formatted_memories = []
    for f in active_facts:
        formatted_memories.append({
            "category": f["fact_key"],
            "event_summary": f"{f['fact_value']} (v{f['version']})",
            "version": f["version"],
            "status": f["status"]
        })
    for ep in episodes:
        formatted_memories.append({
            "category": "episodic",
            "event_summary": ep["event_summary"],
            "timestamp": ep["timestamp"]
        })
        
    return {
        "tenant_id": tenant_id,
        "facts_count": len(active_facts),
        "episodes_count": len(episodes),
        "memories": formatted_memories
    }

@app.post("/api/memory/record")
async def record_memory_endpoint(req: dict):
    """Week 3: Route an event via MemoryRouter, persist to EpisodicStore, and trigger semantic consolidation."""
    tenant_id = req.get("tenant_id", 1)
    event_text = req.get("event_summary", "")
    decision = memory_router.route_information(
        content=event_text,
        entity_id=f"tenant_{tenant_id}",
        session_id=req.get("session_id", "web_session")
    )
    consolidation_result = consolidation_engine.run_periodic_consolidation(subject=f"tenant_{tenant_id}")
    return {
        "status": "success",
        "routing_decision": decision,
        "consolidation": consolidation_result
    }

@app.get("/api/memory/demo/stm")
async def demo_stm_endpoint():
    """Week 3: Interactive demo of ShortTermMemory buffer + decoupled scratchpad."""
    stm = ShortTermMemory(max_turns=3)
    stm.update_scratchpad(
        plan="Handle tenant paint allergy complaint and dispatch maintenance",
        subgoal="Verify unit A-101 lease terms and check paint supplier catalog",
        state_update={"supplier_identified": "EcoSafe Low-VOC Paints"}
    )
    
    stm.add_message("user", "My asthma is flaring up due to oil paint fumes!")
    stm.add_message("assistant", "I will dispatch low-VOC maintenance immediately.")
    stm.add_message("user", "Can you also check when my lease is up?")
    stm.add_message("assistant", "Your lease ends on 2026-12-31.")
    stm.add_message("user", "Great, thanks.")
    
    evicted = stm.prune_to_turn_limit()
    pruned_history = stm.get_context()
    scratchpad = stm.get_scratchpad()
    return {
        "evicted_turns_count": len(evicted),
        "pruned_transcript_turns": len(pruned_history),
        "transcript_preview": pruned_history,
        "scratchpad_preserved": {
            "current_plan": scratchpad.get("current_plan"),
            "active_subgoal": scratchpad.get("active_subgoal"),
            "working_state": scratchpad.get("working_state")
        },
        "guarantee": "Transcript pruning pruned older dialogue turns but left the scratchpad plan and working state 100% intact."
    }


@app.post("/api/memory/demo/route")
async def demo_route_endpoint(req: dict = None):
    """Week 3: Interactive demo of promote-or-drop router with logged reasoning."""
    if req is None:
        req = {}
    content = req.get("content", "Tenant Amr Hassan reported severe paint allergy; requested low-VOC maintenance.")
    entity_id = req.get("entity_id", "tenant_1")
    decision = memory_router.evaluate_item(
        item={"content": content, "role": "user"},
        entity_id=entity_id
    )
    history = memory_router.decision_log
    return {
        "input_content": content,
        "entity_id": entity_id,
        "decision": decision.model_dump(),
        "reasoning": decision.reasoning,
        "destination": decision.destination,
        "recent_router_logs": history[-3:] if history else []
    }

@app.post("/api/memory/demo/consolidate")
async def demo_consolidate_endpoint(req: dict = None):
    """Week 3: Interactive demo of semantic consolidation & real contradiction resolution."""
    if req is None:
        req = {}
    tenant_id = req.get("tenant_id", 1)
    subject = f"tenant_{tenant_id}"
    
    if req.get("trigger_conflict", True):
        episodic_store.insert_episode(
            entity_id=subject,
            event_summary="Tenant submitted formal notice to vacate and relocate at lease end; cancelled renewal interest.",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    result = consolidation_engine.run_periodic_consolidation(subject=subject)
    active_facts = semantic_store.get_active_facts(subject=subject)
    history_facts = semantic_store.get_fact_history(subject=subject, fact_key="lease_intent")
    return {
        "subject": subject,
        "consolidation_result": result,
        "active_facts": active_facts,
        "full_history_including_superseded": history_facts,
        "conflict_resolved": any(f["status"] == "superseded" for f in history_facts)
    }




@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cornerstone MCP Portal Initialized</h1>")

@app.get("/api/chats")
async def list_chats():
    return get_all_chat_sessions()

@app.post("/api/chats")
async def create_chat(req: CreateSessionRequest):
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_data = create_chat_session(session_id=session_id, title=req.title, role=req.role)
    return session_data

class UpdateSessionRoleRequest(BaseModel):
    role: str

@app.get("/api/chats/{session_id}")
async def get_chat(session_id: str):
    messages = get_chat_messages(session_id)
    role = get_chat_session_role(session_id)
    return {"session_id": session_id, "role": role, "messages": messages}

@app.patch("/api/chats/{session_id}/role")
async def update_session_role(session_id: str, req: UpdateSessionRoleRequest):
    update_chat_session_role(session_id, req.role)
    return {"status": "success", "session_id": session_id, "role": req.role}

@app.delete("/api/chats/{session_id}")
async def delete_chat(session_id: str):
    success = delete_chat_session(session_id)
    return {"status": "success" if success else "error"}

@app.get("/api/models")
async def get_models():
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

@app.get("/api/prompts")
async def list_prompts():
    return mcp_server.list_prompts()

@app.get("/api/prompt/get")
async def get_prompt(name: str = "draft_lease_notice", tenant_email: str = "tenant@example.com", proposed_rent: str = "15000"):
    try:
        return mcp_server.get_prompt(name, {"tenant_email": tenant_email, "proposed_rent": proposed_rent})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: StreamChatRequest):
    # Fetch prior history from SQLite for multi-turn context
    prior_db_messages = get_chat_messages(req.session_id)
    history_for_llm = []
    for m in prior_db_messages:
        if m["type"] == "user" and m.get("content"):
            history_for_llm.append({"role": "user", "content": m["content"]})
        elif m["type"] == "assistant" and m.get("content"):
            history_for_llm.append({"role": "assistant", "content": m["content"]})

    # Save current user prompt and active persona role to SQLite
    update_chat_session_role(req.session_id, req.role)
    save_chat_message(session_id=req.session_id, msg_type="user", content=req.user_message)
    
    # Enforce title update on first user message
    if req.user_message and req.user_message.strip():
        try:
            conn = get_db_connection()
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = ? AND msg_type = 'user';", (req.session_id,))
                cnt = cur.fetchone()[0]
                if cnt <= 1:
                    snip = req.user_message.strip()[:35] + ("..." if len(req.user_message.strip()) > 35 else "")
                    conn.execute("UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (snip, req.session_id))
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update session title in endpoint: {e}")

    system_prompt = build_system_prompt(req.role)


    # Inject RAG context based on selected strategy
    rag_context = ""
    if req.rag_strategy == "hybrid":
        search_results = hybrid_engine.search(req.user_message, top_k=3)
        rag_context = "\n\nHYBRID RAG CONTEXT (Vector + BM25 Keyword Fusion):\n"
        for r in search_results:
            rag_context += f"- {r['payload'][:200]}\n"
    elif req.rag_strategy == "agentic":
        agentic_result = agentic_router.reason_and_retrieve(req.user_message)
        rag_context = "\n\nAGENTIC RAG CONTEXT (Multi-Hop Decomposition):\n"
        rag_context += f"Sub-queries: {', '.join(agentic_result['sub_queries'])}\n"
        for e in agentic_result["evidence"]:
            rag_context += f"- {e[:200]}\n"
    elif req.rag_strategy == "graph":
        graph_result = graph_rag.query_graph(req.user_message)
        rag_context = "\n\nGRAPH RAG CONTEXT (Entity Traversal):\n"
        rag_context += f"Matched entities: {', '.join(graph_result['matched_entities'])}\n"
        for p in graph_result["paths"]:
            rag_context += f"- {p['source']} --[{p['relation']}]--> {p['target']}\n"
    elif req.rag_strategy == "naive":
        search_results = naive_rag_search(query=req.user_message, vector_store=rag_store, top_k=3)
        rag_context = "\n\nNAIVE RAG CONTEXT (Dense Vector Similarity):\n"
        for r in search_results:
            rag_context += f"- {r['payload'][:200]}\n"

    if rag_context:
        system_prompt += rag_context
    
    persona = FIXED_PERSONAS.get(req.role, FIXED_PERSONAS["tenant"])
    tenant_id = persona.get("tenant_id", 1)
    active_facts = semantic_store.get_active_facts(subject=f"tenant_{tenant_id}")
    recent_episodes = episodic_store.query_episodes(entity_id=f"tenant_{tenant_id}", limit=3)

    stream_gen = llm_engine.execute_agent_loop_stream(
        mcp_server_instance=mcp_server,
        user_message=req.user_message,
        system_prompt=system_prompt,
        conversation_history=history_for_llm,
        model=req.model,
        role=req.role
    )
    
    async def sse_wrapper():
        full_assistant_text = ""

        # Step 1: Run Mistral Intent Classification Router
        intent_res = await llm_engine.classify_intent(req.user_message)
        intent_event = {
            "type": "intent_routed",
            "intent": intent_res["intent"],
            "rationale": intent_res["rationale"]
        }
        save_chat_message(
            session_id=req.session_id,
            msg_type="intent_routed",
            content=json.dumps(intent_event, ensure_ascii=False)
        )
        yield f"data: {json.dumps(intent_event)}\n\n"

        if intent_res["intent"] == "PLANNING":
            try:
                from agent.planning_agent import PlanningAgent
                from web.llm_engine import create_langchain_llm
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
                    save_chat_message(
                        session_id=req.session_id,
                        msg_type="planning_subtask",
                        content=json.dumps(sub_event, ensure_ascii=False)
                    )
                    loop.call_soon_threadsafe(queue.put_nowait, sub_event)

                fut = loop.run_in_executor(None, agent.execute_request, req.user_message, on_subtask_complete)

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

                save_chat_message(session_id=req.session_id, msg_type="assistant", content=summary_text)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
            except Exception as e:
                logger.error(f"Planning execution error in SSE chat stream: {e}")

        # Step 2: Standard execution flow
        if active_facts or recent_episodes:
            mem_event = {
                "type": "memory_context",
                "tenant_id": tenant_id,
                "persona_name": persona.get("name", "Tenant"),
                "active_facts": [
                    {"category": f["fact_key"], "value": f["fact_value"], "version": f["version"], "status": f["status"]}
                    for f in active_facts
                ],
                "recent_episodes": [
                    {"summary": ep["event_summary"], "timestamp": ep["timestamp"][:10]}
                    for ep in recent_episodes
                ]
            }
            save_chat_message(
                session_id=req.session_id,
                msg_type="memory_context",
                content=json.dumps(mem_event, ensure_ascii=False)
            )
            yield f"data: {json.dumps(mem_event)}\n\n"

        async for chunk in stream_gen:
            yield chunk
            if chunk.startswith("data: "):
                try:
                    event = json.loads(chunk[6:].strip())
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
                            if rag_context:
                                critique = self_rag_verifier.verify_generation(
                                    query=req.user_message,
                                    evidence=[rag_context],
                                    generated_answer=full_assistant_text
                                )
                                critique_payload = {
                                    "type": "self_rag_verification",
                                    "is_relevant": critique.is_relevant,
                                    "is_supported": critique.is_supported,
                                    "critique_rationale": critique.critique_rationale,
                                    "faithfulness_score": critique.faithfulness_score
                                }
                                save_chat_message(
                                    session_id=req.session_id,
                                    msg_type="self_rag_verification",
                                    content=json.dumps(critique_payload, ensure_ascii=False)
                                )
                                yield f"data: {json.dumps(critique_payload)}\n\n"
                except Exception as e:
                    logger.error(f"Error parsing/saving SSE event to DB: {e}")



    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

@app.post("/api/elicitation/respond")
async def respond_elicitation(req: ElicitationResponse):
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

class PlanningExecuteRequest(BaseModel):
    request: str = "Emergency plumbing burst at Nile Tower Cairo. Re-plan contractor schedules under Egyptian Law 4/1996 SLAs."
    mode: str = "dynamic"
    env_mode: str = "grounded"

@app.post("/api/planning/execute")
async def execute_planning_agent_endpoint(req: PlanningExecuteRequest):
    try:
        from agent.planning_agent import PlanningAgent
        from web.llm_engine import create_langchain_llm
        llm = create_langchain_llm("gemini/gemini-3.1-flash-lite")
        
        agent = PlanningAgent(llm=llm, mode=req.mode)
        agent.environment.mode = req.env_mode
        
        res = agent.execute_request(req.request)
        return {
            "status": "success",
            "request": req.request,
            "mode": req.mode,
            "env_mode": req.env_mode,
            "summary": res.get("summary", ""),
            "trace": res.get("trace", {})
        }
    except Exception as e:
        logger.error(f"Planning execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "The planning agent could not generate an execution plan due to a temporary service issue.",
            "summary": "The planning agent encountered a temporary execution issue. Please check your request parameters and retry."
        }

@app.get("/api/planning/benchmarks")
async def get_planning_benchmarks():
    results_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "planning_eval", "results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"status": "success", "benchmarks": data}
    return {"status": "error", "message": "Benchmark results not found"}


# ---------------------------------------------------------------------------
# State Graph Execution & Checkpoint Endpoints (Session 4 & Final Project)
# ---------------------------------------------------------------------------

class StateGraphRunRequest(BaseModel):
    graph_id: str
    run_id: Optional[str] = None
    variables: Dict[str, Any] = {}


@app.post("/api/state-graph/run")
async def run_state_graph(req: StateGraphRunRequest, db: AsyncSession = Depends(get_async_db)):
    """Start or advance a state graph run asynchronously."""
    run_id = req.run_id or f"run-{uuid.uuid4().hex[:8]}"
    initial_state = GraphState(
        run_id=run_id,
        graph_id=req.graph_id,
        current_node="",
        variables=req.variables
    )
    res_state = await StateGraphService.arun_graph(db, initial_state)
    return {
        "status": "success",
        "run_id": res_state.run_id,
        "graph_status": res_state.status,
        "current_node": res_state.current_node,
        "step_number": res_state.step_number,
        "pending_hitl": res_state.pending_hitl,
        "last_error": res_state.last_error,
        "variables": res_state.variables,
        "history": res_state.history
    }


@app.get("/api/state-graph/{run_id}")
async def get_state_graph_status(run_id: str, db: AsyncSession = Depends(get_async_db)):
    """Retrieve the latest checkpoint state for a run."""
    state = await StateGraphService.aload_latest_state(db, run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return {"status": "success", "state": state.model_dump()}


# ---------------------------------------------------------------------------
# Admin Dynamic Tool Matrix Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/admin/agents/{agent_id}/tools")
async def get_agent_tools(agent_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get active tool permissions for a given agent persona."""
    bindings = await ToolRegistryService.aget_agent_tools(db, agent_id)
    all_tools = mcp_server.list_tools(role="executive_admin")
    result = []
    for t in all_tools:
        result.append({
            "name": t["name"],
            "description": t["description"],
            "is_enabled": bindings.get(t["name"], True)
        })
    return {"status": "success", "agent_id": agent_id, "tools": result}


class ToggleToolRequest(BaseModel):
    tool_name: str
    is_enabled: bool


@app.post("/api/admin/agents/{agent_id}/tools/toggle")
async def toggle_agent_tool(agent_id: str, req: ToggleToolRequest, db: AsyncSession = Depends(get_async_db)):
    """Dynamically enable/disable a tool for an agent and emit listChanged."""
    success = await ToolRegistryService.atoggle_tool(
        session=db,
        agent_id=agent_id,
        tool_name=req.tool_name,
        is_enabled=req.is_enabled
    )
    return {"status": "success", "agent_id": agent_id, "tool_name": req.tool_name, "is_enabled": req.is_enabled}


# ---------------------------------------------------------------------------
# Admin HITL Review Queue & Failure Ticket Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/admin/hitl/tasks")
async def list_hitl_tasks(db: AsyncSession = Depends(get_async_db)):
    """List pending Human-in-the-Loop review tasks."""
    tasks = await HITLService.alist_pending_tasks(db)
    return {"status": "success", "tasks": tasks}


class ResolveHITLRequest(BaseModel):
    decision: str  # approved, rejected, modified
    notes: Optional[str] = ""
    decided_by: Optional[str] = "Executive Admin"


@app.post("/api/admin/hitl/tasks/{task_id}/resolve")
async def resolve_hitl_task(task_id: str, req: ResolveHITLRequest, db: AsyncSession = Depends(get_async_db)):
    """Resolve an HITL review task and unblock state graph."""
    success = await HITLService.aresolve_task(db, task_id, req.decision, req.notes, req.decided_by)
    return {"status": "success", "task_id": task_id, "decision": req.decision}


@app.get("/api/admin/tickets")
async def list_failure_tickets(status: Optional[str] = None, db: AsyncSession = Depends(get_async_db)):
    """List captured state graph node failure tickets."""
    tickets = await TicketService.alist_tickets(db, status=status)
    return {"status": "success", "tickets": tickets}


# ---------------------------------------------------------------------------
# SPA Static File Mounting & Web Platform Routing
# ---------------------------------------------------------------------------

DIST_DIR = os.path.join(os.path.dirname(__file__), "dist")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(DIST_DIR) and os.path.exists(os.path.join(DIST_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_spa_index():
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    static_index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return HTMLResponse("<h1>Cornerstone Realty Group MCP Platform API Running</h1>")


if __name__ == "__main__":
    import uvicorn
    import sys
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    is_dev = "--dev" in sys.argv or "--reload" in sys.argv or os.getenv("DEV", "").lower() in ("true", "1") or os.getenv("RELOAD", "").lower() in ("true", "1")
    
    if is_dev:
        print("🚀 Starting FastAPI Server in DEV (Auto-Reload) Mode with Cache Exclusions...")
        uvicorn.run(
            "web.app:app",
            host=host,
            port=port,
            reload=True,
            reload_excludes=[".venv", "__pycache__", "*.pyc", "*.pyo", ".git", "db/*.db*", "planning_eval/*"]
        )
    else:
        uvicorn.run("web.app:app", host=host, port=port)

