from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryUnitsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: Optional[int] = Field(None, description="Filter by property ID (1: Cornerstone Heights, 2: Alex Beachfront, 3: Giza Commercial)")
    city: Optional[Literal["Cairo", "Alexandria", "Giza"]] = Field(None, description="Filter properties by city location")

class LookupLeaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., description="Registered tenant email address to query active lease terms")

class MaintenanceRequestArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: int = Field(..., ge=1, description="Valid tenant ID submitting request")
    unit_id: int = Field(..., ge=1, description="Target unit ID where repair is needed")
    issue_description: str = Field(..., min_length=5, max_length=500, description="Detailed problem description")
    priority: Literal["low", "medium", "high", "urgent"] = Field("medium", description="Severity level of the issue")

class ModifyLeaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lease_id: int = Field(..., ge=1, description="Target lease contract ID")
    new_monthly_rent: float = Field(..., gt=0, description="Proposed monthly rent amount")
    duration_months: int = Field(..., ge=1, le=36, description="Lease duration in months")
    executive_approval_given: bool = Field(False, description="Whether executive sign-off has been provided via human elicitation")

class BatchAuditArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: int = Field(..., ge=1, description="Property ID to audit for compliance")
    include_expired_leases: bool = Field(True, description="Whether to include historical expired leases in audit report")
