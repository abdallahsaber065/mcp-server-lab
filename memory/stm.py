"""
Short-Term Memory (STM) & Scratchpad Subsystem.
Maintains an active conversation message buffer alongside a decoupled scratchpad
holding the agent's current plan, active sub-goal, and working state.
Pruning the message transcript NEVER destroys or alters the scratchpad.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    timestamp: Optional[str] = None


class ShortTermMemory:
    def __init__(self, max_turns: int = 20, max_tokens: Optional[int] = None):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []
        self.scratchpad: Dict[str, Any] = {
            "current_plan": None,
            "active_subgoal": None,
            "working_state": {},
            "intermediate_findings": [],
        }

    def add_message(self, role: str, content: str, **kwargs) -> Dict[str, Any]:
        """Append a new message to the rolling STM transcript."""
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        return msg

    def update_scratchpad(
        self,
        plan: Optional[str] = None,
        subgoal: Optional[str] = None,
        state_update: Optional[Dict[str, Any]] = None,
        finding: Optional[str] = None,
    ) -> None:
        """Update active execution state in the decoupled scratchpad."""
        if plan is not None:
            self.scratchpad["current_plan"] = plan
        if subgoal is not None:
            self.scratchpad["active_subgoal"] = subgoal
        if state_update:
            self.scratchpad["working_state"].update(state_update)
        if finding:
            self.scratchpad["intermediate_findings"].append(finding)

    def get_context(self) -> List[Dict[str, Any]]:
        """Return the current active message context."""
        return list(self.messages)

    def get_scratchpad(self) -> Dict[str, Any]:
        """Return current scratchpad working state."""
        return dict(self.scratchpad)

    def get_formatted_system_prompt(self, base_prompt: str) -> str:
        """Inject active scratchpad state into system prompt without polluting history."""
        plan_str = self.scratchpad.get("current_plan") or "No active plan"
        subgoal_str = self.scratchpad.get("active_subgoal") or "None"
        findings_str = "; ".join(self.scratchpad.get("intermediate_findings", [])) or "None"

        return (
            f"{base_prompt}\n\n"
            f"=== AGENT WORKING SCRATCHPAD ===\n"
            f"Active Plan: {plan_str}\n"
            f"Current Sub-Goal: {subgoal_str}\n"
            f"Key Findings: {findings_str}\n"
            f"================================="
        )

    def prune_to_turn_limit(self) -> List[Dict[str, Any]]:
        """
        Prune older messages exceeding max_turns.
        Returns evicted items for promote-or-drop routing.
        CRITICAL: Scratchpad is completely unaffected by this pruning.
        """
        evicted = []
        if len(self.messages) > self.max_turns:
            evicted = self.messages[:-self.max_turns]
            self.messages = self.messages[-self.max_turns:]
        return evicted
