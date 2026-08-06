"""
12 Domain-Specific Test Questions for Cornerstone Realty Legal & Policy Binder.
Categories:
  1. General Policy Questions (favors Naive RAG)
  2. Citation & Statute Questions (favors Hybrid Search)
  3. Multi-Hop / Decomposition Questions (favors Agentic & Graph RAG)
"""

TEST_QUESTIONS = [
    # Category 1: General Policy Questions (4 Questions)
    {
        "id": "Q1_GEN",
        "category": "general",
        "query": "What is the standard routine maintenance turnaround time for non-urgent plumbing requests?",
        "expected_keywords": ["48 hours", "business days", "routine maintenance", "Section 3.1"],
    },
    {
        "id": "Q2_GEN",
        "category": "general",
        "query": "What are the rules regarding tenant repainting and wall modifications in residential units?",
        "expected_keywords": ["prior written consent", "water-based primer", "original condition", "Section 5.4"],
    },
    {
        "id": "Q3_GEN",
        "category": "general",
        "query": "How many days in advance must a landlord provide notice before a routine property inspection?",
        "expected_keywords": ["48 hours", "advance notice", "Section 2.3", "inspection"],
    },
    {
        "id": "Q4_GEN",
        "category": "general",
        "query": "What is the security deposit refund timeline after move-out inspection in Cairo properties?",
        "expected_keywords": ["14 business days", "deposit refund", "deductions", "Section 6.2"],
    },

    # Category 2: Exact Citation & Statute Questions (4 Questions)
    {
        "id": "Q5_CIT",
        "category": "citation",
        "query": "What does Section 4.2b say regarding early termination penalty fees for 2-year residential leases in Alexandria?",
        "expected_keywords": ["Section 4.2b", "two months rent penalty", "60 days written notice", "Alexandria"],
    },
    {
        "id": "Q6_CIT",
        "category": "citation",
        "query": "Under Egyptian Tenancy Law 4 of 1996, what governs annual rent escalation caps for commercial units?",
        "expected_keywords": ["Law 4 of 1996", "contractual agreement", "escalation cap", "Article 3"],
    },
    {
        "id": "Q7_CIT",
        "category": "citation",
        "query": "What does Policy Clause 8.1c specify for emergency water leaks occurring after 10:00 PM?",
        "expected_keywords": ["Policy Clause 8.1c", "2-hour emergency dispatch", "on-call contractor"],
    },
    {
        "id": "Q8_CIT",
        "category": "citation",
        "query": "According to Bylaw Form CR-802, what documentation is required for corporate tenant lease guarantees?",
        "expected_keywords": ["Form CR-802", "commercial registry", "tax card", "board resolution"],
    },

    # Category 3: Multi-Hop / Decomposition Questions (4 Questions)
    {
        "id": "Q9_HOP",
        "category": "multi_hop",
        "query": "For a commercial tenant in Giza with a 3-year lease wanting to sublease 40% of their floor area to a medical clinic, what pre-approvals, deposit adjustments, and legal notices apply under Section 7.3 and Law 4/1996?",
        "expected_keywords": ["Section 7.3", "executive sign-off", "additional 1-month deposit", "Law 4/1996", "municipal commercial permit"],
    },
    {
        "id": "Q10_HOP",
        "category": "multi_hop",
        "query": "If a residential tenant in Cairo reports severe black mold in Unit 402, what emergency repair SLAs, rent abatement percentages, and temporary relocation provisions are triggered across Section 8.2 and Section 9.1?",
        "expected_keywords": ["24-hour remediation", "50% rent abatement", "relocation to comparable unit", "Section 8.2", "Section 9.1"],
    },
    {
        "id": "Q11_HOP",
        "category": "multi_hop",
        "query": "What is the complete dispute resolution chain when a high-value lease tenant disputes a $5,000 HVAC replacement charge, including informal mediation, property manager sign-off, and formal arbitration under Egyptian Law?",
        "expected_keywords": ["10-day mediation", "executive approval", "arbitration tribunal", "Section 11.4"],
    },
    {
        "id": "Q12_HOP",
        "category": "multi_hop",
        "query": "When converting a residential lease to a live-work office in Alexandria, what municipal approvals, insurance riders, and building bylaws under Section 4.5 and Section 12.1 must be fulfilled?",
        "expected_keywords": ["commercial rider", "building syndicate consent", "Section 4.5", "Section 12.1", "Alexandria municipality"],
    },
]
