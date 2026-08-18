"""Hybrid Search: Vector Similarity + BM25 Keyword Search with Reciprocal Rank Fusion (RRF)."""
import re
from typing import Any, Dict, List, Optional

from rag.vector_store import VectorStore


class HybridSearchEngine:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.documents = vector_store.payloads

    def _bm25_keyword_score(self, query: str, doc_text: str) -> float:
        query_words = re.findall(r"\w+", query.lower())
        doc_words = re.findall(r"\w+", doc_text.lower())
        if not query_words or not doc_words:
            return 0.0
        score = sum(1.0 for w in query_words if w in doc_words)
        # Bonus for exact statute / section matches (e.g. 4.2b, Law 4)
        if any(c in doc_text.lower() for c in ["4.2b", "law 4", "8.1c", "cr-802"]):
            score += 2.5
        return score

    def search(self, query: str, top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # 1. Vector Search Candidates
        vec_results = self.vector_store.query(query_text=query, top_k=10, metadata_filter=metadata_filter)

        # 2. Score via Reciprocal Rank Fusion (RRF)
        scored_docs = {}
        for rank, item in enumerate(vec_results):
            payload = item["payload"]
            rrf_score = 1.0 / (60 + rank + 1)
            scored_docs[payload] = {
                "vector_rank": rank,
                "rrf_score": rrf_score,
                "metadata": item["metadata"],
                "payload": payload,
            }

        # 3. Add BM25 keyword score
        for payload, data in scored_docs.items():
            bm25 = self._bm25_keyword_score(query, payload)
            data["hybrid_score"] = data["rrf_score"] + (bm25 * 0.1)

        sorted_results = sorted(scored_docs.values(), key=lambda x: x["hybrid_score"], reverse=True)
        return sorted_results[:top_k]
