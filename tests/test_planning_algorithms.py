"""
Unit Test Suite for Planning Algorithms (PS, ToT, LATS) using TA Reference Models
"""

import pytest
from unittest.mock import MagicMock
from planning.plan_and_solve import plan_and_solve
from planning.tree_of_thoughts import tree_of_thoughts
from planning.lats import lats, LATSResult
from planning.environment import Environment


def test_plan_and_solve_ta_reference():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "PLAN:\n1. Check budget\nSOLUTION:\nProceed with repair"
    res = plan_and_solve("Nile Tower maintenance", mock_llm)
    assert "PLAN:" in res
    assert "SOLUTION:" in res


def test_tree_of_thoughts_ta_reference():
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.side_effect = [
        MagicMock(candidates=["Option A", "Option B"]),
        MagicMock(score=0.9, rationale="High speed"),
        MagicMock(score=0.6, rationale="Low speed"),
    ]
    frontier = tree_of_thoughts("Vendor ranking", mock_llm, depth=1, beam_width=2)
    assert len(frontier) <= 2
    assert frontier[0].score == 0.9
