from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field


class QueryUnitsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: Optional[int] = Field(None, description="Filter by property ID (1: Nile Plaza, 2: Zamalek Royal, etc.)")
    city: Optional[Literal["Cairo", "Alexandria", "Giza", "New Cairo", "Hurghada"]] = Field(None, description="Filter properties by city location")


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


class BookTourArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: int = Field(..., ge=1, description="Target property ID to tour")
    contact_name: str = Field(..., min_length=2, description="Prospect or tenant full name")
    contact_email: str = Field(..., min_length=5, description="Contact email address")
    requested_date: str = Field(..., description="Desired tour date in YYYY-MM-DD format")
    time_slot: str = Field(..., description="Desired time slot, e.g. '14:00' or '10:30 AM'")
    unit_id: Optional[int] = Field(None, description="Optional specific unit ID to view")
    tour_type: Literal["in_person", "virtual_guided", "3d_self_guided"] = Field("in_person", description="Type of tour requested")
    contact_phone: Optional[str] = Field(None, description="Optional contact phone number")
    notes: Optional[str] = Field(None, description="Any specific accessibility or viewing preferences")


class ListToursArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: Optional[int] = Field(None, description="Filter tour bookings by property ID")
    status: Optional[Literal["pending", "confirmed", "rescheduled", "completed", "cancelled"]] = Field(None, description="Filter by booking status")


class UpdateTourStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: int = Field(..., ge=1, description="Tour booking ID to update")
    status: Literal["confirmed", "rescheduled", "completed", "cancelled"] = Field(..., description="New status for the booking")
    manager_notes: Optional[str] = Field(None, description="Internal manager notes or reason for status update")
