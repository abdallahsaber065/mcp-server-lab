"""
HITL Registry (web/services/hitl/registry.py)

Single source of truth for all HITL interceptors.
Open/Closed: add a new handler class, register it — zero changes to llm_engine.py.
"""

from typing import Any, Dict, List, Optional

from web.services.hitl.base_handler import BaseHITLHandler


class HITLRegistry:
    """
    Maintains an ordered list of HITL handlers and routes tool calls through them.

    Usage:
        registry = HITLRegistry()
        registry.register(TourHandler())
        registry.register(MaintenanceHandler())

        payload = registry.check(tool_name, args)
        if payload:
            # emit SSE action_confirmation and halt
    """

    def __init__(self) -> None:
        self._handlers: List[BaseHITLHandler] = []

    def register(self, handler: BaseHITLHandler) -> None:
        """Register a HITL handler. Duplicate tool_name registrations are silently skipped."""
        if any(h.tool_name == handler.tool_name for h in self._handlers):
            return
        self._handlers.append(handler)

    def check(self, tool_name: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Return a confirmation payload if tool_name requires HITL, else None.
        First matching handler wins (handlers are checked in registration order).
        """
        for handler in self._handlers:
            if handler.should_intercept(tool_name):
                return handler.build_confirmation(args)
        return None

    @property
    def intercepted_tools(self) -> List[str]:
        return [h.tool_name for h in self._handlers]
