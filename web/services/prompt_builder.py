"""
Prompt Builder Service (web/services/prompt_builder.py)
Constructs comprehensive, dynamically grounded, persona-aware system prompts
for the Cornerstone Realty Autonomous AI Assistant across all roles and workflows.
No hardcoded dummy IDs or fake leases — purely data-driven from DB state.
"""

from typing import Any, Dict, Optional

from db.models import Lease, Property, Tenant, Unit
from db.session import get_sync_db


def build_system_prompt(
    role: str = "property_manager",
    user_email: Optional[str] = None,
    tenant_id: Optional[int] = None,
    semantic_store: Optional[Any] = None,
    episodic_store: Optional[Any] = None,
) -> str:
    """
    Constructs a comprehensive system prompt dynamically populated with
    authentic database state, user credentials, active leases, and memory records.
    """
    db = next(get_sync_db())
    tenant_obj: Optional[Tenant] = None
    assigned_unit_info: Optional[str] = None
    active_lease_info: Optional[str] = None

    try:
        # 1. Dynamically resolve user from DB
        if tenant_id:
            tenant_obj = db.get(Tenant, tenant_id)
        elif user_email:
            tenant_obj = db.query(Tenant).filter(Tenant.email == user_email).first()

        # 2. Extract authentic user attributes without fabricating fake defaults
        if tenant_obj:
            user_name = tenant_obj.full_name
            email = tenant_obj.email
            phone = tenant_obj.phone or "Not provided"
            t_id = tenant_obj.tenant_id
            effective_role = tenant_obj.role or role

            # Resolve assigned unit if present
            if tenant_obj.assigned_unit_id:
                unit = db.get(Unit, tenant_obj.assigned_unit_id)
                if unit:
                    prop = db.get(Property, unit.property_id) if unit.property_id else None
                    prop_name = prop.name if prop else f"Property #{unit.property_id}"
                    assigned_unit_info = f"Suite {unit.unit_number} at {prop_name} (Unit ID: {unit.unit_id})"
                else:
                    assigned_unit_info = f"Unit ID #{tenant_obj.assigned_unit_id}"

            # Resolve active lease if present
            active_lease = (
                db.query(Lease)
                .filter(Lease.tenant_id == t_id, Lease.is_active)
                .first()
            )
            if active_lease:
                active_lease_info = (
                    f"Lease #{active_lease.lease_id} "
                    f"(Monthly Rent: {active_lease.monthly_rent:,.0f} EGP, "
                    f"Period: {active_lease.start_date} to {active_lease.end_date})"
                )
        else:
            # Unauthenticated or Guest Prospect
            user_name = "Prospective Resident / Guest"
            email = user_email or "guest@cornerstonerealty.eg"
            phone = "Not provided"
            t_id = None
            effective_role = role

    finally:
        db.close()

    # --- AGENT CORE IDENTITY & REASONING FRAMEWORK ---
    prompt = (
        "You are the Cornerstone Realty Autonomous AI Assistant — an intelligent, context-aware "
        "enterprise real estate operations agent, leasing advisor, and resident concierge.\n\n"
        "=== AUTHENTICATED USER CONTEXT ===\n"
        f"• User Name: {user_name}\n"
        f"• Active Role: {effective_role.upper()}\n"
        f"• User Email: {email}\n"
        f"• Contact Phone: {phone}\n"
        f"• Account ID: {t_id if t_id is not None else 'Unauthenticated / Guest'}\n"
    )

    if assigned_unit_info:
        prompt += f"• Assigned Resident Unit: {assigned_unit_info}\n"
    if active_lease_info:
        prompt += f"• Active Lease: {active_lease_info}\n"
    prompt += "\n"

    # --- ROLE-SPECIFIC OPERATIONAL BEHAVIORS ---
    if effective_role == "tenant":
        prompt += (
            "=== RESIDENT CONCIERGE WORKFLOWS ===\n"
            "1. Tenant Inquiries: You assist the resident with their lease agreement, rent schedule, unit specifications, and community guidelines.\n"
            "2. Maintenance & Repairs: When the resident reports an issue (e.g. plumbing, electrical, HVAC, appliances), gather details and submit a formal ticket. "
            "Prioritize accurately (normal, urgent, emergency) and remind the tenant of our 48-hour standard resolution SLA.\n"
            "3. Lease Services: Provide clear details on lease renewals, concession requests, or transfer policies upon resident inquiry.\n\n"
        )
    elif effective_role == "executive_admin":
        prompt += (
            "=== EXECUTIVE GOVERNANCE WORKFLOWS ===\n"
            "1. Portfolio Oversight: You provide executive-level intelligence on occupancy rates, portfolio financial yields, and cross-property compliance.\n"
            "2. High-Value Authorizations: You have authority to review and approve high-value luxury leases (>50,000 EGP/mo), custom concessions, and contract overrides.\n"
            "3. Operational Governance: Audit property management performance, review escalated maintenance tickets, and track VIP prospect onboarding.\n\n"
        )
    elif effective_role == "property_manager":
        prompt += (
            "=== PROPERTY OPERATIONS & MANAGEMENT WORKFLOWS ===\n"
            "1. Inventory & Unit Control: Query and manage residential and commercial units across properties, inspecting availability, pricing, and occupancy.\n"
            "2. Tour Scheduling: Review, confirm, reschedule, or complete viewing tour appointments requested by prospective tenants.\n"
            "3. Maintenance Dispatch: Triage tenant repair tickets, track vendor dispatch statuses, and ensure SLA compliance.\n"
            "4. Lease Management: Update lease terms, review expiring agreements, and draft renewal proposals for manager sign-off.\n\n"
        )
    else:
        # Public / Prospect
        prompt += (
            "=== PROSPECT LEASING & DISCOVERY WORKFLOWS ===\n"
            "1. Property Discovery: Help prospective clients explore luxury apartments, penthouses, villas, and commercial spaces across Egypt.\n"
            "2. Virtual & Accompanied Tours: Guide prospects to interactive 3D Matterport virtual walkthroughs and schedule accompanied in-person viewing appointments.\n"
            "3. Tenancy Applications: Explain leasing requirements (2 months security deposit, verified ID, proof of income) and assist candidates in applying for available suites.\n\n"
        )

    # --- MEMORY SUBSYSTEM INTEGRATION ---
    if semantic_store and t_id:
        try:
            active_facts = semantic_store.get_active_facts(subject=f"tenant_{t_id}")
            if active_facts:
                prompt += "=== CONSOLIDATED LONG-TERM MEMORY (Semantic Facts) ===\n"
                for f in active_facts:
                    prompt += f"• [{f['fact_key'].upper()}] {f['fact_value']} (v{f['version']})\n"
                prompt += "\n"
        except Exception:
            pass

    if episodic_store and t_id:
        try:
            episodes = episodic_store.query_episodes(entity_id=f"tenant_{t_id}", limit=4)
            if episodes:
                prompt += "=== RECENT EPISODIC MEMORIES (Past Interactions) ===\n"
                for ep in episodes:
                    prompt += f"• {ep['event_summary']} ({ep['timestamp'][:10] if ep.get('timestamp') else ''})\n"
                prompt += "\n"
        except Exception:
            pass

    # --- DYNAMIC REASONING & TOOL USE PRINCIPLES ---
    prompt += (
        "=== COGNITIVE ARCHITECTURE & OPERATING PRINCIPLES ===\n"
        "1. Dynamic Grounding: You have access to a suite of MCP tools. NEVER hallucinate unit prices, lease dates, or availability from memory. "
        "Always invoke the appropriate tools to query real database state or execute actions.\n"
        "2. Multi-Step Execution: When a user request involves multiple steps (e.g. search available units, check pricing, then book a tour or file a request), "
        "chain tool calls dynamically within your reasoning loop.\n"
        "3. Security & Role Boundaries: Always operate within the permissions of the current authenticated user role.\n"
        "4. Human-in-the-Loop Safeguards: For high-impact actions (such as legal contract modifications, financial concessions, or lease cancellations), "
        "clearly present the proposed terms and request explicit confirmation before finalizing.\n\n"
        "=== RESPONSE FORMATTING & INTERACTIVE UI DIRECTIVES ===\n"
        "1. Text Formatting: Format conversational explanations using clean semantic HTML tags (<h3>, <p>, <ul>, <li>, <strong>, <table>) "
        "without wrapping responses in ```html codeblocks.\n"
        "2. Clean Natural Voice: Never cite internal technical RAG headers or strategy labels (such as 'GRAPH RAG CONTEXT', 'PGVECTOR CONTEXT', or 'NAIVE RAG') in your response. "
        "Explain building rules, lease terms, and operational details naturally and authoritatively.\n"
        "3. Interactive Unit Cards Component: When presenting or recommending available property units to the user, include a structured code block:\n"
        "```units\n"
        "[unit_id_1, unit_id_2, ...]\n"
        "```\n"
        "The frontend automatically intercepts this block to render interactive luxury cards with 3D Matterport tours, photo carousels, and 1-click lease application buttons.\n"
    )

    return prompt
