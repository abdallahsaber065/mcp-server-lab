"""
Plan-and-Solve Single-Pass Algorithm (planning/plan_and_solve.py)
Directly adapts TA reference toolkit plan_and_solve module.
"""

from langchain_core.language_models.chat_models import BaseChatModel


def plan_and_solve(question: str, llm: BaseChatModel) -> str:
    """
    Executes Plan-and-Solve single-pass prompting for forward-looking operational schedules.
    """
    response = llm.invoke([
        ("system", "You are a Strategic Planning & Scheduling Agent for emergency property management. Your task is to output a FORWARD-LOOKING OPERATIONAL PLAN, TIMELINE SCHEDULE, AND STRATEGY for the Property Manager. Do NOT report fake past timestamps or pretend unexecuted actions already occurred. Instead, output actionable future milestones, vendor priority assignments, and risk mitigations."),
        ("human", f"""{question}

First analyze the operational requirements and devise a structured plan. Then output the forward-looking action schedule, timeline milestones, and vendor priorities step by step."""),
    ], temperature=0.2)

    if not isinstance(response.content, str) or not response.content.strip():
        raise RuntimeError("The chat model returned an empty or unsupported response")
    return response.content.strip()
