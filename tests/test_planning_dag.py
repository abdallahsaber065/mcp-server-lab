"""
Unit Tests for DAG Task Decomposition & Dynamic Execution (tests/test_planning_dag.py)
"""

from unittest.mock import MagicMock

import pytest

from agent.planning_agent import PlanningAgent
from planning.decomposition import decompose_goal
from planning.dynamic_decomposition import dynamic_decomposition
from planning.models import Plan, Task


def test_dag_acyclicity_and_topological_sort():
    tasks = [
        Task(id="t1", instruction="Assess Nile Tower emergency plumbing burst", depends_on=[]),
        Task(id="t2", instruction="Rank vendor emergency dispatch priority", depends_on=["t1"]),
        Task(id="t3", instruction="Draft tenant temporary relocation plan", depends_on=["t1"]),
        Task(id="t4", instruction="Verify Egyptian Law 4/1996 SLA compliance", depends_on=["t2", "t3"]),
    ]
    plan = Plan(goal="Nile Tower emergency plumbing repair", tasks=tasks)
    assert plan.topological_order() == ["t1", "t2", "t3", "t4"]
    assert plan.execution_batches() == [["t1"], ["t2", "t3"], ["t4"]]
    assert plan.terminal_tasks() == ["t4"]


def test_dag_cycle_rejection():
    tasks = [
        Task(id="t1", instruction="Step 1", depends_on=["t2"]),
        Task(id="t2", instruction="Step 2", depends_on=["t1"]),
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        Plan(goal="Cycle test plan", tasks=tasks)


def test_planning_agent_subtask_routing():
    mock_llm = MagicMock()
    agent = PlanningAgent(llm=mock_llm, mode="static")

    assert agent.route_subtask("Rank emergency plumbing vendors by speed") == "ToT"
    assert agent.route_subtask("Verify Egyptian Law 4/1996 SLA compliance") == "LATS"
    assert agent.route_subtask("Calculate maintenance budget line items") == "PS"


def test_dynamic_decomposition_divergence_simulation():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.side_effect = [
        MagicMock(done=False, next_task="Primary contractor dispatch"),
        MagicMock(done=False, next_task="Primary vendor busy. Re-route secondary contractor"),
        MagicMock(done=True, next_task=""),
    ]
    mock_llm.invoke.return_value.content = "Sub-task executed successfully."

    history = dynamic_decomposition("Nile Tower burst", mock_llm, max_steps=3)
    assert len(history) == 2
    assert "Re-route" in history[1][0]
