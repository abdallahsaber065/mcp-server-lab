"""
Unit Tests for Planning Evaluation Suite
"""

import json
from pathlib import Path
import pytest
from planning_eval.run_eval import run_benchmark


def test_planning_eval_benchmark():
    run_benchmark()
    results_path = Path("planning_eval/results.json")
    assert results_path.exists()
    
    with open(results_path, "r") as f:
        data = json.load(f)
        
    assert "decomposition" in data
    assert "planning" in data
    assert "self_correction" in data
    assert "Self-Refine" in data["self_correction"]
    assert "Reflexion" in data["self_correction"]
