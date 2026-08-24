"""
Lease Flow State Schemas (state_graph/schemas/lease_schema.py)
"""
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class VisionExtractionResult(BaseModel):
    bank_name: str = Field(default="Banque Misr")
    transaction_reference: str = Field(default="TXN-MISR-998822")
    transfer_amount: float = Field(default=144000.0)
    payer_name: str = Field(default="Dr. Tarek El-Mahdy")
    transfer_date: str = Field(default="2026-08-25")
    account_destination: str = Field(default="Cornerstone Realty Escrow #EG880002")
    is_amount_exact_match: bool = Field(default=True)
    ocr_confidence: float = Field(default=0.98)


class LeaseState(TypedDict, total=False):
    unit_id: int
    base_rent: float
    proposed_rent: float
    applicant_name: str
    applicant_email: str
    receipt_image_urls: List[str]
    decomposed_milestones: List[str]
    discount_pct: float
    escrow_required: float
    unit_verified: bool
    vision_extracted: Optional[Dict[str, Any]]
    accountant_verified: bool
    accountant_notes: Optional[str]
    executive_decision: Optional[str]
    executive_notes: Optional[str]
    lease_status: str
    status: str
    history_log: Annotated[List[str], operator.add]
    failure_ticket_id: Optional[str]
    hitl_decision: Optional[str]
    accountant_confirmation: Optional[Dict[str, Any]]
    bank_webhook_payload: Optional[Dict[str, Any]]
