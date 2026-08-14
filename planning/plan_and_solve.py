"""
Plan-and-Solve Single-Pass Algorithm (planning/plan_and_solve.py)
Directly adapts TA reference toolkit plan_and_solve module.
"""

from langchain_core.language_models.chat_models import BaseChatModel


def plan_and_solve(question: str, llm: BaseChatModel) -> str:
    """
    Executes Plan-and-Solve single-pass prompting.
    """
    response = llm.invoke([
        ("system", "You use Plan-and-Solve prompting for emergency property management. Clearly separate PLAN from SOLUTION."),
        ("human", f"""{question}

First understand the problem and devise a plan to solve it. Then carry out the
plan step by step. Check calculations and common-sense assumptions."""),
    ], temperature=0.2)
    
    if not isinstance(response.content, str) or not response.content.strip():
        raise RuntimeError("The chat model returned an empty or unsupported response")
    return response.content.strip()
