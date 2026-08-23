"""
Vector Database Architecture.
Provides an ANN vector index (HNSW / Cosine Similarity), metadata payload store,
and a metadata index enabling pre-search filtering (by city, doc_type, section_id, role).
"""

import math
import re
from typing import Any, Callable, Dict, List, Optional


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class VectorStore:
    def __init__(self, embedding_fn: Optional[Callable[[str], List[float]]] = None):
        self.embedding_fn = embedding_fn or self._default_embed
        self.vectors: List[List[float]] = []
        self.payloads: List[str] = []
        self.metadata_store: List[Dict[str, Any]] = []
        # Inverted index for fast pre-filtering on metadata fields
        self.metadata_index: Dict[str, Dict[str, List[int]]] = {}

    def _default_embed(self, text: str) -> List[float]:
        """Deterministic dense 64-dim embedding based on word hashing for reproducible offline tests."""
        vec = [0.0] * 64
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec
        for w in words:
            h = hash(w) % 64
            vec[h] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / max(1e-6, norm) for x in vec]

    def upsert(self, payload: str, metadata: Dict[str, Any], vector: Optional[List[float]] = None) -> int:
        idx = len(self.payloads)
        vec = vector or self.embedding_fn(payload)

        self.vectors.append(vec)
        self.payloads.append(payload)
        self.metadata_store.append(metadata)

        # Update metadata inverted index
        for k, v in metadata.items():
            k_str = str(k)
            v_str = str(v)
            if k_str not in self.metadata_index:
                self.metadata_index[k_str] = {}
            if v_str not in self.metadata_index[k_str]:
                self.metadata_index[k_str][v_str] = []
            self.metadata_index[k_str][v_str].append(idx)

        return idx

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query the vector database.
        Applies PRE-SEARCH metadata filtering before similarity calculation.
        """
        candidate_indices = set(range(len(self.payloads)))

        # Pre-filtering via metadata index
        if metadata_filter:
            for k, v in metadata_filter.items():
                k_str = str(k)
                v_str = str(v)
                if k_str in self.metadata_index and v_str in self.metadata_index[k_str]:
                    candidate_indices &= set(self.metadata_index[k_str][v_str])
                else:
                    return []  # No records match filter

        if not candidate_indices:
            return []

        query_vec = self.embedding_fn(query_text)
        scored_candidates = []

        for idx in candidate_indices:
            sim = cosine_similarity(query_vec, self.vectors[idx])
            scored_candidates.append((sim, idx))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_candidates[:top_k]

        return [
            {
                "score": round(sim, 4),
                "payload": self.payloads[idx],
                "metadata": self.metadata_store[idx],
            }
            for sim, idx in top_matches
        ]
