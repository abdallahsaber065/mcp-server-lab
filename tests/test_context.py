"""
Executable Pytest Suite for Context Pruning & Self-RAG Verification.
"""

import pytest
from context_eval.strategies import (
    apply_sliding_window,
    apply_observation_masking,
    apply_recursive_summarization,
    apply_zone_based_pruning,
)
from context_eval.test_suite import generate_long_context_transcript
from rag.self_rag import SelfRAGVerifier


def test_observation_masking_preserves_dialogue_and_prunes_json():
    """Verify Observation Masking keeps critical dialogue while masking older tool outputs."""
    transcript, target_fact = generate_long_context_transcript(variation_id=1)
    pruned = apply_observation_masking(transcript, keep_recent_tools=3)

    # Assert dialogue survived
    dialogue_texts = [m["content"] for m in pruned if m["role"] == "user"]
    assert any("allergy" in t.lower() for t in dialogue_texts)

    # Assert older tool outputs are replaced with placeholder
    tool_msgs = [m for m in pruned if m["role"] == "tool"]
    masked_count = sum(1 for m in tool_msgs if "[tool output omitted" in m["content"])
    assert masked_count > 10


def test_self_rag_critique_rejection():
    """Verify Self-RAG rejects unsupported claims and flags hallucination."""
    verifier = SelfRAGVerifier()
    query = "What is the penalty for early lease termination under Section 4.2b?"
    evidence = ["Section 4.2b specifies an early termination penalty fee equal to 2 months rent with 60 days notice."]
    
    # Grounded answer passes
    grounded_ans = "Under Section 4.2b, the early termination penalty is two months rent."
    res1 = verifier.verify_generation(query, evidence, grounded_ans)
    assert res1.is_supported == "fully_supported"

    # Hallucinated answer is rejected
    hallucinated_ans = "The penalty is 6 months rent and forfeiture of all furniture under Section 99."
    res2 = verifier.verify_generation(query, evidence, hallucinated_ans)
    assert res2.is_supported == "no_support"
