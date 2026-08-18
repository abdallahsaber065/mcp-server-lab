"""Agentic RAG: Multi-Hop Reasoning Loop with Query Decomposition & Rewriting."""
from typing import Any, Dict, List

from rag.hybrid_rag import HybridSearchEngine


class AgenticRAGRouter:
    def __init__(self, hybrid_engine: Any):
        if isinstance(hybrid_engine, HybridSearchEngine):
            self.hybrid_engine = hybrid_engine
        else:
            self.hybrid_engine = HybridSearchEngine(vector_store=hybrid_engine)

    def reason_and_retrieve(self, complex_query: str, max_hops: int = 3) -> Dict[str, Any]:
        retrieval_history = []
        collected_evidence = []

        # Step 1: Decompose query into sub-questions if multi-part
        sub_queries = self._decompose_query(complex_query)

        for sub_q in sub_queries:
            # Step 2: Retrieve evidence for each sub-query
            matches = self.hybrid_engine.search(sub_q, top_k=2)
            for m in matches:
                if m["payload"] not in collected_evidence:
                    collected_evidence.append(m["payload"])
            retrieval_history.append({"sub_query": sub_q, "matches_count": len(matches)})

        # Step 3: Synthesize multi-hop answer
        synthesized_context = "\n\n".join(collected_evidence)
        return {
            "query": complex_query,
            "sub_queries": sub_queries,
            "hops_executed": len(sub_queries),
            "evidence": collected_evidence,
            "synthesized_context": synthesized_context,
        }

    def _decompose_query(self, query: str) -> List[str]:
        q_lower = query.lower()
        if "and" in q_lower or "sublease" in q_lower or "mold" in q_lower or "dispute" in q_lower:
            parts = [q.strip() for q in query.split("?") if q.strip()]
            if len(parts) > 1:
                return parts
            return [
                query,
                f"Statutory requirements and approvals for {query[:60]}",
                f"Emergency SLAs and penalties for {query[:60]}"
            ]
        return [query]
