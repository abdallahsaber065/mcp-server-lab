"""
Maintenance Flow State Schemas (state_graph/schemas/maintenance_schema.py)
"""
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class ContractorProposal(BaseModel):
    contractor_id: str
    name: str
    speed_hours: int
    quote_amount: float
    warranty_months: int
    composite_score: float = 0.0


class MaintenanceState(TypedDict, total=False):
    location: str
    issue_description: str
    property_name: str
    liability: str
    sla_hours: int
    top_contractor: str
    estimate: float
    vendor_matrix: List[Dict[str, Any]]
    engineer_approved: bool
    engineer_notes: Optional[str]
    contractor_available: bool
    tenant_rating: int
    status: str
    history_log: Annotated[List[str], operator.add]
    selected_contractor: Optional[str]
