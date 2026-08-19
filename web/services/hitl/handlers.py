"""
Concrete HITL Handlers (web/services/hitl/handlers.py)

One class per intercepted tool. Each class is self-contained — no cross-references.
Register them all in web/services/hitl/__init__.py.
"""

from typing import Any, Dict

from web.services.hitl.base_handler import BaseHITLHandler


class TourBookingHandler(BaseHITLHandler):
    """Intercepts book_property_tour before it creates a DB record."""

    @property
    def tool_name(self) -> str:
        return "book_property_tour"

    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        name = args.get("contact_name", "Guest")
        prop_id = args.get("property_id", "?")
        date = args.get("requested_date", "")
        slot = args.get("time_slot", "")
        tour_type = args.get("tour_type", "in_person").replace("_", " ").title()
        unit_info = f" Unit #{args['unit_id']}" if args.get("unit_id") else ""
        return {
            "action_type": "schedule_tour",
            "prompt": (
                f"Please confirm scheduling a {tour_type} viewing for **{name}**"
                f" at Property #{prop_id}{unit_info} on {date} at {slot}."
            ),
            "payload": args,
        }


class MaintenanceRequestHandler(BaseHITLHandler):
    """Intercepts submit_maintenance_request before it dispatches a work order."""

    @property
    def tool_name(self) -> str:
        return "submit_maintenance_request"

    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        unit_id = args.get("unit_id", "?")
        priority = str(args.get("priority", "medium")).upper()
        description = args.get("issue_description", "")[:80]
        return {
            "action_type": "submit_maintenance",
            "prompt": (
                f"Dispatch a **{priority}** priority maintenance work order for Unit #{unit_id}.\n"
                f"Issue: \"{description}{'…' if len(str(args.get('issue_description', ''))) > 80 else ''}\""
            ),
            "payload": args,
        }


class LeaseModificationHandler(BaseHITLHandler):
    """Intercepts modify_lease_terms to enforce executive sign-off gate."""

    @property
    def tool_name(self) -> str:
        return "modify_lease_terms"

    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        lease_id = args.get("lease_id", "?")
        proposed_rent = args.get("new_monthly_rent", 0)
        duration = args.get("duration_months", 12)
        return {
            "action_type": "modify_lease",
            "prompt": (
                f"Executive approval required: Modify Lease **#{lease_id}** to "
                f"EGP {proposed_rent:,.0f}/month for {duration} months.\n"
                f"Discounts >15% or high-value leases require explicit sign-off."
            ),
            "payload": {
                "lease_id": lease_id,
                "proposed_rent": proposed_rent,
                "duration_months": duration,
            },
        }


class RentPaymentHandler(BaseHITLHandler):
    """Intercepts record_rent_payment to confirm large transaction amounts."""

    @property
    def tool_name(self) -> str:
        return "record_rent_payment"

    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        amount = args.get("amount", 0)
        lease_id = args.get("lease_id", "?")
        method = args.get("payment_method", "credit_card").replace("_", " ").title()
        return {
            "action_type": "record_payment",
            "prompt": (
                f"Confirm recording a payment of **EGP {amount:,.2f}** via {method} "
                f"against Lease #{lease_id}."
            ),
            "payload": args,
        }


class TourCancellationHandler(BaseHITLHandler):
    """Intercepts cancel_tour_booking to confirm before irrevocable cancellation."""

    @property
    def tool_name(self) -> str:
        return "cancel_tour_booking"

    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        booking_id = args.get("booking_id", "?")
        reason = args.get("cancellation_reason", "User requested cancellation")
        return {
            "action_type": "cancel_tour",
            "prompt": (
                f"Confirm cancellation of Tour Booking **#{booking_id}**.\n"
                f"Reason: \"{reason}\""
            ),
            "payload": args,
        }
