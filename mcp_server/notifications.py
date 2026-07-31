"""
mcp_server/notifications.py
----------------------------
Handler for MCP `notifications/tools/list_changed` push events.

When the authenticated user's role changes (e.g. from `property_manager`
to `tenant`), the server emits this notification so the client can
refresh its local tool registry without reconnecting.

MCP Spec Reference: https://modelcontextprotocol.io/docs/concepts/notifications
"""

import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


class ToolListChangedNotification:
    """
    Represents a single `notifications/tools/list_changed` event payload.

    Attributes
    ----------
    previous_role : str
        The user role before the change.
    new_role : str
        The user role after the change.
    available_tools : list[str]
        Tool names visible to *new_role*.
    timestamp : str
        ISO-8601 UTC timestamp the notification was emitted.
    """

    METHOD = "notifications/tools/list_changed"

    def __init__(
        self,
        previous_role: str,
        new_role: str,
        available_tools: List[str],
    ) -> None:
        self.previous_role = previous_role
        self.new_role = new_role
        self.available_tools = available_tools
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the notification into the MCP JSON-RPC notification shape."""
        return {
            "jsonrpc": "2.0",
            "method": self.METHOD,
            "params": {
                "previousRole": self.previous_role,
                "newRole": self.new_role,
                "availableTools": self.available_tools,
                "timestamp": self.timestamp,
            },
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ToolListChangedNotification "
            f"prev={self.previous_role!r} new={self.new_role!r} "
            f"tools={self.available_tools}>"
        )


class NotificationDispatcher:
    """
    Lightweight pub/sub dispatcher for server-push MCP notifications.

    Usage
    -----
    >>> dispatcher = NotificationDispatcher()
    >>> dispatcher.subscribe("notifications/tools/list_changed", my_handler)
    >>> dispatcher.dispatch(notification.to_dict())
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe(
        self, method: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register *handler* to be called when *method* notifications arrive."""
        self._handlers.setdefault(method, []).append(handler)

    def unsubscribe(
        self, method: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Remove a previously registered handler (no-op if not found)."""
        if method in self._handlers:
            try:
                self._handlers[method].remove(handler)
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(self, notification: Dict[str, Any]) -> int:
        """
        Deliver *notification* to all subscribed handlers.

        Returns the number of handlers invoked.
        """
        method = notification.get("method", "")
        self._history.append(notification)
        handlers = self._handlers.get(method, [])
        for handler in handlers:
            handler(notification)
        return len(handlers)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Read-only list of every dispatched notification (oldest first)."""
        return list(self._history)

    def clear_history(self) -> None:
        """Flush the notification history log."""
        self._history.clear()

    def handler_count(self, method: str) -> int:
        """Return the number of handlers registered for *method*."""
        return len(self._handlers.get(method, []))


# ---------------------------------------------------------------------------
# Module-level singleton (convenient for agent & test imports)
# ---------------------------------------------------------------------------
dispatcher = NotificationDispatcher()
