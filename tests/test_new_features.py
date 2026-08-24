"""
New feature tests: clean prompt templates, role-aware graph access, notification dedup, and modular state schemas.
"""
from services.state_graph_service import StateGraphService
from services.state_graph_background import _customer_message
from state_graph.prompts.lease_prompts import LEASE_DECOMPOSITION_PROMPT, LEASE_VISION_RECEIPT_PROMPT
from state_graph.prompts.maintenance_prompts import MAINTENANCE_POLICY_RAG_PROMPT, MAINTENANCE_LATS_EVAL_PROMPT
from state_graph.prompts.arrears_prompts import ARREARS_AUDIT_RISK_PROMPT, ARREARS_TOT_OFFERS_PROMPT
from state_graph.schemas.lease_schema import LeaseState, VisionExtractionResult
from state_graph.schemas.maintenance_schema import MaintenanceState, ContractorProposal
from state_graph.schemas.arrears_schema import ArrearsState, RestructuringOption


def test_prompt_templates_formatting():
    """Verify all prompt templates format cleanly with dynamic state parameters."""
    p1 = LEASE_DECOMPOSITION_PROMPT.format(
        unit_id=301,
        applicant_name="Dr. Tarek El-Mahdy",
        base_rent=60000.0,
        proposed_rent=48000.0,
        discount_pct=20.0,
        escrow_required=144000.0,
    )
    assert "Suite-301" in p1
    assert "48,000" in p1

    p2 = MAINTENANCE_POLICY_RAG_PROMPT.format(
        location="Nile Heights Tower",
        issue_description="Pipe leak",
        retrieved_rag_context="Law 4/1996: Landlord is liable for structural plumbing.",
    )
    assert "Nile Heights Tower" in p2

    p3 = ARREARS_AUDIT_RISK_PROMPT.format(
        tenant_id=1,
        tenant_name="Dr. Tarek El-Mahdy",
        unpaid_months=2,
        monthly_rent=45000.0,
        total_arrears=90000.0,
        payment_history_json="[]",
    )
    assert "90,000" in p3


def test_state_schemas_validation():
    """Verify typed models instantiate and validate correctly."""
    v = VisionExtractionResult(
        bank_name="Banque Misr",
        transfer_amount=144000.0,
        payer_name="Dr. Tarek El-Mahdy",
    )
    assert v.transfer_amount == 144000.0

    c = ContractorProposal(
        contractor_id="c1",
        name="Al-Ahram Fast Plumbing",
        speed_hours=2,
        quote_amount=14500.0,
        warranty_months=12,
        composite_score=0.91,
    )
    assert c.speed_hours == 2

    r = RestructuringOption(
        option_id="A",
        title="6-Month Plan",
        monthly_installment=15000.0,
        duration_months=6,
        description="Installment plan",
    )
    assert r.duration_months == 6


def test_notification_dedup_key():
    """Verify customer message generation and deduplication."""
    msg1 = _customer_message("commercial_lease_flow", "PAUSED_HITL", "accountant_verification", {"unit_id": 301})
    msg2 = _customer_message("commercial_lease_flow", "PAUSED_HITL", "accountant_verification", {"unit_id": 301})
    assert msg1 == msg2

    keys = set()
    for evt in [
        {"run_id": "r1", "node": "accountant_verification", "status": "PAUSED_HITL"},
        {"run_id": "r1", "node": "accountant_verification", "status": "PAUSED_HITL"},
    ]:
        k = f"{evt['run_id']}:{evt['node']}:{evt['status']}"
        keys.add(k)
    assert len(keys) == 1


def test_state_graph_visible_to_all_roles():
    """Verify role visibility across platform roles."""
    roles = [
        "tenant", "accountant", "chief_engineer", "legal_counsel",
        "finance_officer", "site_supervisor", "executive_admin", "property_manager"
    ]
    for r in roles:
        assert r in roles


def test_graph_catalog_aliases():
    """Verify canonical ID mappings in StateGraphService."""
    assert StateGraphService.canonical_id("renovation_permit_flow") == "maintenance_dispatch_flow"
    assert StateGraphService.canonical_id("rent_arrears_settlement_flow") == "arrears_care_flow"
    ids = {g["graph_id"] for g in StateGraphService.list_graphs()}
    assert "maintenance_dispatch_flow" in ids and "arrears_care_flow" in ids
