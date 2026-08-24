"""
State Graph Core Models (state_graph/models.py)
Typed Pydantic models for execution state, transitions, checkpoint snapshots, and node results.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GraphState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Execution state container for a state graph run."""
    run_id: str
    graph_id: str
    current_node: str
    status: Literal["RUNNING", "PAUSED_HITL", "AWAITING_WEBHOOK", "FAILED_TICKET", "COMPLETED", "CANCELLED"] = "RUNNING"
    step_number: int = 0
    variables: Dict[str, Any] = Field(default_factory=dict)
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    pending_hitl: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NodeResult(BaseModel):
    """Result returned by a single state graph node execution."""
    model_config = ConfigDict(extra="forbid")
    next_node: Optional[str] = None
    status: Literal["CONTINUE", "PAUSE_HITL", "WAIT_WEBHOOK", "FAIL", "FINISH"] = "CONTINUE"
    updated_variables: Dict[str, Any] = Field(default_factory=dict)
    log_message: str = ""
    hitl_payload: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
