"""
BaseNode — class-based, robust node abstraction (SOLID).
Each state is a class with typed input/output, retries, timeout, and real LLM hook.
"""
from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from state_graph.models import GraphState, NodeResult

logger = logging.getLogger("state_graph.nodes")


class BaseNode(ABC):
    name: str = "base"
    max_retries: int = 1
    timeout_s: float = 30.0

    @abstractmethod
    async def execute(self, state: GraphState) -> NodeResult:  # noqa: D102
        ...

    async def run(self, state: GraphState) -> NodeResult:
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                return await asyncio.wait_for(self.execute(state), timeout=self.timeout_s)
            except asyncio.TimeoutError as e:
                last_exc = e
                logger.warning(f"Node {self.name} timeout attempt {attempt}")
            except Exception as e:
                last_exc = e
                logger.warning(f"Node {self.name} failed attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    return NodeResult(status="FAIL", error_details={"node": self.name, "error": str(e)}, log_message=f"Node {self.name} failed: {e}")
                await asyncio.sleep(0.2 * (attempt + 1))
        return NodeResult(status="FAIL", error_details={"node": self.name, "error": str(last_exc)}, log_message=f"Node {self.name} failed after retries")

    def wrap(self):
        async def _fn(state: GraphState) -> NodeResult:
            return await self.run(state)
        _fn.__name__ = self.name
        return _fn
