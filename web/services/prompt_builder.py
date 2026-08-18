"""
Prompt Builder Service (web/services/prompt_builder.py)
Constructs persona-aware, dynamically grounded system prompts for Cornerstone Realty autonomous agents.
"""

from typing import Optional, Dict, Any
from db.models import Tenant, Unit, Property, Lease
from db.session import get_sync_db


def build_system_prompt(
    role: str = "property_manager",
    user_email: Optional[str] = None,
    tenant_id: Optional[int] = None,
    semantic_store: Optional[Any] = None,
    episodic_store: Optional[Any] = None,
) -> str:
    """Builds dynamic, grounded system prompt injecting authentic DB persona identity and memory."""
    db = next(get_sync_db())
    tenant_obj: Optional[Tenant] = None

    try:
        if tenant_id:
            tenant_obj = db.get(Tenant, tenant_id)
        elif user_email:
            tenant_obj = db.query(Tenant).filter(Tenant.email == user_email).first()
        elif role == "tenant":
            tenant_obj = db.get(Tenant, 1)  # Default tenant: Dr. Tarek El-Mahdy
        elif role == "property_manager":
            tenant_obj = db.query(Tenant).filter(Tenant.role == "property_manager").first()
        elif role == "executive_admin":
            tenant_obj = db.query(Tenant).filter(Tenant.role == "executive_admin").first()

        # Fallback values if DB lookup fails
        if not tenant_obj:
            if role == "executive_admin":
                user_name = "Laila Fouad"
                email = "laila.fouad@cornerstonerealty.eg"
                phone = "+20 100 000 0001"
                t_id = 9
                assigned_unit = None
            elif role == "property_manager":
                user_name = "Tarek Mahmoud"
                email = "tarek.m@cornerstonerealty.eg"
                phone = "+20 122 333 4444"
                t_id = 8
                assigned_unit = None
            else:
                user_name = "Dr. Tarek El-Mahdy"
                email = "tarek.mahdy@cairomed.org"
                phone = "+20 100 123 4567"
                t_id = 1
                assigned_unit = "101-Garden"
        else:
            user_name = tenant_obj.full_name
            email = tenant_obj.email
            phone = tenant_obj.phone or "+20 100 000 0000"
            t_id = tenant_obj.tenant_id
            assigned_unit = f"Unit {tenant_obj.assigned_unit_id}" if tenant_obj.assigned_unit_id else None

        # Fetch lease details if tenant
        active_lease: Optional[Lease] = None
        if t_id:
            active_lease = db.query(Lease).filter(Lease.tenant_id == t_id, Lease.is_active == True).first()

    finally:
        db.close()

    prompt = (
        f"You are the Cornerstone Realty Autonomous AI Assistant.\n"
        f"CURRENT AUTHENTICATED USER PERSONA:\n"
        f"- Full Name: {user_name}\n"
        f"- System Role: {role.upper()}\n"
        f"- Registered Email: {email}\n"
        f"- Phone: {phone}\n"
        f"- Tenant ID: {t_id}\n"
    )

    if role == "tenant":
        unit_str = assigned_unit or "Unit 101"
        lease_id_str = str(active_lease.lease_id) if active_lease else "1"
        prompt += (
            f"- Assigned Unit: {unit_str}\n"
            f"- Active Lease ID: {lease_id_str}\n\n"
            "TENANT PERSONA BEHAVIOR & RULES:\n"
            "1. Whenever the user asks about 'my lease', 'my rent', 'my apartment', or 'my maintenance tickets', "
            f"you MUST use their authentic registered email: '{email}' or tenant_id: {t_id} or unit_id: {t_id}.\n"
            f"2. NEVER use dummy/placeholder emails (like amr.hassan). Always use '{email}'.\n"
            "3. If the tool returns lease or maintenance info, summarize it clearly with rent numbers and dates.\n\n"
        )
    elif role == "executive_admin":
        prompt += (
            "\nEXECUTIVE ADMIN BEHAVIOR:\n"
            "You have full authority to approve high-value lease agreements (>50,000 EGP/month) requiring executive sign-off, "
            "review portfolio-wide lease terms, approve concessions, and override constraints.\n\n"
        )
    else:
        prompt += (
            "\nPROPERTY MANAGER BEHAVIOR:\n"
            "You manage property operations, unit search/lookup, maintenance dispatch (48-hr SLA), and standard tenant communication.\n\n"
        )

    # Memory Subsystem Integration (Consolidated Semantic Facts & Recalled Episodes)
    if semantic_store:
        try:
            active_facts = semantic_store.get_active_facts(subject=f"tenant_{t_id}")
            if active_facts:
                prompt += "\nACTIVE CONSOLIDATED TENANT FACTS (Semantic Memory):\n"
                for f in active_facts:
                    prompt += f"- [{f['fact_key'].upper()}] {f['fact_value']} (v{f['version']})\n"
                prompt += "\n"
        except Exception:
            pass

    if episodic_store:
        try:
            episodes = episodic_store.query_episodes(entity_id=f"tenant_{t_id}", limit=4)
            if episodes:
                prompt += "RECENT EPISODIC MEMORIES (Episodic Store):\n"
                for ep in episodes:
                    prompt += f"- {ep['event_summary']} ({ep['timestamp'][:10] if ep.get('timestamp') else ''})\n"
                prompt += "\n"
        except Exception:
            pass

    prompt += (
        "PROPERTY & UNIT DIRECTORY:\n"
        "- Property ID 1: Nile Plaza Luxury Residences (Cairo, 12 El-Tahrir Square) — Units: 101 (unit_id: 101), 102 (102), 103 (103)\n"
        "- Property ID 2: Alexandria Beachfront Towers (Alexandria, 45 Corniche El-Nile) — Units: 201 (unit_id: 201), 202 (202)\n"
        "- Property ID 3: Giza Commercial & Residential Center (Giza, 88 Pyramids Road) — Units: 301 (unit_id: 301), 302 (302)\n"
        "- Property ID 4: Zamalek Royal Suites (Cairo, 24 26th of July Street) — Units: 401 (unit_id: 401), 402 (402)\n"
        "- Property ID 5: Gleem Bay Residence (Alexandria, 102 El-Geish Road, Gleem) — Units: 501 (unit_id: 501)\n"
        "- Property ID 6: Red Sea Marina Villas (Hurghada, Marina Promenade) — Units: 601 (unit_id: 601)\n\n"
        "CRITICAL MULTI-TOOL & REASONING RULES:\n"
        "1. When submitting a maintenance ticket (`submit_maintenance_request`), ALWAYS use the tenant's assigned `unit_id` (e.g. `101`), NEVER the property_id.\n"
        "2. Whenever answering a request, you MUST invoke the appropriate MCP tool(s) (lookup_available_units, submit_maintenance_request, modify_lease_terms, run_property_audit) to fetch or update real database records.\n"
        "3. When the user requests a compliance or occupancy audit for a property (e.g. 'audit property 1'), IMMEDIATELY call the `run_property_audit` tool with `property_id: 1`.\n"
        "4. If a request requires multiple actions (e.g. searching for available units THEN checking maintenance or modifying lease terms), execute multiple MCP tool calls iteratively.\n"
        "5. Do NOT make up unit prices, lease numbers, or maintenance statuses.\n\n"
        "OUTPUT FORMAT INSTRUCTIONS:\n"
        "Format your final text responses strictly using clean, semantic HTML tags without markdown codeblock wrappers (no ```html). "
        "Use <h3> for section titles, <p> for text, <ul>/<li> for lists, <strong> for emphasis, and <table>/<thead>/<tbody>/<tr>/<th>/<td> for structured tables. "
        "This ensures rich rendering inside the portal interface."
    )

    return prompt
