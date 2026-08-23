"""Naive RAG: Vector Similarity Baseline."""
from typing import Any, Dict, List

from rag.vector_store import VectorStore


def naive_rag_search(query: str, vector_store: VectorStore, top_k: int = 3) -> List[Dict[str, Any]]:
    return vector_store.query(query_text=query, top_k=top_k)
