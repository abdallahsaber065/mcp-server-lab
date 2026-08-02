"""
agent/client.py
----------------
Cornerstone Realty Group  MCP Client Agent  (Phase 3 / Ahmed Wael)

Demonstrates the full MCP client lifecycle:
  1. Protocol handshake & capability negotiation
  2. Dynamic tool discovery  (tools/list)
  3. Static resource read    (realty://policies/lease_terms)
  4. submit_maintenance_request tool call
  5. modify_lease_terms with elicitation mid-call pause + resumption
  6. notifications/tools/list_changed push listener (role switch  tenant)
  7. run_property_audit with live progressToken reporting
  8. Execution transcript written to  agent/demo_transcript.txt
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path bootstrap  allows running from any working directory
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mcp_server.db_helpers import init_db
from mcp_server.notifications import (
    NotificationDispatcher,
    ToolListChangedNotification,
)
from mcp_server.progress import make_tracker
from mcp_server.server import CornerstoneMCPServer

# ---------------------------------------------------------------------------
# Transcript logger
# ---------------------------------------------------------------------------

TRANSCRIPT_PATH = os.path.join(os.path.dirname(__file__), "demo_transcript.txt")


class TranscriptLogger:
    """Collects structured log lines and flushes to disk at the end."""

    def __init__(self) -> None:
        self._lines: List[str] = []

    def _ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def section(self, title: str) -> None:
        separator = "=" * 70
        self._lines += ["", separator, f"  {title}", separator]
        print(f"\n{'='*70}\n  {title}\n{'='*70}")

    def log(self, label: str, data: Any, *, indent: int = 2) -> None:
        body = (
            json.dumps(data, indent=indent, default=str)
            if isinstance(data, (dict, list))
            else str(data)
        )
        line = f"[{self._ts()}] [{label}]\n{body}"
        self._lines.append(line)
        print(line)

    def flush(self) -> None:
        os.makedirs(os.path.dirname(TRANSCRIPT_PATH), exist_ok=True)
        with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as fh:
            header = (
                "Cornerstone Realty Group MCP  End-to-End Execution Transcript\n"
                f"Generated : {datetime.now(timezone.utc).isoformat()}\n"
                f"Author    : Ahmed Wael (ahmedeladawy16)\n"
                f"Phase     : 3  Client Agent & Notifications\n"
                + ("=" * 70)
            )
            fh.write(header + "\n")
            fh.write("\n".join(self._lines))
        print(f"\n[OK]  Transcript saved -> {TRANSCRIPT_PATH}")


# ---------------------------------------------------------------------------
# MCP Client Agent
# ---------------------------------------------------------------------------


class CornerstoneClientAgent:
    """
    Simulated MCP Client that drives the CornerstoneMCPServer through the
    full protocol lifecycle defined in the lab specification.
    """

    CLIENT_INFO = {
        "name": "cornerstone-client-agent",
        "version": "1.0.0",
        "author": "Ahmed Wael (ahmedeladawy16)",
    }

    def __init__(self) -> None:
        self.transcript = TranscriptLogger()
        self._server: Optional[CornerstoneMCPServer] = None
        self._server_caps: Dict[str, Any] = {}
        self._known_tools: List[str] = []
        self._notification_log: List[Dict[str, Any]] = []

        # Notification dispatcher wired to our handler
        self._dispatcher = NotificationDispatcher()
        self._dispatcher.subscribe(
            ToolListChangedNotification.METHOD,
            self._on_tools_list_changed,
        )

    # ------------------------------------------------------------------
    # Internal notification handler
    # ------------------------------------------------------------------

    def _on_tools_list_changed(self, notification: Dict[str, Any]) -> None:
        params = notification.get("params", {})
        self._notification_log.append(notification)
        self.transcript.log(
            "NOTIFICATION RECEIVED  notifications/tools/list_changed",
            {
                "previous_role": params.get("previousRole"),
                "new_role": params.get("newRole"),
                "new_tool_list": params.get("availableTools"),
                "timestamp": params.get("timestamp"),
            },
        )
        # Refresh local tool registry
        self._known_tools = params.get("availableTools", [])

    # ------------------------------------------------------------------
    # Step 1  Protocol handshake & capability negotiation
    # ------------------------------------------------------------------

    def _step_handshake(self) -> None:
        self.transcript.section("STEP 1  Protocol Handshake & Capability Negotiation")

        init_db()
        self._server = CornerstoneMCPServer()

        # Client sends its own info as part of `initialize`
        initialize_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {
                "protocolVersion": "2025-06-18",
                "clientInfo": self.CLIENT_INFO,
                "capabilities": {
                    "sampling": {},
                    "elicitation": {},
                    "progress": {},
                },
            },
        }
        self.transcript.log("CLIENT -> initialize request", initialize_request)

        self._server_caps = self._server.get_capabilities()
        self.transcript.log("SERVER -> initialize response", self._server_caps)

        # Verify required capabilities before proceeding
        caps = self._server_caps.get("capabilities", {})
        assert caps["tools"]["listChanged"] is True, "Server must support listChanged"
        assert caps["elicitation"]["supported"] is True, "Server must support elicitation"
        assert caps["progress"]["supported"] is True, "Server must support progress"

        self.transcript.log(
            "HANDSHAKE",
            "Capability negotiation passed  elicitation, listChanged, progress all supported.",
        )

    # ------------------------------------------------------------------
    # Step 2  Dynamic tool discovery
    # ------------------------------------------------------------------

    def _step_tool_discovery(self) -> None:
        self.transcript.section("STEP 2  Dynamic Tool Discovery (tools/list)")

        tools_list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2,
            "params": {},
        }
        self.transcript.log("CLIENT -> tools/list request", tools_list_request)

        tools = self._server.list_tools()
        self._known_tools = [t["name"] for t in tools]
        self.transcript.log(
            "SERVER -> tools/list response",
            {
                "tools": [
                    {"name": t["name"], "description": t["description"]}
                    for t in tools
                ]
            },
        )
        self.transcript.log(
            "DISCOVERY",
            f"Discovered {len(tools)} tools: {self._known_tools}",
        )

    # ------------------------------------------------------------------
    # Step 3  Static resource read
    # ------------------------------------------------------------------

    def _step_resource_read(self) -> None:
        self.transcript.section(
            "STEP 3  Static Resource Read (realty://policies/lease_terms)"
        )

        resource_request = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "id": 3,
            "params": {"uri": "realty://policies/lease_terms"},
        }
        self.transcript.log("CLIENT -> resources/read request", resource_request)

        resource_response = self._server.read_resource("realty://policies/lease_terms")
        self.transcript.log("SERVER -> resources/read response", resource_response)

        # Parse and surface key policy constraints
        policy_text = resource_response["contents"][0]["text"]
        policy = json.loads(policy_text)
        self.transcript.log(
            "POLICY",
            f"Max manager discount = {policy['max_manager_discount_percent']}% | "
            f"Exec approval above EGP {policy['executive_approval_required_above_rent']:,.0f}",
        )

    # ------------------------------------------------------------------
    # Step 4  submit_maintenance_request
    # ------------------------------------------------------------------

    def _step_maintenance_request(self) -> None:
        self.transcript.section("STEP 4  Tool Call: submit_maintenance_request")

        tool_call_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 4,
            "params": {
                "name": "submit_maintenance_request",
                "arguments": {
                    "tenant_id": 1,
                    "unit_id": 101,
                    "issue_description": "HVAC unit producing unusual noise, failing to cool unit below 28 degrees C.",
                    "priority": "urgent",
                },
            },
        }
        self.transcript.log("CLIENT -> tools/call request", tool_call_request)

        result = self._server.call_tool(
            "submit_maintenance_request",
            tool_call_request["params"]["arguments"],
        )
        self.transcript.log("SERVER -> tools/call response", result)
        assert result["status"] == "success", "Maintenance request should succeed"
        self.transcript.log(
            "MAINTENANCE",
            f"Ticket #{result['result']['request_id']} filed  priority=urgent",
        )

    # ------------------------------------------------------------------
    # Step 5  modify_lease_terms with elicitation
    # ------------------------------------------------------------------

    def _step_modify_lease_with_elicitation(self) -> None:
        self.transcript.section(
            "STEP 5  Tool Call: modify_lease_terms (Elicitation Mid-Call Pause)"
        )

        # First attempt  25% discount > 15% threshold  elicitation_required
        call_args = {
            "lease_id": 1,
            "new_monthly_rent": 9000.0,  # 25% discount on base EGP 12,000
            "duration_months": 12,
            "executive_approval_given": False,
        }
        first_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 5,
            "params": {"name": "modify_lease_terms", "arguments": call_args},
        }
        self.transcript.log(
            "CLIENT -> tools/call request (attempt 1  no approval)",
            first_request,
        )

        result_1 = self._server.call_tool("modify_lease_terms", call_args)
        self.transcript.log(
            "SERVER -> tools/call response (elicitation_required)", result_1
        )
        assert result_1["status"] == "elicitation_required", "Must pause for approval"

        # Simulate human approval via elicitation/create
        elicitation_payload = result_1["elicitation_payload"]
        elicitation_request = {
            "jsonrpc": "2.0",
            "method": "elicitation/create",
            "id": "elicit-1",
            "params": {
                "prompt": elicitation_payload["prompt"],
                "leaseId": elicitation_payload["lease_id"],
                "proposedRent": elicitation_payload["proposed_rent"],
            },
        }
        self.transcript.log(
            "CLIENT -> elicitation/create (human review request)", elicitation_request
        )

        # Simulated human approves
        human_decision = {
            "jsonrpc": "2.0",
            "id": "elicit-1",
            "result": {
                "action": "approved",
                "approver": "exec_manager@cornerstone.eg",
                "comment": "One-time discount authorised for long-standing tenant.",
            },
        }
        self.transcript.log("HUMAN -> elicitation response (approved)", human_decision)

        # Resume with executive_approval_given = True
        resume_args = {**call_args, "executive_approval_given": True}
        resume_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 6,
            "params": {"name": "modify_lease_terms", "arguments": resume_args},
        }
        self.transcript.log(
            "CLIENT -> tools/call request (attempt 2  with approval)", resume_request
        )

        result_2 = self._server.call_tool("modify_lease_terms", resume_args)
        self.transcript.log("SERVER -> tools/call response (success)", result_2)
        assert result_2["status"] == "success", "Lease update should succeed after approval"
        self.transcript.log(
            "ELICITATION",
            f"Lease #{result_2['result']['lease_id']} updated: "
            f"EGP {result_2['result']['previous_rent']:,.0f} -> "
            f"EGP {result_2['result']['updated_rent']:,.0f}",
        )

    # ------------------------------------------------------------------
    # Step 6  Role switch  notifications/tools/list_changed
    # ------------------------------------------------------------------

    def _step_role_switch_notification(self) -> None:
        self.transcript.section(
            "STEP 6  Role Switch -> notifications/tools/list_changed Push Notification"
        )

        # Server switches role from property_manager  tenant
        notification_payload = self._server.set_user_role_and_notify("tenant")
        self.transcript.log(
            "SERVER  role switch triggered", notification_payload
        )

        # Build MCP notification envelope & emit it
        notif = ToolListChangedNotification(
            previous_role=notification_payload["previous_role"],
            new_role=notification_payload["new_role"],
            available_tools=notification_payload["available_tools"],
        )
        mcp_notification = notif.to_dict()
        self.transcript.log(
            "SERVER -> notifications/tools/list_changed push", mcp_notification
        )

        # Client dispatcher delivers to registered handler
        handled = self._dispatcher.dispatch(mcp_notification)
        self.transcript.log(
            "NOTIFICATIONS",
            f"Notification delivered to {handled} handler(s). "
            f"Client tool registry refreshed: {self._known_tools}",
        )

        assert "modify_lease_terms" not in self._known_tools, (
            "Tenant role should NOT see modify_lease_terms"
        )
        assert "run_property_audit" not in self._known_tools, (
            "Tenant role should NOT see run_property_audit"
        )

    # ------------------------------------------------------------------
    # Step 7  run_property_audit with progressToken
    # ------------------------------------------------------------------

    def _step_property_audit_with_progress(self) -> None:
        self.transcript.section(
            "STEP 7  Tool Call: run_property_audit (progressToken Reporting)"
        )

        # Switch back to manager role to regain audit access
        self._server.set_user_role_and_notify("property_manager")

        progress_token = f"audit-{uuid.uuid4().hex[:8]}"
        progress_updates: List[Dict[str, Any]] = []

        tracker = make_tracker(
            token=progress_token,
            total_steps=5,
            on_update=lambda u: progress_updates.append(u.to_dict()),
        )

        audit_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 7,
            "params": {
                "name": "run_property_audit",
                "arguments": {
                    "property_id": 1,
                    "include_expired_leases": True,
                },
                "_meta": {"progressToken": progress_token},
            },
        }
        self.transcript.log(
            "CLIENT -> tools/call request (with progressToken)", audit_request
        )

        # Replay server's internal progress steps through our tracker
        audit_result = self._server.call_tool(
            "run_property_audit",
            {"property_id": 1, "include_expired_leases": True},
            progress_token=progress_token,
        )

        # Emit each progress step via our ProgressTracker
        for prog in audit_result.get("progress_logs", []):
            tracker.report(prog["step"], prog["message"])
            self.transcript.log(
                f"SERVER -> notifications/progress (step {prog['step']}/5)",
                progress_updates[-1],
            )

        self.transcript.log("SERVER -> tools/call final response", audit_result)
        assert audit_result["status"] == "success"
        assert tracker.is_complete, "All 5 progress steps must be reported"

        self.transcript.log(
            "PROGRESS",
            f"Audit complete  {audit_result['total_units']} units, "
            f"{audit_result['occupancy_rate']} occupancy. "
            f"Progress token: {progress_token}",
        )

    # ------------------------------------------------------------------
    # Public run entrypoint
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the full MCP client lifecycle and save the transcript."""
        self.transcript.section(
            "Cornerstone Realty Group  MCP Client Agent (Phase 3)"
        )
        self.transcript.log(
            "CLIENT_INFO",
            {**self.CLIENT_INFO, "started_at": datetime.now(timezone.utc).isoformat()},
        )

        try:
            self._step_handshake()
            self._step_tool_discovery()
            self._step_resource_read()
            self._step_maintenance_request()
            self._step_modify_lease_with_elicitation()
            self._step_role_switch_notification()
            self._step_property_audit_with_progress()

            self.transcript.section("ALL STEPS COMPLETE")
            self.transcript.log(
                "SUMMARY",
                {
                    "steps_executed": 7,
                    "notifications_received": len(self._notification_log),
                    "status": "SUCCESS",
                },
            )
        finally:
            self.transcript.flush()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = CornerstoneClientAgent()
    agent.run()

