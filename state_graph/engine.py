"""
State Graph Execution Engine (state_graph/engine.py)
Async-First state machine runner supporting cycles, asynchronous waits, HITL pauses, and durable checkpoints.
"""

import asyncio
import concurrent.futures
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Union

from state_graph.models import GraphState, NodeResult

logger = logging.getLogger("state_graph.engine")


class StateGraph:
    """Async-First state machine engine supporting cycles, pauses, and checkpoints."""

    def __init__(self, graph_id: str, checkpointer=None, max_cycles: int = 25):
        self.graph_id = graph_id
        self.checkpointer = checkpointer
        self.nodes: Dict[str, Callable[[GraphState], Union[NodeResult, Any]]] = {}
        self.entry_node: Optional[str] = None
        self.max_cycles: int = max_cycles

    def add_node(self, name: str, fn: Callable[[GraphState], Union[NodeResult, Any]]):
        """Register a node function (sync or async) in the state graph."""
        self.nodes[name] = fn
        if self.entry_node is None:
            self.entry_node = name

    def set_entry_point(self, name: str):
        """Set the initial starting node of the state graph."""
        self.entry_node = name

    async def _execute_node(self, node_fn: Callable, state: GraphState) -> NodeResult:
        """Execute a node function whether it is a synchronous function or an async coroutine."""
        if inspect.iscoroutinefunction(node_fn):
            return await node_fn(state)
        return node_fn(state)

    async def _save_checkpoint_async(self, state: GraphState):
        """Save checkpoint via async or sync checkpointer."""
        if not self.checkpointer:
            return
        if hasattr(self.checkpointer, "asave_checkpoint"):
            await self.checkpointer.asave_checkpoint(state)
        elif hasattr(self.checkpointer, "save_checkpoint"):
            self.checkpointer.save_checkpoint(state)

    async def arun(self, initial_state: GraphState) -> GraphState:
        """
        Asynchronously run the state graph until reaching a terminal state, an asynchronous wait, or an HITL pause.
        Writes durable checkpoints after every meaningful transition.
        """
        state = initial_state
        state.status = "RUNNING"

        if not state.current_node:
            state.current_node = self.entry_node

        await self._save_checkpoint_async(state)

        cycles = 0
        while state.status == "RUNNING" and state.current_node:
            cycles += 1
            if cycles > self.max_cycles:
                logger.warning("Max cycle budget (%d) reached for run %s", self.max_cycles, state.run_id)
                state.status = "FAILED_TICKET"
                state.last_error = {
                    "type": "MaxCyclesExceeded",
                    "message": f"Loop exceeded safety budget of {self.max_cycles} cycles"
                }
                await self._save_checkpoint_async(state)
                break

            node_fn = self.nodes.get(state.current_node)
            if not node_fn:
                raise ValueError(f"Node '{state.current_node}' not registered in graph '{self.graph_id}'.")

            state.step_number += 1
            logger.info("Executing node '%s' (Step %d, Run %s)", state.current_node, state.step_number, state.run_id)

            try:
                result = await self._execute_node(node_fn, state)
            except Exception as e:
                logger.exception("Uncaught exception in node '%s': %s", state.current_node, str(e))
                state.status = "FAILED_TICKET"
                state.last_error = {"type": type(e).__name__, "message": str(e)}
                await self._save_checkpoint_async(state)
                return state

            # Update state with node output
            state.variables.update(result.updated_variables)
            state.history.append({
                "step": state.step_number,
                "node": state.current_node,
                "status": result.status,
                "message": result.log_message
            })

            if result.status == "PAUSE_HITL":
                state.status = "PAUSED_HITL"
                state.pending_hitl = result.hitl_payload
                state.current_node = result.next_node or state.current_node
            elif result.status == "WAIT_WEBHOOK":
                state.status = "AWAITING_WEBHOOK"
                state.current_node = result.next_node or state.current_node
            elif result.status == "FAIL":
                state.status = "FAILED_TICKET"
                state.last_error = result.error_details or {"message": result.log_message}
            elif result.status == "FINISH":
                state.status = "COMPLETED"
                state.current_node = ""
            else:
                state.current_node = result.next_node

            await self._save_checkpoint_async(state)

        return state

    async def astream(self, initial_state: GraphState):
        """Async generator yielding per-node progress for SSE live visualization."""
        state = initial_state
        state.status = "RUNNING"
        if not state.current_node:
            state.current_node = self.entry_node
        await self._save_checkpoint_async(state)
        yield {"type": "checkpoint", "step": state.step_number, "node": state.current_node, "status": state.status, "variables": dict(state.variables), "history": list(state.history)}
        cycles = 0
        while state.status == "RUNNING" and state.current_node:
            cycles += 1
            if cycles > self.max_cycles:
                state.status = "FAILED_TICKET"
                state.last_error = {"type": "MaxCyclesExceeded", "message": f"Loop exceeded safety budget of {self.max_cycles} cycles"}
                await self._save_checkpoint_async(state)
                yield {"type": "failed", "status": state.status, "error": state.last_error, "variables": dict(state.variables), "history": list(state.history)}
                break
            node_fn = self.nodes.get(state.current_node)
            if not node_fn:
                raise ValueError(f"Node '{state.current_node}' not registered in graph '{self.graph_id}'.")
            prev_node = state.current_node
            state.step_number += 1
            yield {"type": "node_start", "node": prev_node, "step": state.step_number, "variables": dict(state.variables)}
            try:
                result = await self._execute_node(node_fn, state)
            except Exception as e:
                state.status = "FAILED_TICKET"
                state.last_error = {"type": type(e).__name__, "message": str(e)}
                await self._save_checkpoint_async(state)
                yield {"type": "failed", "status": state.status, "error": state.last_error, "node": prev_node, "variables": dict(state.variables), "history": list(state.history)}
                return
            state.variables.update(result.updated_variables)
            state.history.append({"step": state.step_number, "node": prev_node, "status": result.status, "message": result.log_message})
            if result.status == "PAUSE_HITL":
                state.status = "PAUSED_HITL"
                state.pending_hitl = result.hitl_payload
                state.current_node = result.next_node or state.current_node
            elif result.status == "WAIT_WEBHOOK":
                state.status = "AWAITING_WEBHOOK"
                state.current_node = result.next_node or state.current_node
            elif result.status == "FAIL":
                state.status = "FAILED_TICKET"
                state.last_error = result.error_details or {"message": result.log_message}
            elif result.status == "FINISH":
                state.status = "COMPLETED"
                state.current_node = ""
            else:
                state.current_node = result.next_node
            await self._save_checkpoint_async(state)
            yield {"type": "node_complete", "node": prev_node, "step": state.step_number, "status": result.status, "message": result.log_message, "next_node": state.current_node, "pending_hitl": state.pending_hitl, "variables": dict(state.variables), "history": list(state.history), "graph_status": state.status}
            if state.status in ("PAUSED_HITL", "AWAITING_WEBHOOK", "FAILED_TICKET", "COMPLETED"):
                yield {"type": "final", "run_id": state.run_id, "graph_status": state.status, "current_node": state.current_node, "step_number": state.step_number, "pending_hitl": state.pending_hitl, "last_error": state.last_error, "variables": dict(state.variables), "history": list(state.history)}
                return

    def run(self, initial_state: GraphState) -> GraphState:
        """Synchronous wrapper for arun(). Handles existing running event loops safely."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In an already running loop (e.g. Jupyter or nested async), use ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, self.arun(initial_state))
                    return future.result()
            return loop.run_until_complete(self.arun(initial_state))
        except RuntimeError:
            return asyncio.run(self.arun(initial_state))
