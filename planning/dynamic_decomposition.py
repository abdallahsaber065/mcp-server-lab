from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, model_validator


class DynamicDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    done: bool
    next_task: str

    @model_validator(mode="before")
    @classmethod
    def strip_defs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data.pop("$defs", None)
            data.pop("definitions", None)
        return data


def dynamic_decomposition(goal: str, llm: BaseChatModel, max_steps: int = 4) -> list[tuple[str, str]]:
    history: list[tuple[str, str]] = []
    for step in range(max_steps):
        observation = "\n".join(f"{task}: {result}" for task, result in history) or "None"
        try:
            decision: Any = llm.with_structured_output(
                DynamicDecision,
                method="json_schema",
            ).invoke([
                ("system", "You are an adaptive emergency property manager for Cornerstone Realty Group B. Use prior contractor observations before deciding what comes next."),
                ("human", f"""Goal: {goal}
Completed work and observations:
{observation}

Decide the single best next task. Set done to true only when the goal is met.
When done is true, use an empty string for next_task."""),
            ], temperature=0.1)
        except Exception:
            if history:
                break
            decision = DynamicDecision(done=False, next_task=f"Execute emergency response plan for: {goal}")

        is_done = bool(getattr(decision, "done", False)) if not isinstance(decision, dict) else bool(decision.get("done", False))
        if is_done:
            break
        task = str(getattr(decision, "next_task", "")).strip() if not isinstance(decision, dict) else str(decision.get("next_task", "")).strip()
        if not task:
            raise ValueError(f"Dynamic planner omitted next_task at step {step + 1}")
        response = llm.invoke([
            ("system", "Execute the next adaptive sub-task using the observations provided."),
            ("human", f"Goal: {goal}\nNext task: {task}\nPrior observations:\n{observation}"),
        ], temperature=0.2)
        result = response.content
        if not isinstance(result, str) or not result.strip():
            raise RuntimeError("The chat model returned an empty or unsupported response")
        result = result.strip()
        history.append((task, result))
    return history
