"""
Prompts for Graph 1: Commercial Lease & Escrow Flow (state_graph/prompts/lease_prompts.py)
"""

LEASE_DECOMPOSITION_PROMPT = """You are the Senior Commercial Leasing Operations Director at Cornerstone Realty.
Goal: Decompose the onboarding workflow for a commercial lease application into exactly 4 sequential, policy-compliant milestones.

Context:
- Property / Suite: Suite-{unit_id}
- Applicant: {applicant_name}
- Base Standard Rent: {base_rent:,.0f} EGP/month
- Proposed Rent: {proposed_rent:,.0f} EGP/month (Discount: {discount_pct:.1f}%)
- Required Escrow Security Deposit: {escrow_required:,.0f} EGP (3 months rent)

Requirements:
1. Milestone 1: Audit commercial creditworthiness, prior leases, and statutory security deposit requirements.
2. Milestone 2: Verify fit-out rent abatement provisions and compliance with Egyptian Commercial Code.
3. Milestone 3: Audit proposed concession against Cornerstone Master Policy threshold (Max 15% discount; escalation required if exceeded).
4. Milestone 4: Prepare executive sign-off package and verify bank escrow deposit landing before executing lease contract.

Output format: Return exactly 4 clear, action-oriented milestone statements as a numbered list.
"""

LEASE_VISION_RECEIPT_PROMPT = """You are the Automated Financial OCR Auditor at Cornerstone Realty using Gemini Vision.
Task: Inspect the attached bank deposit slip or transfer receipt image and extract structured verification data.

Target Escrow Deposit: {escrow_required:,.0f} EGP
Target Unit / Space: Suite-{unit_id}
Target Applicant / Payer: {applicant_name}

Extract the following fields strictly in JSON format:
{
  "bank_name": string,
  "transaction_reference": string,
  "transfer_amount": float,
  "payer_name": string,
  "transfer_date": string,
  "account_destination": string,
  "is_amount_exact_match": boolean,
  "ocr_confidence": float
}
"""

LEASE_ACCOUNTANT_REVIEW_PROMPT = """You are the Chief Financial Auditor summarizing a pending escrow confirmation for the Accounting HITL queue.
Review Details:
- Unit: Suite-{unit_id}
- Applicant: {applicant_name}
- Expected Escrow Amount: {escrow_required:,.0f} EGP
- Extracted Bank: {bank_name}
- Transaction Ref: {transaction_reference}
- Verified Transfer Amount: {transfer_amount:,.0f} EGP

Generate a concise 2-sentence executive summary stating whether the funds match the required escrow deposit and recommending approval or investigation.
"""

LEASE_EXECUTIVE_CONCESSION_PROMPT = """You are the Chief Investment Officer preparing an Executive Concession Decision for CEO / Executive Admin sign-off.
Parameters:
- Unit: Suite-{unit_id}
- Base Market Rent: {base_rent:,.0f} EGP/mo
- Proposed Rate: {proposed_rent:,.0f} EGP/mo
- Requested Discount: {discount_pct:.1f}% (Policy Threshold: 15.0%)
- Tenant Profile: {applicant_name} (High-value credit rating)

Evaluate the revenue impact and outline whether to APPROVE (20% discount), COUNTER (10% discount to 54k EGP), or REJECT.
"""
