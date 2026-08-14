"""
Unified Planning Agent (agent/planning_agent.py)
Orchestrates static vs dynamic DAG task decomposition, sub-task routing (PS, ToT, LATS),
self-correction (Self-Refine, Reflexion), and grounded environment feedback.
Reuses existing mcp_server/ and db/ without touching Week 1-3 memory/RAG code paths.
"""

from typing import Dict, Any, List
import json
import logging
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel

from planning.decomposition import decompose_goal, execute_plan, final_output
from planning.dynamic_decomposition import dynamic_decomposition
from planning.plan_and_solve import plan_and_solve
from planning.tree_of_thoughts import tree_of_thoughts
from planning.lats import lats
from planning.self_refine import reflect_and_refine
from planning.reflexion import reflexion
from planning.environment import Environment

logger = logging.getLogger(__name__)


class PlanningAgent:
    def __init__(self, llm: BaseChatModel, mode: str = "dynamic"):
        self.llm = llm
        self.mode = mode
        self.environment = Environment(mode="grounded")
        self.traces: List[Dict[str, Any]] = []

    def route_subtask(self, instruction: str) -> str:
        """
        Routes sub-tasks based on shape & risk profile:
        - Vendor Ranking / Multi-option -> Tree of Thoughts (ToT)
        - Legal SLA / Emergency Relocation -> LATS (MCTS + Grounded Env)
        - Cheap-to-redo / simple step -> Plan-and-Solve (PS)
        """
        instr_lower = instruction.lower()
        if "rank" in instr_lower or "vendor" in instr_lower or "priority" in instr_lower:
            return "ToT"
        elif "relocat" in instr_lower or "law 4/1996" in instr_lower or "verify" in instr_lower or "emergency" in instr_lower:
            return "LATS"
        else:
            return "PS"

    def execute_subtask(self, subtask_name: str, method: str) -> Dict[str, Any]:
        """
        Executes a single sub-task using the routed planning algorithm.
        """
        if method == "PS":
            output = plan_and_solve(subtask_name, self.llm)
            return {"method": "PS", "output": output, "status": "success"}
        elif method == "ToT":
            thoughts = tree_of_thoughts(subtask_name, self.llm, depth=2, beam_width=2)
            best_thought = thoughts[0] if thoughts else None
            return {
                "method": "ToT",
                "output": best_thought.state if best_thought else "No valid thought",
                "score": best_thought.score if best_thought else 0.0,
                "status": "success"
            }
        elif method == "LATS":
            lats_res = lats(subtask_name, self.llm, self.environment, iterations=2, n_actions=2)
            return {
                "method": "LATS",
                "output": lats_res.output,
                "success": lats_res.success,
                "best_score": lats_res.best_score,
                "status": "success" if lats_res.success else "failed_grounding"
            }
        else:
            output = plan_and_solve(subtask_name, self.llm)
            return {"method": "PS", "output": output, "status": "success"}

    def execute_request(self, request: str) -> Dict[str, Any]:
        """
        Executes top-level enterprise request using static or dynamic DAG decomposition.
        """
        logger.info(f"Executing request (mode={self.mode}): {request}")
        trace: Dict[str, Any] = {"request": request, "mode": self.mode, "subtasks": []}

        if self.mode == "static":
            plan = decompose_goal(request, self.llm)
            trace["plan_dag"] = [t.model_dump() for t in plan.tasks]
            
            raw_outputs = {}
            for batch in plan.execution_batches():
                for task_id in batch:
                    task_item = plan.task(task_id)
                    method = self.route_subtask(task_item.instruction)
                    res = self.execute_subtask(task_item.instruction, method)
                    raw_outputs[task_id] = str(res["output"])
                    trace["subtasks"].append({"task_id": task_id, "instruction": task_item.instruction, "routing": res})

            summary = final_output(plan, raw_outputs)
            trace["summary"] = summary
        else:
            history = dynamic_decomposition(request, self.llm, max_steps=4)
            trace["history"] = history
            for task, res in history:
                method = self.route_subtask(task)
                trace["subtasks"].append({"instruction": task, "method": method, "result": res})
            summary = "\n".join(f"{task}: {res}" for task, res in history)
            trace["summary"] = summary

        self.traces.append(trace)
        self._save_trace(trace)
        return {"status": "success", "summary": summary, "trace": trace}

    def _save_trace(self, trace: Dict[str, Any]) -> None:
        art_dir = Path("artifacts")
        art_dir.mkdir(exist_ok=True)
        with open(art_dir / "planning_traces.json", "a") as f:
            f.write(json.dumps(trace) + "\n")
