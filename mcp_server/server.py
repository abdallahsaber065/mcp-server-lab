import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

# Add root path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.models import Lease, MaintenanceRequest, Property, Tenant, Unit
from db.repositories.application_repo import ApplicationRepository
from db.repositories.maintenance_repo import MaintenanceRepository
from db.repositories.payment_repo import PaymentRepository
from db.repositories.tenant_repo import TenantRepository
from db.repositories.tour_repo import TourRepository
from db.session import get_sync_db, init_sync_db
from mcp_server.db_helpers import (
    create_maintenance_record,
    init_db,
    query_available_units,
    query_tenant_lease,
    update_lease_terms,
)
from mcp_server.notifications import ToolListChangedNotification, dispatcher
from mcp_server.schemas import (
    BatchAuditArgs,
    BookTourArgs,
    CancelTourArgs,
    GetMyMaintenanceRequestsArgs,
    ListPaymentsArgs,
    ListToursArgs,
    LookupLeaseArgs,
    MaintenanceRequestArgs,
    ModifyLeaseArgs,
    PayRentArgs,
    QueryUnitsArgs,
    RenewLeaseArgs,
    RescheduleTourArgs,
    SubmitLeaseApplicationArgs,
    UpdateTourStatusArgs,
)
from services.lease_service import LeaseService
from services.maintenance_service import MaintenanceService
from services.property_service import PropertyService
from services.tool_registry_service import ToolRegistryService


class CornerstoneMCPServer:
    """Cornerstone Realty Group MCP Server implementing protocol concerns."""

    def __init__(self):
        self.name = "cornerstone-realty-mcp"
        self.version = "1.0.0"
        self.protocol_version = "2025-06-18"
        init_db()
        init_sync_db()
        self.current_user_role = "property_manager"

    def get_agent_tool_bindings(self, agent_id: str) -> Dict[str, bool]:
        """Return enabled status for tools assigned to a specific agent via ToolRegistryService."""
        with next(get_sync_db()) as session:
            return ToolRegistryService.get_agent_tools(session, agent_id)

    def toggle_agent_tool(self, agent_id: str, tool_name: str, is_enabled: bool) -> bool:
        """Dynamically enable or disable a tool for an agent at runtime via ToolRegistryService."""
        active_tools = [t["name"] for t in self.list_tools(agent_id=agent_id)]
        with next(get_sync_db()) as session:
            return ToolRegistryService.toggle_tool(
                session=session,
                agent_id=agent_id,
                tool_name=tool_name,
                is_enabled=is_enabled,
                current_role=self.current_user_role,
                active_tools=active_tools
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """Declare capability negotiation capabilities."""
        return {
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": True},
                "elicitation": {"supported": True},
                "sampling": {"supported": True},
                "progress": {"supported": True}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "protocolVersion": self.protocol_version
        }

    def list_tools(self, role: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return available tools filtered by authenticated user role and runtime agent bindings."""
        active_role = role or self.current_user_role

        all_tools = [
            {
                "name": "lookup_available_units",
                "description": "Query available residential/commercial property units by property ID or city location.",
                "inputSchema": QueryUnitsArgs.model_json_schema()
            },
            {
                "name": "get_tenant_lease",
                "description": "Retrieve active or historical lease agreement details for a registered tenant by email (supports multi-lease queries).",
                "inputSchema": LookupLeaseArgs.model_json_schema()
            },
            {
                "name": "submit_maintenance_request",
                "description": "File a maintenance or repair ticket for a property unit.",
                "inputSchema": MaintenanceRequestArgs.model_json_schema()
            },
            {
                "name": "get_my_maintenance_requests",
                "description": "Retrieve all maintenance tickets filed by a tenant with optional status filtering.",
                "inputSchema": GetMyMaintenanceRequestsArgs.model_json_schema()
            },
            {
                "name": "book_property_tour",
                "description": "Schedule an in-person, 3D Matterport guided, or self-guided viewing appointment for a property or unit.",
                "inputSchema": BookTourArgs.model_json_schema()
            },
            {
                "name": "list_tour_bookings",
                "description": "List scheduled property viewing appointments with status, property, or email filters.",
                "inputSchema": ListToursArgs.model_json_schema()
            },
            {
                "name": "cancel_tour_booking",
                "description": "Cancel a scheduled property viewing tour with a specified cancellation reason.",
                "inputSchema": CancelTourArgs.model_json_schema()
            },
            {
                "name": "reschedule_tour_booking",
                "description": "Reschedule a property tour appointment to a new date and time slot.",
                "inputSchema": RescheduleTourArgs.model_json_schema()
            },
            {
                "name": "submit_lease_application",
                "description": "Submit a digital rental lease application for an available unit.",
                "inputSchema": SubmitLeaseApplicationArgs.model_json_schema()
            },
            {
                "name": "list_tenant_payments",
                "description": "Query payment history, invoices, receipts, and outstanding rent ledger for a tenant or lease.",
                "inputSchema": ListPaymentsArgs.model_json_schema()
            },
            {
                "name": "record_rent_payment",
                "description": "Execute or record a rent installment payment for a lease agreement.",
                "inputSchema": PayRentArgs.model_json_schema()
            },
            {
                "name": "request_lease_renewal",
                "description": "Submit a formal request to renew an existing active lease agreement.",
                "inputSchema": RenewLeaseArgs.model_json_schema()
            },
        ]

        # Role-gated write tools (Demonstrates Notifications & defensive auth)
        if active_role in ("property_manager", "executive_admin"):
            all_tools.append({
                "name": "update_tour_status",
                "description": "Approve, reschedule, complete, or cancel a prospect tour booking.",
                "inputSchema": UpdateTourStatusArgs.model_json_schema()
            })
            all_tools.append({
                "name": "modify_lease_terms",
                "description": "Update lease terms or monthly rent. Triggers human elicitation if discount > 15% or high value.",
                "inputSchema": ModifyLeaseArgs.model_json_schema()
            })
            all_tools.append({
                "name": "run_property_audit",
                "description": "Run a comprehensive compliance audit report for a property. Reports live progress updates.",
                "inputSchema": BatchAuditArgs.model_json_schema()
            })

        # Apply runtime agent dynamic bindings if agent_id is provided
        if agent_id:
            bindings = self.get_agent_tool_bindings(agent_id)
            filtered_tools = []
            for t in all_tools:
                if bindings.get(t["name"], True):
                    filtered_tools.append(t)
            return filtered_tools

        return all_tools

    def list_resources(self) -> List[Dict[str, Any]]:
        """Return exposed static resources."""
        return [
            {
                "uri": "realty://policies/lease_terms",
                "name": "Cornerstone Master Leasing Policy Document",
                "mimeType": "application/json",
                "description": "Static regulatory rules, max allowed discount percentages, and executive sign-off policies."
            }
        ]

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specified resource URI."""
        if uri == "realty://policies/lease_terms":
            policy_doc = {
                "organization": "Cornerstone Realty Group",
                "max_manager_discount_percent": 15.0,
                "executive_approval_required_above_rent": 40000.0,
                "urgent_maintenance_response_hours": 2,
                "governing_law": "Egyptian Civil Code - Lease Regulations"
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(policy_doc, indent=2)
                    }
                ]
            }
        raise ValueError(f"Resource '{uri}' not found.")

    def list_prompts(self) -> List[Dict[str, Any]]:
        """Return parameterized prompt templates."""
        return [
            {
                "name": "draft_lease_notice",
                "description": "Generates a standardized renewal or discount notice for a tenant.",
                "arguments": [
                    {"name": "tenant_email", "description": "Tenant email", "required": True},
                    {"name": "proposed_rent", "description": "New monthly rent amount", "required": True}
                ]
            }
        ]

    def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get prompt template filled with arguments."""
        if name == "draft_lease_notice":
            email = arguments.get("tenant_email", "")
            rent = arguments.get("proposed_rent", "")
            return {
                "description": f"Draft lease notice for {email}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Please draft a formal Cornerstone Realty lease adjustment notice for tenant ({email}) offering the new monthly rent of EGP {rent}. State that terms adhere to Cornerstone Master Leasing Policy."
                        }
                    }
                ]
            }
        raise ValueError(f"Prompt '{name}' not found.")

    def call_tool(self, name: str, arguments: Dict[str, Any], client_capabilities: Optional[Dict[str, Any]] = None, progress_token: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool with server-side Pydantic validation, elicitation, and defensive boundaries."""
        try:
            if name == "lookup_available_units":
                validated = QueryUnitsArgs(**arguments)
                results = query_available_units(property_id=validated.property_id, city=validated.city)
                return {"status": "success", "result": results, "count": len(results)}

            elif name == "get_tenant_lease":
                validated = LookupLeaseArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TenantRepository(session)
                    leases = repo.get_all_leases(validated.email)
                    if validated.active_only:
                        leases = [l for l in leases if l.get("is_active")]
                    if not leases:
                        return {"status": "not_found", "message": f"No lease records found for {validated.email}"}
                    return {
                        "status": "success",
                        "leases": leases,
                        "count": len(leases),
                        "active_count": len([l for l in leases if l.get("is_active")]),
                        "primary_lease": leases[0]
                    }

            elif name == "submit_maintenance_request":
                validated = MaintenanceRequestArgs(**arguments)
                res = create_maintenance_record(
                    tenant_id=validated.tenant_id,
                    unit_id=validated.unit_id,
                    issue_description=validated.issue_description,
                    priority=validated.priority
                )
                return {"status": "success", "result": res}

            elif name == "get_my_maintenance_requests":
                validated = GetMyMaintenanceRequestsArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = MaintenanceRepository(session)
                    tickets = repo.get_by_tenant(validated.tenant_id)
                    if validated.status:
                        tickets = [t for t in tickets if t.get("status") == validated.status]
                    return {"status": "success", "requests": tickets, "count": len(tickets)}

            elif name == "book_property_tour":
                validated = BookTourArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TourRepository(session)
                    booking = repo.create_booking(
                        property_id=validated.property_id,
                        unit_id=validated.unit_id,
                        contact_name=validated.contact_name,
                        contact_email=validated.contact_email,
                        contact_phone=validated.contact_phone,
                        tour_type=validated.tour_type,
                        requested_date=validated.requested_date,
                        time_slot=validated.time_slot,
                        notes=validated.notes
                    )
                    return {
                        "status": "success",
                        "message": f"Tour booked successfully for {booking['contact_name']} at {booking['property_name']} on {booking['requested_date']} at {booking['time_slot']}.",
                        "booking": booking
                    }

            elif name == "list_tour_bookings":
                validated = ListToursArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TourRepository(session)
                    bookings = repo.list_bookings(
                        property_id=validated.property_id,
                        status=validated.status,
                        email=validated.contact_email
                    )
                    return {"status": "success", "bookings": bookings, "count": len(bookings)}

            elif name == "cancel_tour_booking":
                validated = CancelTourArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TourRepository(session)
                    cancelled = repo.cancel_booking(
                        booking_id=validated.booking_id,
                        cancellation_reason=validated.cancellation_reason or "User cancelled viewing"
                    )
                    if not cancelled:
                        return {"status": "not_found", "message": f"Tour booking #{validated.booking_id} not found."}
                    return {
                        "status": "success",
                        "message": f"Tour booking #{validated.booking_id} has been cancelled.",
                        "booking": cancelled
                    }

            elif name == "reschedule_tour_booking":
                validated = RescheduleTourArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TourRepository(session)
                    rescheduled = repo.reschedule_booking(
                        booking_id=validated.booking_id,
                        new_date=validated.new_date,
                        new_slot=validated.new_time_slot,
                        notes=validated.notes
                    )
                    if not rescheduled:
                        return {"status": "not_found", "message": f"Tour booking #{validated.booking_id} not found."}
                    return {
                        "status": "success",
                        "message": f"Tour booking #{validated.booking_id} rescheduled to {validated.new_date} at {validated.new_time_slot}.",
                        "booking": rescheduled
                    }

            elif name == "submit_lease_application":
                validated = SubmitLeaseApplicationArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = ApplicationRepository(session)
                    app = repo.create_application(
                        unit_id=validated.unit_id,
                        applicant_name=validated.applicant_name,
                        applicant_email=validated.applicant_email,
                        proposed_monthly_rent=validated.proposed_monthly_rent,
                        lease_duration_months=validated.lease_duration_months,
                        move_in_date=validated.move_in_date,
                        applicant_phone=validated.applicant_phone,
                        employment_details=validated.employment_details
                    )
                    return {
                        "status": "success",
                        "message": f"Digital lease application #{app['application_id']} submitted for {app['applicant_name']}.",
                        "application": app
                    }

            elif name == "list_tenant_payments":
                validated = ListPaymentsArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = PaymentRepository(session)
                    if validated.tenant_id:
                        payments = repo.get_by_tenant(validated.tenant_id)
                    elif validated.lease_id:
                        payments = repo.get_by_lease(validated.lease_id)
                    else:
                        payments = []
                    return {"status": "success", "payments": payments, "count": len(payments)}

            elif name == "record_rent_payment":
                validated = PayRentArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = PaymentRepository(session)
                    receipt = repo.record_payment(
                        lease_id=validated.lease_id,
                        tenant_id=validated.tenant_id,
                        amount=validated.amount,
                        payment_method=validated.payment_method,
                        notes=validated.notes
                    )
                    return {
                        "status": "success",
                        "message": f"Payment of EGP {validated.amount:,.2f} recorded successfully.",
                        "receipt": receipt
                    }

            elif name == "request_lease_renewal":
                validated = RenewLeaseArgs(**arguments)
                with next(get_sync_db()) as session:
                    lease = session.get(Lease, validated.lease_id)
                    if not lease:
                        return {"status": "not_found", "message": f"Lease #{validated.lease_id} not found."}
                    lease.renewal_status = "requested"
                    lease.notes = f"{lease.notes or ''} | Renewal requested for {validated.extension_months} months: {validated.notes or ''}".strip()
                    session.commit()
                    return {
                        "status": "success",
                        "message": f"Renewal request registered for Lease #{validated.lease_id} ({validated.extension_months} months extension).",
                        "lease_id": validated.lease_id,
                        "renewal_status": "requested"
                    }

            elif name == "update_tour_status":
                validated = UpdateTourStatusArgs(**arguments)
                with next(get_sync_db()) as session:
                    repo = TourRepository(session)
                    updated = repo.update_status(
                        booking_id=validated.booking_id,
                        status=validated.status,
                        manager_notes=validated.manager_notes
                    )
                    if not updated:
                        return {"status": "not_found", "message": f"Tour booking #{validated.booking_id} not found."}
                    return {"status": "success", "message": f"Tour booking #{validated.booking_id} updated to '{validated.status}'.", "booking": updated}

            elif name == "modify_lease_terms":
                validated = ModifyLeaseArgs(**arguments)
                res = update_lease_terms(
                    lease_id=validated.lease_id,
                    new_rent=validated.new_monthly_rent,
                    duration_months=validated.duration_months,
                    signed_off_by_executive=validated.executive_approval_given
                )

                if res.get("requires_elicitation"):
                    return {
                        "status": "elicitation_required",
                        "elicitation_payload": {
                            "prompt": f"APPROVAL REQUIRED: {res['reason']}. Do you authorize lease #{validated.lease_id} at EGP {validated.new_monthly_rent}?",
                            "lease_id": validated.lease_id,
                            "proposed_rent": validated.new_monthly_rent
                        }
                    }
                return {"status": "success", "result": res}

            elif name == "run_property_audit":
                validated = BatchAuditArgs(**arguments)
                with next(get_sync_db()) as session:
                    prop = session.get(Property, validated.property_id)
                    if not prop:
                        return {
                            "status": "error",
                            "error_type": "ToolExecutionException",
                            "message": f"Property ID {validated.property_id} not found in property database. Please verify the property identifier."
                        }

                    progress_history = []
                    for step in range(1, 6):
                        pct = step * 20
                        msg = f"Auditing {prop.name} (ID: {validated.property_id}) - Step {step}/5 ({pct}%)"
                        progress_history.append({"step": step, "percentage": pct, "message": msg})

                    units = session.query(Unit).filter(Unit.property_id == validated.property_id).all()
                    total_u = len(units)
                    occupied_u = len([u for u in units if u.status == "occupied"])

                    return {
                        "status": "success",
                        "property_id": validated.property_id,
                        "property_name": prop.name,
                        "total_units": total_u,
                        "occupied_units": occupied_u,
                        "occupancy_rate": f"{(occupied_u / total_u * 100):.1f}%" if total_u > 0 else "0%",
                        "progress_logs": progress_history
                    }

            else:
                return {"status": "error", "error_type": "UnknownTool", "message": f"Requested tool '{name}' is not recognized in current permissions."}

        except ValidationError as e:
            return {
                "status": "error",
                "error_type": "ValidationError",
                "message": "Invalid input parameters: Please check required fields and data types.",
                "details": e.errors()
            }
        except Exception as e:
            err_msg = str(e)
            if "FOREIGN KEY" in err_msg.upper():
                clean_msg = "Invalid reference: The specified Unit ID or Tenant ID does not exist in property records."
            elif "UNIQUE CONSTRAINT" in err_msg.upper():
                clean_msg = "Conflict: A record with these unique identifiers already exists."
            elif "NOT FOUND" in err_msg.upper():
                clean_msg = err_msg
            elif "CHECK CONSTRAINT" in err_msg.upper():
                clean_msg = "Validation constraint failed: Input value is out of permitted range."
            else:
                clean_msg = err_msg.replace("sqlite3.IntegrityError: ", "").replace("sqlite3.OperationalError: ", "").strip()
                if "sqlite" in clean_msg.lower() or "syntax" in clean_msg.lower():
                    clean_msg = "Unable to process database query due to an invalid request format."
            return {
                "status": "error",
                "error_type": "ToolExecutionException",
                "message": clean_msg
            }

    def set_user_role_and_notify(self, new_role: str) -> Dict[str, Any]:
        """Simulate role change and return list_changed notification payload."""
        old_role = self.current_user_role
        self.current_user_role = new_role
        return {
            "notification": "notifications/tools/list_changed",
            "previous_role": old_role,
            "new_role": new_role,
            "available_tools": [t["name"] for t in self.list_tools(new_role)]
        }


if __name__ == "__main__":
    server = CornerstoneMCPServer()
    print(f"Initialized {server.name} v{server.version}")
    caps = server.get_capabilities()
    print("Capabilities:", json.dumps(caps, indent=2))
    tools = server.list_tools()
    print(f"Available tools ({len(tools)}):", [t["name"] for t in tools])
