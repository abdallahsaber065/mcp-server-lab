"""
Document Chunking and Ingestion Pipeline.
Chunks the 60-page Cornerstone Realty Legal Operations Binder into structured,
metadata-enriched sections (City, Section ID, Law Reference, Role).
"""

from typing import Any, Dict, List

from rag.vector_store import VectorStore

POLICY_BINDER_CORPUS = [
    {
        "section_id": "Section 1.1",
        "title": "Cairo & Alexandria Standard Leasing Bylaws",
        "content": "All residential leases within Cairo, Giza, and Alexandria are subject to standard tenancy agreements. Standard security deposit is equal to one month rent, refundable within 14 business days post move-out inspection.",
        "metadata": {"city": "Cairo", "doc_type": "bylaw", "section": "1.1", "role": "all"}
    },
    {
        "section_id": "Section 2.3",
        "title": "Property Access & Landlord Inspections",
        "content": "Property managers and landlords must provide at least 48 hours advance written notice before conducting routine inspections. Emergency access for active pipe leaks or electrical hazards requires no prior notice.",
        "metadata": {"city": "all", "doc_type": "bylaw", "section": "2.3", "role": "all"}
    },
    {
        "section_id": "Section 3.1",
        "title": "Routine Maintenance Turnaround SLA",
        "content": "Non-urgent plumbing, electrical, and cosmetic maintenance requests have a standard SLA turnaround of 48 hours during regular business days. Urgent leaks must be dispatched within 2 hours under Clause 8.1c.",
        "metadata": {"city": "all", "doc_type": "sla", "section": "3.1", "role": "maintenance"}
    },
    {
        "section_id": "Section 4.2b",
        "title": "Early Termination Penalties in Alexandria",
        "content": "Under Section 4.2b, early termination of a two-year residential lease in Alexandria requires 60 days written notice and a penalty fee equal to two months rent, unless caused by documented job relocation.",
        "metadata": {"city": "Alexandria", "doc_type": "legal_bylaw", "section": "4.2b", "role": "property_manager"}
    },
    {
        "section_id": "Section 5.4",
        "title": "Residential Paint and Wall Alterations",
        "content": "Tenants must obtain prior written consent for wall repainting. All paint work must use water-based eco-primer. Oil-based paints are strictly prohibited in residential towers due to respiratory allergy safety.",
        "metadata": {"city": "Cairo", "doc_type": "bylaw", "section": "5.4", "role": "all"}
    },
    {
        "section_id": "Section 6.2",
        "title": "Security Deposit Deductions & Banking Regulations",
        "content": "Security deposits must be held in an escrow sub-account at Banque Misr. Allowable deductions include unpaid utility bills, deep cleaning for smoking violations, and documented tenant-caused property damage.",
        "metadata": {"city": "Cairo", "doc_type": "finance", "section": "6.2", "role": "executive_admin"}
    },
    {
        "section_id": "Section 7.3",
        "title": "Commercial Subleasing & Municipal Compliance (Law 4/1996)",
        "content": "Commercial tenants with multi-year leases may sublease up to 40% floor space only with executive sign-off, an additional 1-month security deposit adjustment, and municipal commercial permits under Egyptian Law 4 of 1996.",
        "metadata": {"city": "Giza", "doc_type": "legal_statute", "section": "7.3", "law_ref": "Law 4 of 1996", "role": "executive_admin"}
    },
    {
        "section_id": "Section 8.1c",
        "title": "Emergency Night-Time Water Leak Protocols",
        "content": "Policy Clause 8.1c: For water leaks reported after 10:00 PM, on-call emergency contractors are dispatched within 2 hours. Property manager sign-off is automatically pre-authorized up to $1,500 for emergency containment.",
        "metadata": {"city": "all", "doc_type": "emergency_sla", "section": "8.1c", "role": "maintenance"}
    },
    {
        "section_id": "Section 8.2 & 9.1",
        "title": "Severe Environmental Hazard & Relocation Abatement",
        "content": "If toxic mold or severe structural hazard renders a unit uninhabitable, emergency remediation must start within 24 hours, tenant receives 50% rent abatement, and relocation to a comparable tower unit is mandated.",
        "metadata": {"city": "Cairo", "doc_type": "hazard_policy", "section": "8.2", "role": "property_manager"}
    },
    {
        "section_id": "Section 11.4",
        "title": "High-Value Lease Dispute Resolution & Arbitration",
        "content": "Disputes on commercial leases exceeding $20,000 annual rent follow a 10-day informal mediation, followed by executive review, and escalation to the Cairo Regional Centre for International Commercial Arbitration (CRCICA).",
        "metadata": {"city": "Cairo", "doc_type": "arbitration", "section": "11.4", "role": "executive_admin"}
    },
]


def build_and_seed_vector_store() -> VectorStore:
    vdb = VectorStore()
    for doc in POLICY_BINDER_CORPUS:
        vdb.upsert(payload=doc["content"], metadata=doc["metadata"])
    return vdb
