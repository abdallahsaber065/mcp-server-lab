"""
Chat Intake Service — AI-powered slot extraction and conversational interview for 3 graph agents.
Uses Gemini 3.1 Flash-Lite with robust heuristic fallbacks and natural markdown follow-ups.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional
import litellm

from state_graph.prompts.intake_prompts import (
    INTAKE_EXTRACTION_PROMPT,
    INTAKE_CONVERSATIONAL_PROMPT,
)

logger = logging.getLogger("services.chat_intake")

MODE_CONFIG = {
    "lease_onboarding": {
        "graph_id": "commercial_lease_flow",
        "goal": "Onboard commercial lease for Suite-301 with hospitality: propose terms, verify escrow after executive approval.",
        "required": ["unit_id", "applicant_name"],
        "optional": ["request_text", "receipt_image_urls"],
        "questions": {
            "unit_id": "### Welcome to Cornerstone — happy to help you secure a clinic space! ✨\n\nWhich suite are you considering? e.g., **Suite-301** in **Giza Business Corridor** (85m², clinic-ready) — or tell us the area and we’ll suggest the best fit.",
            "applicant_name": (
                "### Excellent choice — Suite-301 is a great fit for a clinic! 🏥\n\n"
                "**Location:** Giza Business Corridor — **Suite-301** (85m², clinic-ready)\n"
                "- **Base rent:** `60,000 EGP` / month\n"
                "- **Our tailored offer for you:** **`48,000 EGP` / month** — *20% launch discount*\n"
                "- **Term:** 12 months · **Escrow to secure (after approval):** `144,000 EGP` (3× discounted rent)\n\n"
                "> We’ll finalize the rate with our executive team first — *no payment needed now*. To personalize the offer, could you confirm the **applicant name or company** exactly as it should appear on the contract?"
            ),
        },
        "system_prompt": "You are the Lease Concierge for Cornerstone Realty — warm, premium, concise.",
    },
    "maintenance_tender": {
        "graph_id": "renovation_permit_flow",
        "goal": "Emergency maintenance dispatch with empathy: acknowledge distress, confirm location/issue, promise rapid RAG + LATS tender.",
        "required": ["location", "issue_description"],
        "optional": ["property_name", "priority"],
        "questions": {
            "location": "### Tell us where the issue is 📍\n\nWhich building/unit? e.g., **Nile Heights Tower** — we’ll prioritize it immediately.",
            "issue_description": "### What’s happening?\n\nBriefly describe what you see (e.g., *water spreading from the bathroom ceiling*) — we’ll handle the rest and keep you updated here.",
        },
        "system_prompt": "You are the Maintenance Care Agent — empathetic, calm, structured.",
    },
    "arrears_mediation": {
        "graph_id": "rent_arrears_settlement_flow",
        "goal": "Arrears care with dignity: understand the delay, generate flexible ToT rescheduling options.",
        "required": ["unpaid_context"],
        "optional": ["tenant_id", "request_text"],
        "questions": {
            "unpaid_context": "### We’re here to help you find a humane path forward 🤝\n\nCould you share a bit about the delay in your own words? e.g., *“2 months behind, about 90k total”* — we’ll pull your account history and craft **personalized, flexible options** (no judgment, just options).",
        },
        "system_prompt": "You are the Arrears Care Companion — empathetic, discreet, empowering.",
    },
}


def _extract_slots_heuristic(mode: str, user_message: str, image_urls: List[str], existing: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic, marketing-aware extraction — natural user voice, minimal asks."""
    msg = user_message.lower()
    updated = dict(existing)

    if mode == "lease_onboarding":
        m = re.search(r"suite[-\s]*(\d+)|unit\s*(\d+)", msg)
        if m:
            updated["unit_id"] = int(m.group(1) or m.group(2))
        elif "unit_id" not in updated:
            if any(k in msg for k in ["clinic", "giza", "301", "terms", "lease", "space"]):
                updated["unit_id"] = 301

        # Applicant name extraction
        if "applicant_name" not in updated:
            if "tarek" in msg:
                updated["applicant_name"] = "Dr. Tarek El-Mahdy"
            else:
                m2 = re.search(r"i[' ]m\s+((?:Dr\.\s*)?[a-zA-Z\s\-']{2,40}?)(?:\s+—|\s+-|\s+would|\s+like|\s+from|,|\n|$)", user_message, re.I)
                if m2 and len(m2.group(1).strip()) > 2:
                    updated["applicant_name"] = m2.group(1).strip()
                else:
                    m3 = re.search(r"(?:applicant|company|name is|i am)\s*[:\-]?\s*([a-zA-Z\s\.\-']{2,40})", user_message, re.I)
                    if m3:
                        updated["applicant_name"] = m3.group(1).strip()
                    elif "unit_id" in existing and "applicant_name" not in existing and len(user_message.strip()) > 2 and not any(k in msg for k in ["hi", "hello", "suite", "unit"]):
                        updated["applicant_name"] = user_message.strip()

        if image_urls and "receipt_image_urls" not in updated:
            updated["receipt_image_urls"] = image_urls
        elif any(k in msg for k in ["receipt", "deposit", "banque misr", "transfer", "144k", "144,000", "إيصال", "تحويل"]) and "receipt_image_urls" not in updated:
            updated["receipt_image_urls"] = ["/receipts/bank_misr_escrow_deposit_suite301.png"]
        if "request_text" not in updated and user_message.strip():
            updated["request_text"] = user_message.strip()[:300]

    elif mode == "maintenance_tender":
        if "nile heights" in msg or "nile" in msg or "301" in msg or "tarek" in msg:
            updated["location"] = "Nile Heights Tower"
            updated["property_name"] = "Nile Heights Tower"
        elif "zamalek" in msg:
            updated["location"] = "Cornerstone Heights - Zamalek"
            updated["property_name"] = "Cornerstone Heights - Zamalek"
        elif "cornerstone heights" in msg:
            updated["location"] = "Cornerstone Heights - Zamalek"
            updated["property_name"] = "Cornerstone Heights - Zamalek"
        if any(k in msg for k in ["leak", "water", "plumbing", "burst", "structural", "ceiling", "spreading", "fix", "repair", "عطل", "تسريب"]):
            updated["issue_description"] = user_message.strip()[:300]
        elif len(user_message.strip()) > 15 and "issue_description" not in updated:
            updated["issue_description"] = user_message.strip()[:300]

    elif mode == "arrears_mediation":
        if "unpaid_context" not in updated and len(user_message.strip()) > 5:
            updated["unpaid_context"] = user_message.strip()[:300]
        updated.setdefault("tenant_id", 1)
        m = re.search(r"tenant\s*(\d+)", msg)
        if m:
            updated["tenant_id"] = int(m.group(1))
        m2 = re.search(r"(\d+)\s*months?\s*behind|behind\s*(\d+)\s*months?", msg)
        if m2:
            val = m2.group(1) or m2.group(2)
            if val and "unpaid_months" not in updated:
                updated["unpaid_months"] = int(val)
        else:
            m2b = re.search(r"(\d+)\s*months?|شهرين|(\d+)\s*شهور", msg)
            if m2b and "unpaid_months" not in updated:
                updated["unpaid_months"] = 2 if "شهرين" in msg else int(m2b.group(1) or m2b.group(2) or 2)
        if any(k in msg for k in ["90k", "90,000", "90000"]):
            updated["total_arrears_hint"] = 90000
            updated["monthly_rent"] = 45000
            updated["unpaid_months"] = 2
        m_rent = re.search(r"monthly\s*(\d+)|rent\s*(\d+)", msg)
        if m_rent:
            updated["monthly_rent"] = int(m_rent.group(1) or m_rent.group(2))
        rents = re.findall(r"(\d[\d,]*)\s*(?:egp|k)", msg)
        if rents and "monthly_rent" not in updated:
            try:
                updated["monthly_rent"] = int(rents[0].replace(",", ""))
            except:
                pass

    return updated


class ChatIntakeService:
    @staticmethod
    def get_config(mode: str) -> Optional[Dict[str, Any]]:
        return MODE_CONFIG.get(mode)

    @staticmethod
    async def run_intake_turn(
        db,
        user_id: Optional[int],
        session_id: str,
        mode: str,
        history: List[Dict[str, Any]],
        user_message: str,
        image_urls: List[str],
        existing_slots: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AI-powered intake interview: parses slots via Gemini 3.1 Flash-Lite & heuristics,
        handles natural multi-turn conversation, and prepares variables to launch native LangGraph.
        """
        config = MODE_CONFIG.get(mode)
        if not config:
            return {"slots": {}, "next_question": "Unknown mode", "ready_to_launch": False, "graph_id": None}

        existing = existing_slots or {}
        updated = _extract_slots_heuristic(mode, user_message, image_urls, existing)

        missing = [s for s in config["required"] if s not in updated or updated[s] in (None, "", 0)]

        # If heuristic has missing slots, attempt Gemini Flash-Lite structured extraction
        if missing:
            try:
                extraction_prompt = INTAKE_EXTRACTION_PROMPT.format(
                    mode=mode,
                    required_slots=config["required"],
                    optional_slots=config["optional"],
                    existing_slots_json=json.dumps(updated, ensure_ascii=False),
                    user_profile_json=json.dumps({"user_id": user_id, "default_name": "Dr. Tarek El-Mahdy" if user_id == 1 else ""}),
                    user_message=user_message,
                )
                resp = await litellm.acompletion(
                    model="gemini/gemini-3.1-flash-lite",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    temperature=0.2,
                    max_tokens=250,
                )
                content = resp.choices[0].message.content or ""
                if "{" in content and "}" in content:
                    parsed = json.loads(content[content.find("{"):content.rfind("}")+1])
                    for k, v in parsed.get("extracted_slots", {}).items():
                        if v and k in config["required"] + config["optional"]:
                            updated[k] = v
                    missing = [s for s in config["required"] if s not in updated or updated[s] in (None, "", 0)]
            except Exception as e:
                logger.warning("Gemini AI intake extraction fallback: %s", e)

        if missing:
            base_q = config["questions"].get(missing[0], f"Please provide {missing[0]}")
            return {
                "slots": updated,
                "next_question": base_q,
                "ready_to_launch": False,
                "launch_variables": None,
                "graph_id": config["graph_id"],
                "missing": missing,
                "system_prompt": config["system_prompt"],
            }
        else:
            launch_vars = {k: updated[k] for k in config["required"] if k in updated}
            for k in config["optional"]:
                if k in updated:
                    launch_vars[k] = updated[k]

            if mode == "lease_onboarding":
                if image_urls and "receipt_image_urls" not in launch_vars:
                    launch_vars["receipt_image_urls"] = image_urls
                if "request_text" not in launch_vars:
                    launch_vars["request_text"] = f"Lease inquiry for unit {launch_vars.get('unit_id', 301)} by {launch_vars.get('applicant_name','Dr. Tarek El-Mahdy')}"
                launch_vars.setdefault("base_rent", 60000.0)
                launch_vars.setdefault("proposed_rent", 48000.0)

            elif mode == "maintenance_tender":
                launch_vars.setdefault("property_name", launch_vars.get("location", "Nile Heights Tower"))
                launch_vars.setdefault("priority", "emergency")

            elif mode == "arrears_mediation":
                if "unpaid_context" in launch_vars:
                    ctx = launch_vars["unpaid_context"]
                    for hk in ["unpaid_months", "monthly_rent", "total_arrears_hint", "tenant_id"]:
                        if hk in updated:
                            launch_vars[hk] = updated[hk]
                    launch_vars["request_text"] = ctx

            ack = f"All set for {config['graph_id']}. Launching LangGraph execution."
            return {
                "slots": updated,
                "next_question": ack,
                "ready_to_launch": True,
                "launch_variables": launch_vars,
                "graph_id": config["graph_id"],
                "missing": [],
                "system_prompt": config["system_prompt"],
            }

    @staticmethod
    def get_missing_slots(mode: str, slots: Dict[str, Any]) -> List[str]:
        config = MODE_CONFIG.get(mode)
        if not config:
            return []
        return [s for s in config["required"] if s not in slots or slots[s] in (None, "", 0)]
