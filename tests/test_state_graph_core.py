"""
Unit Tests for Async-First State Graph Core Engine & Graph 1 (tests/test_state_graph_core.py)
"""

import pytest
import asyncio
from state_graph.models import GraphState, NodeResult
from state_graph.engine import StateGraph
from state_graph.graphs.lease_flow import build_lease_flow_graph
from db.session import init_async_db, init_sync_db, IS_SQLITE


def test_db_session_initialization():
    """Verify database initialization works synchronously and sets up models."""
    init_sync_db()
    assert IS_SQLITE is True


@pytest.mark.anyio
async def test_async_db_session_initialization():
    """Verify database initialization works asynchronously."""
    await init_async_db()
    assert IS_SQLITE is True


def test_state_graph_basic_sync_flow():
    """Test standard sequential execution."""
    graph = StateGraph("test_simple_flow")

    def step_1(state: GraphState) -> NodeResult:
        return NodeResult(next_node="step_2", status="CONTINUE", updated_variables={"val": 1})

    def step_2(state: GraphState) -> NodeResult:
        return NodeResult(status="FINISH", updated_variables={"val": state.variables["val"] + 1})

    graph.add_node("step_1", step_1)
    graph.add_node("step_2", step_2)
    graph.set_entry_point("step_1")

    initial = GraphState(run_id="test-run-1", graph_id="test_simple_flow", current_node="step_1")
    final = graph.run(initial)

    assert final.status == "COMPLETED"
    assert final.variables["val"] == 2
    assert len(final.history) == 2


@pytest.mark.anyio
async def test_state_graph_async_nodes_and_arun():
    """Test async coroutine node execution in StateGraph."""
    graph = StateGraph("test_async_flow")

    async def async_node_1(state: GraphState) -> NodeResult:
        await asyncio.sleep(0.01)
        return NodeResult(next_node="async_node_2", status="CONTINUE", updated_variables={"async_count": 10})

    async def async_node_2(state: GraphState) -> NodeResult:
        await asyncio.sleep(0.01)
        return NodeResult(status="FINISH", updated_variables={"async_count": state.variables["async_count"] * 2})

    graph.add_node("async_node_1", async_node_1)
    graph.add_node("async_node_2", async_node_2)
    graph.set_entry_point("async_node_1")

    initial = GraphState(run_id="test-async-1", graph_id="test_async_flow", current_node="async_node_1")
    final = await graph.arun(initial)

    assert final.status == "COMPLETED"
    assert final.variables["async_count"] == 20


def test_state_graph_cycles_and_backtracking():
    """Test state graph cycle looping back to a previous state before completing."""
    graph = StateGraph("test_cycle_flow")

    def review_node(state: GraphState) -> NodeResult:
        attempts = state.variables.get("attempts", 0) + 1
        state.variables["attempts"] = attempts
        if attempts < 3:
            # Cycle back to self or previous node
            return NodeResult(next_node="review_node", status="CONTINUE", updated_variables={"attempts": attempts}, log_message=f"Attempt {attempts} rejected, retrying.")
        return NodeResult(status="FINISH", updated_variables={"attempts": attempts}, log_message="Approved on attempt 3!")

    graph.add_node("review_node", review_node)
    graph.set_entry_point("review_node")

    initial = GraphState(run_id="test-cycle-1", graph_id="test_cycle_flow", current_node="review_node")
    final = graph.run(initial)

    assert final.status == "COMPLETED"
    assert final.variables["attempts"] == 3
    assert len(final.history) == 3


def test_graph_1_lease_flow_execution():
    """Verify Graph 1 (Commercial Lease Flow) with Task Decomposition & ReAct."""
    graph = build_lease_flow_graph()

    # Case A: Without bank webhook -> pauses in AWAITING_WEBHOOK
    state_a = GraphState(
        run_id="lease-test-1",
        graph_id="commercial_lease_flow",
        current_node="decompose_requirements",
        variables={"unit_id": 301, "proposed_rent": 48000.0, "base_rent": 60000.0}
    )
    result_a = graph.run(state_a)
    assert result_a.status == "AWAITING_WEBHOOK"
    assert result_a.current_node == "await_bank_escrow"
    assert "decomposed_plan" in result_a.variables

    # Case B: With bank webhook confirmed -> discount 20% (>15%) triggers HITL pause
    result_a.variables["bank_webhook_payload"] = {"escrow_confirmed": True, "transaction_id": "BM-10029"}
    result_b = graph.run(result_a)
    assert result_b.status == "PAUSED_HITL"
    assert result_b.pending_hitl is not None
    assert "Executive Approval Required" in result_b.pending_hitl["reason"]

    # Case C: Admin approves in UI -> resumes and executes lease
    result_b.variables["hitl_decision"] = "APPROVED"
    result_c = graph.run(result_b)
    assert result_c.status == "COMPLETED"
    assert result_c.variables["lease_status"] == "ACTIVE"
