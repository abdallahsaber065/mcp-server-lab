"""
Unit Tests for Grounded EnvironmentFeedback & Self-Correction (TA Reference Compatible)
"""

import pytest

from planning.environment import Environment
from planning.models import EnvironmentFeedback


def test_grounded_vs_ungrounded_contrast():
    plan_with_violation = "Emergency plumbing repair scheduled for 24 hours at Nile Tower."

    ungrounded_env = Environment(mode="ungrounded")
    u_fb = ungrounded_env.evaluate(plan_with_violation)
    assert u_fb.success is True  # Missed Law 4/1996 violation!

    grounded_env = Environment(mode="grounded")
    g_fb = grounded_env.evaluate(plan_with_violation)
    assert g_fb.success is False  # Caught Law 4/1996 violation!
    assert any("LAW 4/1996 VIOLATION" in d for d in g_fb.details)
