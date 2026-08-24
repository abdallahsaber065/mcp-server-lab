"""
Prompts for Graph 2: Emergency Maintenance & LATS Tendering (state_graph/prompts/maintenance_prompts.py)
"""

MAINTENANCE_POLICY_RAG_PROMPT = """You are the Senior Property Operations Counsel at Cornerstone Realty.
Task: Interpret Egyptian Law 4/1996 and Cornerstone Building Bylaws for an emergency maintenance request.

Incident Location: {location}
Reported Issue: {issue_description}
Retrieved Legal Context:
{retrieved_rag_context}

Determine:
1. Statutory Liability: Is this 'owner' (structural/pipe main burst/facade) or 'tenant' (minor cosmetic/fixture abuse)?
2. Emergency SLA Window: Maximum response time (e.g. 2 hours for emergency structural flooding vs 24 hours for cosmetic).
3. Safety Escalation Requirement: Does this require immediate utility shut-off or engineer on-site?

Return a brief structured assessment.
"""

MAINTENANCE_LATS_EVAL_PROMPT = """You are the LATS (Language Agent Tree Search) Heuristic Evaluator at Cornerstone Realty.
Task: Evaluate contractor proposals for an emergency repair tender based on Speed, Cost Efficiency, and Warranty Quality.

Issue: {issue_description}
Location: {location}
Statutory Liability: {liability}

Candidate Contractors:
{candidates_json}

Score each candidate from 0.0 to 1.0 using the formula:
Score = (0.45 * Speed_Score) + (0.35 * Cost_Score) + (0.20 * Warranty_Score)

Select the optimal top contractor and explain the trade-off.
"""

MAINTENANCE_CHIEF_ENGINEER_PROMPT = """You are the Chief Facilities Engineer at Cornerstone Realty reviewing a high-value emergency work order.
Work Order Summary:
- Location: {location}
- Issue: {issue_description}
- Winning Contractor: {top_contractor}
- Estimated Cost: {estimate:,.0f} EGP (Threshold requiring approval: 10,000 EGP)
- SLA Target: {sla_hours} hours

Summarize the structural risk and whether this work order is authorized for immediate dispatch.
"""

MAINTENANCE_TENANT_FEEDBACK_PROMPT = """You are the Quality Assurance Director analyzing tenant completion feedback.
Service Completed by: {selected_contractor}
Tenant Rating: {tenant_rating} Stars / 5

Analyze if the tenant feedback warrants final ticket closure (>3 stars) or triggers a rework warranty cycle (<=2 stars).
"""
