"""
Unified Planning Agent (agent/planning_agent.py)
Orchestrates static vs dynamic DAG task decomposition, sub-task routing (PS, ToT, LATS),
self-correction (Self-Refine, Reflexion), and grounded environment feedback.
Reuses existing mcp_server/ and db/ without touching Week 1-3 memory/RAG code paths.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import litellm
from langchain_core.language_models.chat_models import BaseChatModel

from planning.decomposition import decompose_goal, execute_plan, final_output
from planning.dynamic_decomposition import dynamic_decomposition
from planning.environment import Environment
from planning.lats import lats
from planning.plan_and_solve import plan_and_solve
from planning.reflexion import reflexion
from planning.self_refine import reflect_and_refine
from planning.tree_of_thoughts import tree_of_thoughts

logger = logging.getLogger(__name__)

SUBTASK_ROUTER_PROMPT = """You are a Master Planning Algorithm Router for Cornerstone Realty Group B property management systems.
Your job is to analyze a sub-task instruction and route it to the single best search/execution algorithm among:

1. "ToT" (Tree of Thoughts / Beam Search):
   - Use when the sub-task requires evaluating multiple candidate options, ranking contractors/vendors, comparing hotel relocation facilities, or trade-off decision trees.
   - Examples: "Rank emergency plumbing vendors by response time and hourly rate", "Compare partner hotel options in Maadi vs Zamalek", "Propose top 3 contractor allocation strategies".

2. "LATS" (Language Agent Tree Search / MCTS + Grounded Environment):
   - Use when the sub-task requires legal SLA compliance verification, Egyptian Law 4/1996 habitability audits, structural engineering sign-off, or multi-branch constraint validation.
   - Examples: "Verify compliance under Law 4/1996 Clause 8.1c for emergency 4-hour SLA", "Perform structural integrity clearance and slab moisture audit", "Check legal liability for tenant displacement stipend".

3. "PS" (Plan-and-Solve / Standard Sequential Execution):
   - Use when the sub-task is a deterministic operational step, status tracking, work order creation, notification dispatch, or site monitoring.
   - Examples: "Issue formal notices to affected tenants", "Set up 24-hour digital status monitoring alert", "Close out completed work order in property database".

Return ONLY valid JSON matching: {"method": "PS" | "ToT" | "LATS", "rationale": "<1-sentence reason>"}"""


class PlanningAgent:
    def __init__(self, llm: BaseChatModel, mode: str = "dynamic"):
        self.llm = llm
        self.mode = mode
        self.environment = Environment(mode="grounded")
        self.traces: List[Dict[str, Any]] = []

    def route_subtask(self, instruction: str) -> str:
        """
        Routes a sub-task instruction to PS, ToT, or LATS using Mistral 7B structured classification with heuristic fallback.
        """
        try:
            resp = litellm.completion(
                model="mistral/open-mistral-7b",
                messages=[
                    {"role": "system", "content": SUBTASK_ROUTER_PROMPT},
                    {"role": "user", "content": f"Sub-Task Instruction: {instruction}"}
                ],
                temperature=0.0
            )
            raw = resp.choices[0].message.content or "{}"
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            method = str(data.get("method", "PS")).upper()
            if method in ["PS", "TOT", "LATS"]:
                return "ToT" if method == "TOT" else method
        except Exception as e:
            logger.warning(f"Mistral sub-task routing failed ({e}), using heuristic fallback")

        instr_lower = instruction.lower()
        if any(k in instr_lower for k in ["rank", "vendor", "priority", "compare", "propose options"]):
            return "ToT"
        elif any(k in instr_lower for k in ["relocat", "law 4/1996", "verify", "emergency", "audit", "compliance"]):
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

    def execute_request(self, request: str, step_callback: Optional[Any] = None) -> Dict[str, Any]:
        """
        Executes top-level enterprise request using static or dynamic DAG decomposition,
        invoking step_callback(st_data) in real time after each sub-task completion.
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

                    st_data = {"task_id": task_id, "instruction": task_item.instruction, "routing": res}
                    trace["subtasks"].append(st_data)
                    if step_callback:
                        step_callback(st_data)

            summary = final_output(plan, raw_outputs)
            trace["summary"] = summary
        else:
            history = dynamic_decomposition(request, self.llm, max_steps=3)
            trace["history"] = history

            executed_steps = []
            for task, raw_res in history:
                method = self.route_subtask(task)
                res = self.execute_subtask(task, method)
                executed_steps.append((task, res))

                st_data = {
                    "instruction": task,
                    "method": method,
                    "result": res,
                    "routing": res
                }
                trace["subtasks"].append(st_data)
                if step_callback:
                    step_callback(st_data)

            # Synthesize clean executive summary instead of raw string concatenation
            synthesis_prompt = f"""Synthesize a concise, polished Executive Action Plan (in clean Markdown) for the goal: {request!r}
Based on these executed sub-task results:
"""
            for task, res in executed_steps:
                synthesis_prompt += f"\n- Sub-task ({res.get('method')}): {task}\n  Output: {res.get('output')}\n"

            syn_res = self.llm.invoke([
                ("system", "You are an executive property management planner. Produce a clean, concise, non-repetitive Markdown synthesis of the action plan."),
                ("human", synthesis_prompt)
            ])
            summary = syn_res.content if hasattr(syn_res, "content") else str(syn_res)
            trace["summary"] = summary

        self.traces.append(trace)
        self._save_trace(trace)
        return {"status": "success", "summary": summary, "trace": trace}

    def _save_trace(self, trace: Dict[str, Any]) -> None:
        art_dir = Path("artifacts")
        art_dir.mkdir(exist_ok=True)
        with open(art_dir / "planning_traces.json", "a") as f:
            f.write(json.dumps(trace) + "\n")
