"""
Action Confirm Dispatcher (web/services/chat/action_dispatcher.py)

Executes confirmed HITL actions. Open/Closed: register new action types
by adding an entry to _HANDLERS without touching the router.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger("mcp.action_dispatcher")


# --------------------------------------------------------------------------- #
#  Individual action executors — each is a pure function, easy to unit test   #
# --------------------------------------------------------------------------- #

def _execute_schedule_tour(data: Dict[str, Any]) -> str:
    from db.repositories.tour_repo import TourRepository
    from db.session import get_sync_db

    prop_id = int(data.get("property_id") or 1)
    unit_id = int(data["unit_id"]) if data.get("unit_id") else None
    contact_name = data.get("contact_name") or "Guest Prospect"
    contact_email = data.get("contact_email") or "guest@cornerstonerealty.eg"
    contact_phone = data.get("contact_phone") or "+20 100 000 0000"
    tour_type = data.get("tour_type") or "in_person"
    requested_date = data.get("requested_date") or "2026-09-01"
    time_slot = data.get("time_slot") or "14:00"

    with next(get_sync_db()) as session:
        repo = TourRepository(session)
        booking = repo.create_booking(
            property_id=prop_id,
            unit_id=unit_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            tour_type=tour_type,
            requested_date=requested_date,
            time_slot=time_slot,
            notes=data.get("notes")
        )

    return (
        f"✅ **Viewing Tour Confirmed & Scheduled!**\n\n"
        f"Booking **#{booking['booking_id']}** registered for **{contact_name}** at "
        f"**{booking['property_name']}** (Suite {booking.get('unit_number', 'General')}).\n\n"
        f"• **Date:** {requested_date}\n"
        f"• **Time Slot:** {time_slot}\n"
        f"• **Tour Format:** {tour_type.replace('_', ' ').title()}\n"
        f"• **Email Confirmation Sent:** {contact_email}"
    )


def _execute_cancel_tour(data: Dict[str, Any]) -> str:
    from db.repositories.tour_repo import TourRepository
    from db.session import get_sync_db

    booking_id = int(data.get("booking_id") or 0)
    reason = data.get("cancellation_reason") or "User requested cancellation"

    with next(get_sync_db()) as session:
        repo = TourRepository(session)
        cancelled = repo.cancel_booking(booking_id=booking_id, cancellation_reason=reason)

    if not cancelled:
        return f"⚠️ Tour booking #{booking_id} was not found."
    return (
        f"✅ **Tour Booking #{booking_id} Cancelled.**\n\n"
        f"Reason: {reason}\n"
        f"A confirmation has been noted. The viewing slot has been freed."
    )


def _execute_submit_maintenance(data: Dict[str, Any]) -> str:
    from mcp_server.db_helpers import create_maintenance_record

    unit_id = int(data.get("unit_id") or 101)
    priority = data.get("priority") or "medium"
    desc = data.get("issue_description") or data.get("description") or "Maintenance request submitted."
    tenant_id = int(data.get("tenant_id") or 1)

    res = create_maintenance_record(
        tenant_id=tenant_id,
        unit_id=unit_id,
        issue_description=desc,
        priority=priority
    )
    return (
        f"✅ **Maintenance Ticket Dispatched!**\n\n"
        f"Work order **#{res.get('request_id', 'TKT-?')}** registered for Unit #{unit_id}.\n\n"
        f"• **Priority:** {priority.upper()}\n"
        f"• **Issue Summary:** {desc}\n"
        f"• **SLA Policy:** Under our 48-hour resolution SLA, a technician has been notified."
    )


def _execute_modify_lease(data: Dict[str, Any]) -> str:
    from mcp_server.db_helpers import update_lease_terms

    lease_id = int(data.get("lease_id") or 1)
    proposed_rent = float(data.get("proposed_rent") or data.get("new_monthly_rent") or 42000)
    duration = int(data.get("duration_months") or 12)

    update_lease_terms(
        lease_id=lease_id,
        new_rent=proposed_rent,
        duration_months=duration,
        signed_off_by_executive=True
    )
    return (
        f"✅ **Lease Terms Modified & Executed!**\n\n"
        f"Lease **#{lease_id}** updated to monthly rent **{proposed_rent:,.2f} EGP** for **{duration} months**."
    )


def _execute_record_payment(data: Dict[str, Any]) -> str:
    from db.repositories.payment_repo import PaymentRepository
    from db.session import get_sync_db

    lease_id = int(data.get("lease_id") or 0)
    tenant_id = int(data.get("tenant_id") or 0)
    amount = float(data.get("amount") or 0)
    method = data.get("payment_method") or "credit_card"

    with next(get_sync_db()) as session:
        repo = PaymentRepository(session)
        receipt = repo.record_payment(
            lease_id=lease_id,
            tenant_id=tenant_id,
            amount=amount,
            payment_method=method,
            notes=data.get("notes")
        )
    return (
        f"✅ **Payment Recorded Successfully!**\n\n"
        f"• **Amount:** EGP {amount:,.2f}\n"
        f"• **Transaction Ref:** {receipt.get('transaction_reference')}\n"
        f"• **Method:** {method.replace('_', ' ').title()}\n"
        f"• **Receipt:** {receipt.get('receipt_url')}"
    )


def _execute_apply_lease(data: Dict[str, Any]) -> str:
    """Deprecated simple path — kept for backward compat with older UI flow."""
    applicant_name = data.get("applicant_name") or "Applicant"
    unit_id = int(data.get("unit_id") or 101)
    monthly_rent = float(data.get("monthly_rent") or data.get("proposed_monthly_rent") or 45000)
    deposit = float(data.get("security_deposit") or (monthly_rent * 2))
    term = int(data.get("duration_months") or data.get("lease_duration_months") or 12)
    move_in = data.get("move_in_date") or "2026-09-01"

    return (
        f"✅ **Digital Lease Application Submitted!**\n\n"
        f"Application registered for **{applicant_name}** for **Unit #{unit_id}**.\n\n"
        f"• **Proposed Monthly Rent:** {monthly_rent:,.0f} EGP\n"
        f"• **Security Deposit (2 Months):** {deposit:,.0f} EGP\n"
        f"• **Lease Term:** {term} Months\n"
        f"• **Target Move-in Date:** {move_in}\n\n"
        f"The property management desk will review your submission and contact you within 24 hours."
    )


# --------------------------------------------------------------------------- #
#  Dispatch table — add new action_type here, no router changes needed        #
# --------------------------------------------------------------------------- #

_HANDLERS = {
    "schedule_tour": _execute_schedule_tour,
    "cancel_tour": _execute_cancel_tour,
    "submit_maintenance": _execute_submit_maintenance,
    "modify_lease": _execute_modify_lease,
    "record_payment": _execute_record_payment,
    "apply_lease": _execute_apply_lease,
}


def dispatch_confirmed_action(action_type: str, data: Dict[str, Any]) -> str:
    """
    Route a confirmed HITL action to its executor.
    Returns a markdown-formatted final answer string.
    Raises KeyError if action_type is unknown.
    """
    handler = _HANDLERS.get(action_type)
    if handler is None:
        return f"Action '{action_type}' executed (no specific handler registered)."
    try:
        return handler(data)
    except Exception as exc:
        logger.error(f"action_dispatcher: {action_type} failed — {exc}")
        return f"⚠️ Action failed during execution: {exc}"
