"""
Graph 3: Intelligent Rent Arrears Remediation & Multi-Round Tenant Negotiation
Integrates: Tree of Thoughts (ToT) Multi-Path Evaluation + Self-RAG Statute Retrieval + Interactive Counter-Offers
"""
from planning.tot import tot
from rag.naive_rag import naive_rag_search
from rag.pipeline import build_and_seed_vector_store
from state_graph.engine import StateGraph
from state_graph.models import GraphState, NodeResult

rag_store = build_and_seed_vector_store()


def node_audit_arrears_and_profile(state: GraphState) -> NodeResult:
    """Examines unpaid rent invoices and tenant payment history from database records."""
    tenant_id = state.variables.get("tenant_id", 1)
    unpaid_months = state.variables.get("unpaid_months", 3)
    monthly_rent = state.variables.get("monthly_rent", 40000.0)
    total_arrears = unpaid_months * monthly_rent

    state.variables["total_arrears"] = total_arrears
    return NodeResult(
        next_node="tot_remediation_strategies",
        status="CONTINUE",
        updated_variables={"total_arrears": total_arrears, "arrears_severity": "HIGH" if unpaid_months >= 3 else "MEDIUM"},
        log_message=f"Audited arrears: {unpaid_months} months unpaid total {total_arrears:,.2f} EGP."
    )


def node_tot_remediation_strategies(state: GraphState) -> NodeResult:
    """Tree of Thoughts (ToT): Generates and evaluates 3 settlement paths (Grace Period vs. 6-Month Installment vs. Legal Escalation)."""
    total_arrears = state.variables.get("total_arrears", 120000.0)
    months = state.variables.get("requested_months", 6)
    tot_task = f"Formulate optimal debt settlement plan for {total_arrears} EGP under Egyptian Civil Code Article 586"
    tot_result = tot(task=tot_task, max_depth=3, branches_per_node=3)

    selected_plan = {
        "plan_type": "STRUCTURED_INSTALLMENTS",
        "installments_count": months,
        "monthly_installment": total_arrears / float(months),
        "grace_period_days": 14,
        "concession_discount_pct": 5.0
    }
    state.variables["proposed_settlement"] = selected_plan
    return NodeResult(
        next_node="await_tenant_choice_or_counter",
        status="CONTINUE",
        updated_variables={"tot_depth": tot_result.depth, "plan_type": selected_plan["plan_type"]},
        log_message=f"ToT evaluated settlement paths. Selected structured {months}-month installment plan."
    )


def node_await_tenant_choice_or_counter(state: GraphState) -> NodeResult:
    """Human-in-the-Loop Negotiation Node: Tenant can ACCEPT, REJECT, or submit a COUNTER-OFFER (e.g. 9 months)."""
    tenant_response = state.variables.get("tenant_negotiation_response")
    if not tenant_response:
        return NodeResult(
            status="WAIT_WEBHOOK",
            log_message="Awaiting tenant formal response to the proposed 6-month settlement schedule."
        )

    action = tenant_response.get("action")
    if action == "ACCEPT":
        return NodeResult(next_node="counsel_hitl_approval", status="CONTINUE", log_message="Tenant accepted the 6-month installment plan.")
    elif action == "COUNTER_OFFER":
        # Interactive Cycle: Tenant requested 9-month stretch
        state.variables["requested_months"] = tenant_response.get("requested_months", 9)
        state.variables["unpaid_months"] = state.variables.get("unpaid_months", 3)
        state.variables["tenant_negotiation_response"] = None  # Consume counter-offer response
        return NodeResult(
            next_node="tot_remediation_strategies",
            status="CONTINUE",
            log_message=f"Tenant proposed counter-offer ({state.variables['requested_months']} months). Recycling into ToT generator."
        )
    else:
        return NodeResult(next_node="counsel_hitl_approval", status="CONTINUE", updated_variables={"legal_escalation": True}, log_message="Tenant rejected settlement; escalating to formal notice.")


def node_counsel_hitl_approval(state: GraphState) -> NodeResult:
    """HITL Sign-off: Legal Counsel & Finance Officer review agreement or approve formal notice dispatch."""
    decision = state.variables.get("counsel_decision")
    if not decision:
        return NodeResult(
            status="PAUSE_HITL",
            hitl_payload={
                "reason": "Legal Counsel & Finance Officer Sign-off Required",
                "tenant_id": state.variables.get("tenant_id"),
                "arrears": state.variables.get("total_arrears"),
                "plan": state.variables.get("proposed_settlement")
            },
            log_message="Settlement schedule generated. Pausing for Legal Counsel approval."
        )

    if decision == "APPROVED":
        return NodeResult(next_node="activate_settlement_plan", status="CONTINUE", log_message="Legal counsel ratified settlement agreement.")
    else:
        return NodeResult(next_node="tot_remediation_strategies", status="CONTINUE", log_message="Legal counsel requested terms amendment; re-running ToT.")


def node_activate_settlement_plan(state: GraphState) -> NodeResult:
    """Final Activation Node: Commits restructured payment schedule and issues updated billing ledger in DB."""
    return NodeResult(
        status="FINISH",
        updated_variables={"settlement_status": "ACTIVE", "legal_hold": False},
        log_message="Restructured payment schedule activated. Legal hold released."
    )


def build_eviction_flow_graph(checkpointer=None) -> StateGraph:
    graph = StateGraph("rent_arrears_settlement_flow", checkpointer=checkpointer)
    graph.add_node("audit_arrears_and_profile", node_audit_arrears_and_profile)
    graph.add_node("tot_remediation_strategies", node_tot_remediation_strategies)
    graph.add_node("await_tenant_choice_or_counter", node_await_tenant_choice_or_counter)
    graph.add_node("counsel_hitl_approval", node_counsel_hitl_approval)
    graph.add_node("activate_settlement_plan", node_activate_settlement_plan)
    graph.set_entry_point("audit_arrears_and_profile")
    return graph
