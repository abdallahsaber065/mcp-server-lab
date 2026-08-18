"""
Gemini Embedding Engine (rag/embedding_engine.py)
Implements official Google Gemini Embeddings specifications:
- Primary: `gemini-embedding-2` (latest multimodal & multilingual embedding model)
- Switchable / Fallback: `gemini-embedding-001` (text-only predecessor)
- Matryoshka Representation Learning (MRL) dimension truncation to 768 dims
- Prompt task formatting for gemini-embedding-2
- Offline deterministic normalized vector generator for zero-crash testing
"""

import os
import math
import hashlib
import logging
from typing import List, Optional, Union
import litellm

logger = logging.getLogger("gemini_embedding_engine")


class GeminiEmbeddingEngine:
    """Enterprise Google Gemini Embedding Generator supporting Embedding 2 & Embedding 1."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        output_dim: int = 768,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "gemini/gemini-embedding-2")
        self.output_dim = output_dim
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def embed_query(self, query: str) -> List[float]:
        """Embeds a search query applying Gemini 2 task formatting or Gemini 1 task_type."""
        clean_q = query.strip()
        if not clean_q:
            clean_q = "default query"

        # Gemini Embedding 2 uses prompt task instructions
        if "embedding-2" in self.model_name:
            formatted_text = f"task: search result | query: {clean_q}"
            return self._call_embedding(formatted_text)

        # Gemini Embedding 1 uses task_type config
        return self._call_embedding(clean_q, task_type="RETRIEVAL_QUERY")

    def embed_document(self, content: str, title: Optional[str] = None) -> List[float]:
        """Embeds a knowledge base document applying Gemini 2 document structure or Gemini 1 task_type."""
        clean_text = content.strip()
        doc_title = title.strip() if title and title.strip() else "none"

        # Gemini Embedding 2 uses structured document format
        if "embedding-2" in self.model_name:
            formatted_text = f"title: {doc_title} | text: {clean_text}"
            return self._call_embedding(formatted_text)

        # Gemini Embedding 1 uses task_type config
        return self._call_embedding(clean_text, task_type="RETRIEVAL_DOCUMENT", title=doc_title)

    def _call_embedding(
        self,
        text: str,
        task_type: Optional[str] = None,
        title: Optional[str] = None
    ) -> List[float]:
        """Calls LiteLLM embedding API with fallback to deterministic vector."""
        if not self.api_key or self.api_key.startswith("mock_") or os.getenv("TESTING") == "1":
            return self._generate_deterministic_vector(text, self.output_dim)

        try:
            kwargs = {
                "model": self.model_name,
                "input": [text],
                "api_key": self.api_key,
            }
            # Add dimensions if supported
            if self.output_dim:
                kwargs["dimensions"] = self.output_dim

            response = litellm.embedding(**kwargs)
            if response and hasattr(response, "data") and len(response.data) > 0:
                vec = response.data[0]["embedding"]
                # Truncate to MRL dimension if needed
                if len(vec) > self.output_dim:
                    vec = vec[:self.output_dim]
                # Normalize vector to unit length for cosine distance
                return self._normalize_vector(vec)
        except Exception as e:
            logger.warning(f"LiteLLM embedding call failed ({e}). Falling back to deterministic vector.")

        return self._generate_deterministic_vector(text, self.output_dim)

    @staticmethod
    def _normalize_vector(vec: List[float]) -> List[float]:
        """Normalizes vector to L2 unit norm."""
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            return [x / norm for x in vec]
        return vec

    @staticmethod
    def _generate_deterministic_vector(text: str, dim: int = 768) -> List[float]:
        """Generates deterministic pseudo-random unit vector based on text hash for reliable offline testing."""
        vec = []
        # Seeded pseudo-random generation from SHA256 chunks
        for i in range(dim):
            h = hashlib.sha256(f"{text}:{i}".encode("utf-8")).hexdigest()
            # Map hex to float in [-1.0, 1.0]
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)

        return GeminiEmbeddingEngine._normalize_vector(vec)


# Shared global singleton instance
embedding_engine = GeminiEmbeddingEngine()
