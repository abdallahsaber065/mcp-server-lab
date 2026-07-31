"""
mcp_server/progress.py
-----------------------
Handler for MCP `progressToken` updates during batch / long-running operations.

The MCP spec allows a client to pass a `progressToken` when invoking a tool.
The server then periodically emits `notifications/progress` messages so the
client can render a live progress bar without polling.

MCP Spec Reference: https://modelcontextprotocol.io/docs/concepts/progress
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProgressUpdate:
    """
    A single progress snapshot emitted by a long-running tool call.

    Attributes
    ----------
    token : str
        Opaque progress token provided by the client at call time.
    step : int
        Current step number (1-based).
    total_steps : int
        Total number of steps in the operation.
    percentage : float
        0–100 completion percentage.
    message : str
        Human-readable status message for this step.
    timestamp : str
        ISO-8601 UTC timestamp of this update.
    """

    token: str
    step: int
    total_steps: int
    percentage: float
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise into the MCP `notifications/progress` JSON-RPC shape."""
        return {
            "jsonrpc": "2.0",
            "method": "notifications/progress",
            "params": {
                "progressToken": self.token,
                "step": self.step,
                "totalSteps": self.total_steps,
                "percentage": self.percentage,
                "message": self.message,
                "timestamp": self.timestamp,
            },
        }


# ---------------------------------------------------------------------------
# Progress tracker
# ---------------------------------------------------------------------------


class ProgressTracker:
    """
    Manages progress reporting for a single long-running tool invocation.

    Parameters
    ----------
    token : str
        Progress token supplied by the MCP client.
    total_steps : int
        Expected number of reporting steps.
    on_update : callable, optional
        Callback invoked synchronously after each :meth:`report` call.
        Receives the :class:`ProgressUpdate` instance.

    Examples
    --------
    >>> tracker = ProgressTracker("tok-abc", total_steps=5)
    >>> tracker.report(1, "Validating schema …")
    >>> tracker.report(2, "Querying database …")
    >>> tracker.is_complete
    False
    >>> tracker.report(5, "Done.")
    >>> tracker.is_complete
    True
    """

    def __init__(
        self,
        token: str,
        total_steps: int,
        on_update: Optional[Callable[[ProgressUpdate], None]] = None,
    ) -> None:
        if total_steps < 1:
            raise ValueError("total_steps must be >= 1")
        self.token = token
        self.total_steps = total_steps
        self._on_update = on_update
        self._updates: List[ProgressUpdate] = []

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def report(self, step: int, message: str) -> ProgressUpdate:
        """
        Emit a progress update for *step*.

        Parameters
        ----------
        step : int
            The step number being reported (1 ≤ step ≤ total_steps).
        message : str
            Descriptive status message.

        Returns
        -------
        ProgressUpdate
            The update object that was created and dispatched.
        """
        if step < 1 or step > self.total_steps:
            raise ValueError(
                f"step {step} is out of range [1, {self.total_steps}]"
            )
        pct = round((step / self.total_steps) * 100.0, 1)
        update = ProgressUpdate(
            token=self.token,
            step=step,
            total_steps=self.total_steps,
            percentage=pct,
            message=message,
        )
        self._updates.append(update)
        if self._on_update is not None:
            self._on_update(update)
        return update

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def updates(self) -> List[ProgressUpdate]:
        """All progress updates emitted so far (oldest first)."""
        return list(self._updates)

    @property
    def latest(self) -> Optional[ProgressUpdate]:
        """The most recent update, or *None* if none emitted yet."""
        return self._updates[-1] if self._updates else None

    @property
    def is_complete(self) -> bool:
        """Return True if the last reported step equals *total_steps*."""
        return bool(self._updates) and self._updates[-1].step == self.total_steps

    @property
    def percentage(self) -> float:
        """Current completion percentage (0.0 if no updates yet)."""
        return self._updates[-1].percentage if self._updates else 0.0

    def to_log(self) -> List[Dict[str, Any]]:
        """Return all updates serialised as dicts (for transcript logging)."""
        return [u.to_dict() for u in self._updates]


# ---------------------------------------------------------------------------
# Factory helper used by the client agent
# ---------------------------------------------------------------------------


def make_tracker(
    token: str,
    total_steps: int,
    on_update: Optional[Callable[[ProgressUpdate], None]] = None,
) -> ProgressTracker:
    """Convenience factory for :class:`ProgressTracker`."""
    return ProgressTracker(token=token, total_steps=total_steps, on_update=on_update)
