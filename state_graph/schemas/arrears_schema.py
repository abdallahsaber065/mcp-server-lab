"""
Arrears Flow State Schemas (state_graph/schemas/arrears_schema.py)
"""
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class RestructuringOption(BaseModel):
    option_id: str
    title: str
    monthly_installment: float
    duration_months: int
    discount_applied: float = 0.0
    description: str


class ArrearsState(TypedDict, total=False):
    tenant_id: int
    unpaid_months: int
    monthly_rent: float
    total_arrears: float
    tenant_risk: str
    dynamic_offers: List[Dict[str, Any]]
    tenant_choice: Optional[str]
    custom_proposal: Optional[Dict[str, Any]]
    legal_approved: bool
    legal_notes: Optional[str]
    status: str
    history_log: Annotated[List[str], operator.add]
    waited_days: int
