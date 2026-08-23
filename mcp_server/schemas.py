from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field


class QueryUnitsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: Optional[int] = Field(None, description="Filter by property ID (1: Nile Plaza, 2: Zamalek Royal, etc.)")
    city: Optional[Literal["Cairo", "Alexandria", "Giza", "New Cairo", "Hurghada"]] = Field(None, description="Filter properties by city location")


class LookupLeaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., description="Registered tenant email address to query lease contracts")
    active_only: bool = Field(False, description="If true, return only currently active leases")


class MaintenanceRequestArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: int = Field(..., ge=1, description="Valid tenant ID submitting request")
    unit_id: int = Field(..., ge=1, description="Target unit ID where repair is needed")
    issue_description: str = Field(..., min_length=5, max_length=500, description="Detailed problem description")
    priority: Literal["low", "medium", "high", "urgent"] = Field("medium", description="Severity level of the issue")
    preferred_time_slot: Optional[str] = Field(None, description="Preferred arrival window (e.g. '09:00 AM - 12:00 PM')")


class ModifyLeaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lease_id: int = Field(..., ge=1, description="Target lease contract ID")
    new_monthly_rent: float = Field(..., gt=0, description="Proposed monthly rent amount")
    duration_months: int = Field(..., ge=1, le=36, description="Lease duration in months")
    executive_approval_given: bool = Field(False, description="Whether executive sign-off has been provided via human elicitation")


class RenewLeaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lease_id: int = Field(..., ge=1, description="Target lease ID to request renewal for")
    extension_months: int = Field(12, ge=6, le=36, description="Desired renewal extension period in months")
    notes: Optional[str] = Field(None, description="Additional renewal terms or requests")


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


class CancelTourArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: int = Field(..., ge=1, description="Booking ID of the tour to cancel")
    cancellation_reason: Optional[str] = Field("User requested cancellation", description="Reason for cancelling the viewing appointment")


class RescheduleTourArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: int = Field(..., ge=1, description="Booking ID of the tour to reschedule")
    new_date: str = Field(..., description="New desired tour date in YYYY-MM-DD format")
    new_time_slot: str = Field(..., description="New desired time slot (e.g. '11:00 AM' or '15:30')")
    notes: Optional[str] = Field(None, description="Reason or additional instructions for reschedule")


class ListToursArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: Optional[int] = Field(None, description="Filter tour bookings by property ID")
    status: Optional[Literal["pending", "confirmed", "rescheduled", "completed", "cancelled"]] = Field(None, description="Filter by booking status")
    contact_email: Optional[str] = Field(None, description="Filter tour bookings for a specific contact email")


class UpdateTourStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: int = Field(..., ge=1, description="Tour booking ID to update")
    status: Literal["confirmed", "rescheduled", "completed", "cancelled"] = Field(..., description="New status for the booking")
    manager_notes: Optional[str] = Field(None, description="Internal manager notes or reason for status update")


class SubmitLeaseApplicationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit_id: int = Field(..., ge=1, description="Target unit ID to apply for")
    applicant_name: str = Field(..., min_length=2, description="Full legal name of the applicant")
    applicant_email: str = Field(..., min_length=5, description="Contact email address")
    proposed_monthly_rent: float = Field(..., gt=0, description="Offered or agreed monthly rental rate in EGP")
    lease_duration_months: int = Field(12, ge=6, le=36, description="Desired lease term length in months")
    move_in_date: str = Field(..., description="Target move-in date in YYYY-MM-DD format")
    applicant_phone: Optional[str] = Field(None, description="Mobile contact phone number")
    employment_details: Optional[str] = Field(None, description="Occupation, employer, or corporate entity name")


class ListPaymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: Optional[int] = Field(None, ge=1, description="Filter payments for a specific tenant ID")
    lease_id: Optional[int] = Field(None, ge=1, description="Filter payments for a specific lease contract ID")


class PayRentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lease_id: int = Field(..., ge=1, description="Lease ID the payment is applied toward")
    tenant_id: int = Field(..., ge=1, description="Tenant ID making the payment")
    amount: float = Field(..., gt=0, description="Payment installment amount in EGP")
    payment_method: Literal["credit_card", "fawry", "bank_transfer", "cash"] = Field("credit_card", description="Payment channel")
    notes: Optional[str] = Field(None, description="Optional payment remarks or transaction note")


class GetMyMaintenanceRequestsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: int = Field(..., ge=1, description="Tenant ID whose maintenance tickets to retrieve")
    status: Optional[Literal["open", "dispatched", "in_progress", "resolved", "cancelled"]] = Field(None, description="Optional status filter")
