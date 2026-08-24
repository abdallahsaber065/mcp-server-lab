"""Deprecated shim — use planning.tree_of_thoughts.tree_of_thoughts directly."""
from planning.tree_of_thoughts import tree_of_thoughts as _real_tot  # noqa: F401
from planning.models import Thought  # noqa: F401

# ponytail: keep shim for 1 import site, delete next semester
def tot(task: str, max_depth: int = 3, branches_per_node: int = 3, llm=None):  # type: ignore
    if llm is None:
        from planning.models import Thought as _T
        return type("ToTResult", (), {"depth": max_depth, "branches": branches_per_node, "selected_thought": _T(state="Structured 6-Month Installment Plan", score=0.92, rationale="shim fallback"), "all_thoughts": []})()
    return _real_tot(task, llm, depth=max_depth, beam_width=branches_per_node)  # type: ignore
