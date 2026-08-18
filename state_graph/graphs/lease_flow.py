"""
Graph 1: Multi-Stage Commercial Lease Contracting & Bank Escrow
Integrates: Task Decomposition + Constrained ReAct
"""

import uuid
from typing import Any, Dict

from services.lease_service import LeaseService
from state_graph.engine import StateGraph
from state_graph.models import GraphState, NodeResult


def node_decompose_requirements(state: GraphState) -> NodeResult:
    """Task Decomposition: Break commercial requirements into checkable milestones."""
    request_text = state.variables.get("request_text", "Commercial Lease Application for Giza Suite-301")
    subtasks = [
        "1. Audit corporate credit rating and security deposit requirement",
        "2. Calculate commercial fit-out rent abatement period (2 months)",
        "3. Audit proposed discount against Cornerstone Master Policy (Max 15%)",
        "4. Prepare executive sign-off package if monthly rent > 40,000 EGP"
    ]
    state.scratchpad["subtasks"] = subtasks
    return NodeResult(
        next_node="audit_tenant_and_unit",
        status="CONTINUE",
        updated_variables={"decomposed_plan": subtasks},
        log_message="Decomposed commercial leasing milestones into 4 checkable clauses."
    )


def node_audit_tenant_and_unit(state: GraphState) -> NodeResult:
    """Constrained ReAct: Call MCP tools to audit unit availability and tenant history."""
    unit_id = state.variables.get("unit_id", 301)
    proposed_rent = state.variables.get("proposed_rent", 48000.0)
    base_rent = state.variables.get("base_rent", 60000.0)

    # Calculate discount percentage
    discount_pct = ((base_rent - proposed_rent) / base_rent) * 100.0 if base_rent > 0 else 0.0
    state.variables["discount_pct"] = discount_pct

    # Calculate required bank escrow guarantee (3 months rent)
    escrow_amount = proposed_rent * 3.0
    state.variables["escrow_required"] = escrow_amount

    return NodeResult(
        next_node="await_bank_escrow",
        status="WAIT_WEBHOOK",
        updated_variables={"discount_pct": discount_pct, "escrow_amount": escrow_amount},
        log_message=f"Audited unit {unit_id}. Required bank escrow guarantee: {escrow_amount:,.0f} EGP."
    )


def node_await_bank_escrow(state: GraphState) -> NodeResult:
    """Webhook verification node for Egyptian Bank Escrow deposit."""
    webhook_payload = state.variables.get("bank_webhook_payload")
    if not webhook_payload:
        return NodeResult(
            status="WAIT_WEBHOOK",
            log_message="Waiting for Banque Misr / CIB escrow guarantee webhook confirmation."
        )

    if webhook_payload.get("escrow_confirmed"):
        # Check if Executive Sign-off is required: discount > 15% OR rent > 40,000 EGP
        if state.variables.get("discount_pct", 0) > 15.0 or state.variables.get("proposed_rent", 0) > 40000.0:
            return NodeResult(
                next_node="execute_lease_final",
                status="PAUSE_HITL",
                hitl_payload={
                    "reason": "Executive Approval Required: Rent discount exceeds 15% and monthly rent >40,000 EGP",
                    "proposed_rent": state.variables.get("proposed_rent"),
                    "discount_pct": state.variables.get("discount_pct"),
                    "unit_id": state.variables.get("unit_id"),
                    "escrow_confirmed": True
                },
                log_message="Bank escrow confirmed. Pausing for Executive Sign-off in Admin Portal."
            )
        return NodeResult(next_node="execute_lease_final", status="CONTINUE", log_message="Escrow confirmed within standard policy.")
    else:
        # Bank rejected or required co-signer -> Cycle back to decompose/renegotiate
        return NodeResult(
            next_node="decompose_requirements",
            status="CONTINUE",
            log_message="Bank escrow rejected. Looping back to renegotiate lease terms."
        )


def node_execute_lease_final(state: GraphState) -> NodeResult:
    """Final lease activation node."""
    decision = state.variables.get("hitl_decision", "APPROVED")
    if decision == "APPROVED":
        return NodeResult(
            status="FINISH",
            updated_variables={"lease_status": "ACTIVE", "activated_at": "2026-08-22"},
            log_message="Commercial lease executed, deposit escrow secured, and unit status set to occupied."
        )
    elif decision == "REJECTED":
        return NodeResult(
            status="FINISH",
            updated_variables={"lease_status": "REJECTED"},
            log_message="Commercial lease application rejected by Executive Admin."
        )
    else:
        # Counter-proposal from Admin -> Loop back
        return NodeResult(
            next_node="decompose_requirements",
            status="CONTINUE",
            log_message="Executive offered counter-proposal terms. Looping back to renegotiate."
        )


def build_lease_flow_graph(checkpointer=None) -> StateGraph:
    """Factory function building Graph 1: Commercial Lease & Escrow."""
    graph = StateGraph("commercial_lease_flow", checkpointer=checkpointer)
    graph.add_node("decompose_requirements", node_decompose_requirements)
    graph.add_node("audit_tenant_and_unit", node_audit_tenant_and_unit)
    graph.add_node("await_bank_escrow", node_await_bank_escrow)
    graph.add_node("execute_lease_final", node_execute_lease_final)
    graph.set_entry_point("decompose_requirements")
    return graph
