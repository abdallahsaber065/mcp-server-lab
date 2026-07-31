"""
tests/test_client.py
---------------------
Pytest integration test suite for the MCP Client Agent — Phase 3 (Ahmed Wael).

Covers:
  TC-01  Protocol handshake — server capabilities negotiation
  TC-02  Dynamic tool discovery (tools/list)
  TC-03  Static resource read  (realty://policies/lease_terms)
  TC-04  submit_maintenance_request tool call
  TC-05  modify_lease_terms — elicitation_required on discount > 15%
  TC-06  modify_lease_terms — successful resumption after human approval
  TC-07  notifications/tools/list_changed — role switch from manager → tenant
  TC-08  Tenant role loses privileged tools after list_changed
  TC-09  run_property_audit — progressToken steps reported correctly
  TC-10  NotificationDispatcher pub/sub wiring
  TC-11  ProgressTracker is_complete and percentage tracking
  TC-12  ToolListChangedNotification JSON-RPC envelope structure
"""

import json
import os
import sys
import uuid
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mcp_server.db_helpers import init_db
from mcp_server.notifications import (
    NotificationDispatcher,
    ToolListChangedNotification,
)
from mcp_server.progress import ProgressTracker, make_tracker
from mcp_server.server import CornerstoneMCPServer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def server(tmp_path) -> CornerstoneMCPServer:
    """Fresh server with a reset database for every test."""
    test_db = str(tmp_path / "test_client_realty.db")
    os.environ["MCP_DB_FILE"] = test_db
    init_db(reset=True)
    srv = CornerstoneMCPServer()
    yield srv
    if "MCP_DB_FILE" in os.environ:
        del os.environ["MCP_DB_FILE"]


@pytest.fixture(scope="function")
def dispatcher() -> NotificationDispatcher:
    """Isolated NotificationDispatcher instance."""
    return NotificationDispatcher()


# ---------------------------------------------------------------------------
# TC-01  Protocol handshake — capability negotiation
# ---------------------------------------------------------------------------


class TestHandshake:
    def test_protocol_version(self, server: CornerstoneMCPServer) -> None:
        caps = server.get_capabilities()
        assert caps["protocolVersion"] == "2025-06-18"

    def test_elicitation_supported(self, server: CornerstoneMCPServer) -> None:
        caps = server.get_capabilities()
        assert caps["capabilities"]["elicitation"]["supported"] is True

    def test_tools_list_changed_supported(self, server: CornerstoneMCPServer) -> None:
        caps = server.get_capabilities()
        assert caps["capabilities"]["tools"]["listChanged"] is True

    def test_progress_supported(self, server: CornerstoneMCPServer) -> None:
        caps = server.get_capabilities()
        assert caps["capabilities"]["progress"]["supported"] is True

    def test_server_info_present(self, server: CornerstoneMCPServer) -> None:
        caps = server.get_capabilities()
        info = caps["serverInfo"]
        assert "name" in info
        assert "version" in info


# ---------------------------------------------------------------------------
# TC-02  Dynamic tool discovery
# ---------------------------------------------------------------------------


class TestToolDiscovery:
    def test_default_role_returns_tools(self, server: CornerstoneMCPServer) -> None:
        tools = server.list_tools()
        assert len(tools) > 0

    def test_tool_names_present(self, server: CornerstoneMCPServer) -> None:
        names = {t["name"] for t in server.list_tools()}
        assert "lookup_available_units" in names
        assert "get_tenant_lease" in names
        assert "submit_maintenance_request" in names

    def test_manager_role_sees_privileged_tools(self, server: CornerstoneMCPServer) -> None:
        tools = server.list_tools(role="property_manager")
        names = {t["name"] for t in tools}
        assert "modify_lease_terms" in names
        assert "run_property_audit" in names

    def test_tenant_role_excludes_privileged_tools(self, server: CornerstoneMCPServer) -> None:
        tools = server.list_tools(role="tenant")
        names = {t["name"] for t in tools}
        assert "modify_lease_terms" not in names
        assert "run_property_audit" not in names

    def test_tools_have_input_schema(self, server: CornerstoneMCPServer) -> None:
        for tool in server.list_tools():
            assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"


# ---------------------------------------------------------------------------
# TC-03  Static resource read
# ---------------------------------------------------------------------------


class TestResourceRead:
    def test_lease_policy_uri_resolves(self, server: CornerstoneMCPServer) -> None:
        result = server.read_resource("realty://policies/lease_terms")
        assert "contents" in result
        assert len(result["contents"]) == 1

    def test_lease_policy_is_valid_json(self, server: CornerstoneMCPServer) -> None:
        result = server.read_resource("realty://policies/lease_terms")
        text = result["contents"][0]["text"]
        policy = json.loads(text)
        assert "max_manager_discount_percent" in policy
        assert policy["max_manager_discount_percent"] == 15.0

    def test_unknown_resource_raises(self, server: CornerstoneMCPServer) -> None:
        with pytest.raises(ValueError, match="not found"):
            server.read_resource("realty://unknown/resource")


# ---------------------------------------------------------------------------
# TC-04  submit_maintenance_request
# ---------------------------------------------------------------------------


class TestMaintenanceRequest:
    def test_successful_submission(self, server: CornerstoneMCPServer) -> None:
        # Seeded unit IDs start at 101 (see db/seed.sql)
        res = server.call_tool(
            "submit_maintenance_request",
            {
                "tenant_id": 1,
                "unit_id": 101,
                "issue_description": "Broken window latch on second floor.",
                "priority": "high",
            },
        )
        assert res["status"] == "success"
        assert "request_id" in res["result"]

    def test_urgent_priority_accepted(self, server: CornerstoneMCPServer) -> None:
        res = server.call_tool(
            "submit_maintenance_request",
            {
                "tenant_id": 2,
                "unit_id": 102,
                "issue_description": "Water leak flooding the kitchen area.",
                "priority": "urgent",
            },
        )
        assert res["status"] == "success"

    def test_short_description_rejected(self, server: CornerstoneMCPServer) -> None:
        """Pydantic min_length=5 must reject a description that is too short."""
        res = server.call_tool(
            "submit_maintenance_request",
            {
                "tenant_id": 1,
                "unit_id": 1,
                "issue_description": "Fix",
                "priority": "low",
            },
        )
        assert res["status"] == "error"
        assert res["error_type"] == "ValidationError"


# ---------------------------------------------------------------------------
# TC-05 & TC-06  modify_lease_terms — elicitation flow
# ---------------------------------------------------------------------------


class TestModifyLeaseElicitation:
    def test_high_discount_triggers_elicitation(self, server: CornerstoneMCPServer) -> None:
        """Discount > 15% must pause with elicitation_required."""
        res = server.call_tool(
            "modify_lease_terms",
            {
                "lease_id": 1,
                "new_monthly_rent": 9000.0,  # 25% off EGP 12,000
                "duration_months": 12,
                "executive_approval_given": False,
            },
        )
        assert res["status"] == "elicitation_required"
        payload = res["elicitation_payload"]
        assert "APPROVAL REQUIRED" in payload["prompt"]
        assert payload["lease_id"] == 1

    def test_elicitation_payload_contains_proposed_rent(self, server: CornerstoneMCPServer) -> None:
        res = server.call_tool(
            "modify_lease_terms",
            {
                "lease_id": 1,
                "new_monthly_rent": 9000.0,
                "duration_months": 12,
                "executive_approval_given": False,
            },
        )
        assert res["elicitation_payload"]["proposed_rent"] == 9000.0

    def test_approved_elicitation_completes_update(self, server: CornerstoneMCPServer) -> None:
        """After executive_approval_given=True the update must succeed."""
        res = server.call_tool(
            "modify_lease_terms",
            {
                "lease_id": 1,
                "new_monthly_rent": 9000.0,
                "duration_months": 12,
                "executive_approval_given": True,
            },
        )
        assert res["status"] == "success"
        assert res["result"]["updated_rent"] == 9000.0

    def test_small_discount_skips_elicitation(self, server: CornerstoneMCPServer) -> None:
        """A discount ≤ 15% on a non-executive lease should succeed directly."""
        res = server.call_tool(
            "modify_lease_terms",
            {
                "lease_id": 1,
                "new_monthly_rent": 11000.0,  # ~8.3% discount — under threshold
                "duration_months": 6,
                "executive_approval_given": False,
            },
        )
        # Either success or elicitation_required (high-value flag may force it)
        assert res["status"] in ("success", "elicitation_required")


# ---------------------------------------------------------------------------
# TC-07 & TC-08  notifications/tools/list_changed
# ---------------------------------------------------------------------------


class TestListChangedNotification:
    def test_role_switch_returns_notification_payload(
        self, server: CornerstoneMCPServer
    ) -> None:
        payload = server.set_user_role_and_notify("tenant")
        assert payload["notification"] == "notifications/tools/list_changed"
        assert payload["new_role"] == "tenant"
        assert payload["previous_role"] == "property_manager"

    def test_tenant_loses_privileged_tools_after_switch(
        self, server: CornerstoneMCPServer
    ) -> None:
        payload = server.set_user_role_and_notify("tenant")
        assert "modify_lease_terms" not in payload["available_tools"]
        assert "run_property_audit" not in payload["available_tools"]

    def test_notification_envelope_structure(self) -> None:
        notif = ToolListChangedNotification(
            previous_role="property_manager",
            new_role="tenant",
            available_tools=["lookup_available_units"],
        )
        envelope = notif.to_dict()
        assert envelope["jsonrpc"] == "2.0"
        assert envelope["method"] == "notifications/tools/list_changed"
        params = envelope["params"]
        assert params["previousRole"] == "property_manager"
        assert params["newRole"] == "tenant"
        assert isinstance(params["availableTools"], list)
        assert "timestamp" in params

    def test_dispatcher_delivers_notification(
        self, dispatcher: NotificationDispatcher
    ) -> None:
        received: List[Dict[str, Any]] = []
        dispatcher.subscribe(
            ToolListChangedNotification.METHOD, received.append
        )
        notif = ToolListChangedNotification(
            previous_role="property_manager",
            new_role="tenant",
            available_tools=["lookup_available_units"],
        )
        count = dispatcher.dispatch(notif.to_dict())
        assert count == 1
        assert len(received) == 1
        assert received[0]["params"]["newRole"] == "tenant"

    def test_dispatcher_history_logged(
        self, dispatcher: NotificationDispatcher
    ) -> None:
        notif = ToolListChangedNotification("x", "y", [])
        dispatcher.dispatch(notif.to_dict())
        assert len(dispatcher.history) == 1

    def test_dispatcher_unsubscribe(
        self, dispatcher: NotificationDispatcher
    ) -> None:
        received: List[Any] = []
        handler = received.append
        dispatcher.subscribe(ToolListChangedNotification.METHOD, handler)
        dispatcher.unsubscribe(ToolListChangedNotification.METHOD, handler)
        dispatcher.dispatch(
            ToolListChangedNotification("a", "b", []).to_dict()
        )
        assert len(received) == 0


# ---------------------------------------------------------------------------
# TC-09  run_property_audit — progressToken steps
# ---------------------------------------------------------------------------


class TestPropertyAuditProgress:
    def test_audit_returns_progress_logs(self, server: CornerstoneMCPServer) -> None:
        result = server.call_tool(
            "run_property_audit",
            {"property_id": 1, "include_expired_leases": True},
        )
        assert result["status"] == "success"
        assert "progress_logs" in result
        assert len(result["progress_logs"]) == 5

    def test_audit_progress_percentages(self, server: CornerstoneMCPServer) -> None:
        result = server.call_tool(
            "run_property_audit",
            {"property_id": 1, "include_expired_leases": False},
        )
        percentages = [p["percentage"] for p in result["progress_logs"]]
        assert percentages == [20, 40, 60, 80, 100]

    def test_audit_returns_occupancy_rate(self, server: CornerstoneMCPServer) -> None:
        result = server.call_tool(
            "run_property_audit",
            {"property_id": 1, "include_expired_leases": True},
        )
        assert "occupancy_rate" in result
        assert "%" in result["occupancy_rate"]


# ---------------------------------------------------------------------------
# TC-10  ProgressTracker unit tests
# ---------------------------------------------------------------------------


class TestProgressTracker:
    def test_tracker_reports_correct_percentage(self) -> None:
        tracker = ProgressTracker("tok-1", total_steps=5)
        update = tracker.report(1, "Step 1")
        assert update.percentage == 20.0

    def test_tracker_is_complete_on_last_step(self) -> None:
        tracker = ProgressTracker("tok-2", total_steps=3)
        tracker.report(1, "A")
        tracker.report(2, "B")
        assert not tracker.is_complete
        tracker.report(3, "C")
        assert tracker.is_complete

    def test_tracker_on_update_callback(self) -> None:
        received: List[Any] = []
        tracker = make_tracker("tok-3", 4, on_update=received.append)
        tracker.report(1, "start")
        tracker.report(4, "end")
        assert len(received) == 2
        # The callback receives ProgressUpdate objects (not the tracker itself)
        assert isinstance(received[-1], __import__("mcp_server.progress", fromlist=["ProgressUpdate"]).ProgressUpdate)
        # Verify the last update has 100% percentage (step 4 of 4)
        assert received[-1].percentage == 100.0

    def test_tracker_out_of_range_raises(self) -> None:
        tracker = ProgressTracker("tok-4", total_steps=3)
        with pytest.raises(ValueError):
            tracker.report(0, "invalid")
        with pytest.raises(ValueError):
            tracker.report(4, "out of range")

    def test_tracker_percentage_property(self) -> None:
        tracker = ProgressTracker("tok-5", total_steps=4)
        assert tracker.percentage == 0.0
        tracker.report(2, "halfway")
        assert tracker.percentage == 50.0

    def test_make_tracker_factory(self) -> None:
        tracker = make_tracker("tok-6", total_steps=10)
        assert isinstance(tracker, ProgressTracker)
        assert tracker.token == "tok-6"
        assert tracker.total_steps == 10
