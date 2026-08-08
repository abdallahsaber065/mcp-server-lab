"""
40-Turn Long-Context Test Suite for Cornerstone Realty.
Constructs 10 realistic variations where a critical early constraint
(e.g., Turn 3 paint fume allergy, security deposit waiver, or specific Nile view clause)
is buried under 30+ large property/lease JSON tool outputs.
"""

from typing import Any, Dict, List, Tuple


def generate_long_context_transcript(variation_id: int = 1) -> Tuple[List[Dict[str, Any]], str]:
    """
    Generate a 40-turn transcript.
    Returns (messages, expected_critical_detail).
    """
    critical_details = [
        "Tenant has severe respiratory allergy to oil-based paint fumes; water-based eco-primer required.",
        "Agreed security deposit concession: $2,000 split across first two quarters.",
        "Lease clause 14.b waiver: Tenant permitted 2 indoor domestic cats with pet addendum.",
        "Tenant requires dedicated ground-floor accessible parking bay due to mobility restriction.",
        "Commercial unit 501 agreed rent grace period: 45 days for HVAC fit-out works.",
        "Pre-approved sublease authorization for up to 35% floor area under Law 4/1996.",
        "Tenant payment schedule locked to quarterly wire transfers via Banque Misr.",
        "Late fee exemption granted for first 5 business days of each calendar month.",
        "Unit 304 plumbing warranty: Contractor liable for all pipe repairs through Dec 2026.",
        "Executive sign-off obtained: 10% rent discount applied to 3-year commercial commitment."
    ]

    target_fact = critical_details[(variation_id - 1) % len(critical_details)]
    messages: List[Dict[str, Any]] = []

    # Turn 1: Welcome & inquiry
    messages.append({"role": "user", "content": "Hello, I am inquiring about leasing and maintenance policies for our Cairo units."})
    messages.append({"role": "assistant", "content": "Welcome to Cornerstone Realty Group. How can I assist you today with our properties?"})

    # Turn 3: CRITICAL DETAIL INJECTED EARLY
    messages.append({"role": "user", "content": f"Important note for our file: {target_fact}"})
    messages.append({"role": "assistant", "content": "Noted and recorded in our active tenant working state."})

    # Turns 5 to 38: 34 Turns of realistic, heavy tool queries & large JSON payloads
    for i in range(5, 39, 2):
        tool_name = "query_units" if i % 4 == 0 else "lookup_lease"
        large_json_payload = (
            f'{{"property_id": {i}, "city": "Cairo", "units": [' +
            ", ".join([f'{{"unit_id": {i*10 + j}, "bedrooms": 3, "monthly_rent": 15000, "status": "available", "specs": "Nile Tower Floor {j}"}}' for j in range(15)]) +
            f'], "audit_log": "Inspection completed on 2026-03-01 for all {i} residential units in block B."}}'
        )

        messages.append({
            "role": "assistant", 
            "content": f"Calling tool {tool_name} to inspect available inventory across Cairo and Alexandria."
        })
        messages.append({
            "role": "tool",
            "name": tool_name,
            "content": large_json_payload
        })

    # Turn 39 & 40: The final inquiry testing memory recall
    messages.append({
        "role": "user", 
        "content": "Before we finalize the lease agreement and maintenance schedule, are there any special allergies, concessions, or waivers recorded on this file?"
    })

    return messages, target_fact
