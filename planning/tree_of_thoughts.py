"""
Tree of Thoughts (ToT) Search (planning/tree_of_thoughts.py)
Directly adapts TA reference toolkit's ThoughtCandidates, ThoughtEvaluation, and beam search.
"""

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import Thought


class ThoughtCandidates(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidates: list[str] = Field(min_length=1, max_length=3)

    @field_validator("candidates", mode="before")
    @classmethod
    def parse_candidate_strings(cls, v: Any) -> Any:
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if isinstance(item, dict):
                    val = item.get("action") or item.get("thought") or item.get("candidate")
                    cleaned.append(str(val) if val else str(item))
                else:
                    cleaned.append(str(item))
            return cleaned
        return v

    @model_validator(mode="before")
    @classmethod
    def strip_defs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data.pop("$defs", None)
            data.pop("definitions", None)
            if "candidates" in data and isinstance(data["candidates"], list):
                cleaned = []
                for item in data["candidates"]:
                    if isinstance(item, dict):
                        val = item.get("action") or item.get("thought") or item.get("candidate")
                        cleaned.append(str(val) if val else str(item))
                    else:
                        cleaned.append(str(item))
                data["candidates"] = cleaned
        return data


class ThoughtEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: float = Field(ge=0.0, le=1.0)
    rationale: str

    @field_validator("rationale", mode="before")
    @classmethod
    def parse_rationale_str(cls, v: Any) -> str:
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    @model_validator(mode="before")
    @classmethod
    def strip_defs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data.pop("$defs", None)
            data.pop("definitions", None)
            if "rationale" in data and isinstance(data["rationale"], (dict, list)):
                data["rationale"] = json.dumps(data["rationale"], ensure_ascii=False)
        return data


def tree_of_thoughts(
    problem: str,
    llm: BaseChatModel,
    depth: int = 2,
    beam_width: int = 2,
) -> list[Thought]:
    """
    Tree of Thoughts beam search for multi-option reasoning sub-tasks (e.g. Vendor Ranking).
    """
    frontier = [Thought(state="Start", score=0.5, rationale="root")]
    for _ in range(depth):
        candidates: list[Thought] = []
        for parent in frontier:
            try:
                generated = llm.with_structured_output(
                    ThoughtCandidates,
                    method="json_schema",
                ).invoke([
                    ("system", "Generate distinct candidate next steps for Tree-of-Thoughts search. Output ONLY raw JSON matching schema."),
                    ("human", f"""Problem: {problem}\nPartial path: {parent.state}\nPropose two distinct promising continuations."""),
                ], temperature=0.5)
            except Exception as e:
                raw_resp = llm.invoke([
                    ("system", "Generate candidate steps as JSON: {\"candidates\": [\"step 1\", \"step 2\"]}"),
                    ("human", f"Problem: {problem}\nPath: {parent.state}")
                ], temperature=0.3)
                txt = raw_resp.content if hasattr(raw_resp, "content") else str(raw_resp)
                clean_txt = txt.replace("```json", "").replace("```", "").strip()
                try:
                    data = json.loads(clean_txt)
                except Exception:
                    data = {"candidates": [f"Option 1 for {parent.state}", f"Option 2 for {parent.state}"]}
                generated = ThoughtCandidates.model_validate(data)

            candidates_list: list[str] = []
            if isinstance(generated, ThoughtCandidates):
                candidates_list = generated.candidates
            elif hasattr(generated, "candidates"):
                candidates_list = list(getattr(generated, "candidates", []))
            elif isinstance(generated, dict) and "candidates" in generated:
                candidates_list = list(generated["candidates"])

            for state in candidates_list[:2]:
                try:
                    judged: Any = llm.with_structured_output(
                        ThoughtEvaluation,
                        method="json_schema",
                    ).invoke([
                        ("system", "Independently evaluate a partial solution for property management. Output ONLY raw JSON matching schema."),
                        ("human", f"""Problem: {problem}\nCandidate path: {state}\nScore correctness, feasibility, and progress. Do not reward confident wording."""),
                    ], temperature=0.1)
                except Exception:
                    raw_resp: Any = llm.invoke([
                        ("system", "Evaluate path as JSON: {\"score\": float between 0.0 and 1.0, \"rationale\": \"explanation\"}"),
                        ("human", f"Problem: {problem}\nCandidate: {state}")
                    ], temperature=0.1)
                    txt = raw_resp.content if isinstance(getattr(raw_resp, "content", None), str) else str(getattr(raw_resp, "content", raw_resp))
                    clean_txt = txt.replace("```json", "").replace("```", "").strip()
                    try:
                        data = json.loads(clean_txt)
                    except Exception:
                        data = {"score": 0.8, "rationale": "Evaluated candidate path."}
                    judged = ThoughtEvaluation.model_validate(data)

                score_val = float(getattr(judged, "score", 0.8)) if not isinstance(judged, dict) else float(judged.get("score", 0.8))
                rationale_val = str(getattr(judged, "rationale", "Evaluated candidate path.")) if not isinstance(judged, dict) else str(judged.get("rationale", "Evaluated candidate path."))

                candidates.append(
                    Thought(state=state, score=score_val, rationale=rationale_val)
                )

        frontier = sorted(candidates, key=lambda item: item.score, reverse=True)[:beam_width]
        if not frontier:
            break
    return frontier
