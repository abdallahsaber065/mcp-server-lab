"""
HITL Base Handler (web/services/hitl/base_handler.py)

Abstract base for all Human-in-the-Loop confirmation interceptors.
Each handler owns a single tool's confirmation logic — no cross-cutting hardcoded ifs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseHITLHandler(ABC):
    """
    Contract for a single HITL interceptor.

    Lifecycle:
      1. Registry calls should_intercept(tool_name) — O(1) exact match.
      2. If True, calls build_confirmation(args) to produce the SSE payload.
      3. After user confirms via /api/chat/confirm, registry routes args back
         to execute_confirmed(args) for the actual tool dispatch.
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the MCP tool this handler intercepts."""
        ...

    @abstractmethod
    def build_confirmation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce the confirmation payload sent as an SSE action_confirmation event.

        Returns a dict with at minimum:
          - action_type: str    (client-side discriminator for UI rendering)
          - prompt: str         (human-readable request to the operator)
          - payload: dict       (raw tool args, echoed back for display)
        """
        ...

    def should_intercept(self, tool_name: str) -> bool:
        return tool_name == self.tool_name
