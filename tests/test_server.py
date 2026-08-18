import os
import sys
import tempfile
import pytest
import json

from mcp_server.db_helpers import init_db
from mcp_server.server import CornerstoneMCPServer

@pytest.fixture(scope="module")
def server():
    init_db(reset=False)
    yield CornerstoneMCPServer()

def test_capability_negotiation(server):
    caps = server.get_capabilities()
    assert caps["protocolVersion"] == "2025-06-18"
    assert caps["capabilities"]["elicitation"]["supported"] is True
    assert caps["capabilities"]["tools"]["listChanged"] is True

def test_lookup_available_units_valid(server):
    res = server.call_tool("lookup_available_units", {"city": "Cairo"})
    assert res["status"] == "success"
    assert res["count"] > 0

def test_defensive_pydantic_schema_extra_forbidden(server):
    """Verify defensive boundary: Pydantic rejects unknown input properties (extra='forbid')."""
    res = server.call_tool("lookup_available_units", {"city": "Cairo", "unknown_field": "hacked"})
    assert res["status"] == "error"
    assert res["error_type"] == "ValidationError"

def test_elicitation_trigger_on_high_discount(server):
    """Verify risky write action (>15% discount) triggers human elicitation requirement."""
    res = server.call_tool("modify_lease_terms", {
        "lease_id": 1, # Base rent = 12000.0
        "new_monthly_rent": 9000.0, # 25% discount (> 15%)
        "duration_months": 12,
        "executive_approval_given": False
    })
    assert res["status"] == "elicitation_required"
    assert "APPROVAL REQUIRED" in res["elicitation_payload"]["prompt"]
