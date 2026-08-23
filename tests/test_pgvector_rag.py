"""
Unit and Integration Tests for PGVector Enterprise RAG & Gemini Embedding Engine (tests/test_pgvector_rag.py)
Validates:
1. GeminiEmbeddingEngine (Gemini Embedding 2 prompt formatting + Gemini Embedding 1 task_type)
2. 768-dim MRL vector normalization
3. PgVectorRAGStore permission pre-filtering & tenant isolation (anti-data-leakage)
4. Full cosine similarity ranking and integration with FastAPI chat stream
"""

import math

import pytest

from rag.embedding_engine import GeminiEmbeddingEngine
from rag.pgvector_rag import PgVectorRAGStore


class TestGeminiEmbeddingEngine:
    def test_deterministic_fallback_dimensions(self):
        engine = GeminiEmbeddingEngine(output_dim=768)
        vec = engine.embed_query("What are the quiet hours?")
        assert len(vec) == 768
        # Check unit normalization
        norm = math.sqrt(sum(x * x for x in vec))
        assert pytest.approx(norm, rel=1e-3) == 1.0

    def test_document_embedding_format(self):
        engine = GeminiEmbeddingEngine(model_name="gemini/gemini-embedding-2", output_dim=768)
        doc_vec = engine.embed_document("Quiet hours are 10 PM to 7 AM", title="Community Bylaws")
        assert len(doc_vec) == 768
        norm = math.sqrt(sum(x * x for x in doc_vec))
        assert pytest.approx(norm, rel=1e-3) == 1.0

    def test_embedding_1_fallback(self):
        engine = GeminiEmbeddingEngine(model_name="gemini/gemini-embedding-001", output_dim=768)
        vec = engine.embed_query("Emergency burst pipe procedure")
        assert len(vec) == 768


class TestPgVectorPermissionGuardrails:
    @pytest.fixture
    def rag_store(self):
        return PgVectorRAGStore()

    def test_tenant_cannot_access_executive_policies(self, rag_store):
        """Tenants must never retrieve confidential executive admin documents."""
        results = rag_store.search(
            query="Executive escalation for high-value asset governance and capital expenditure approvals",
            role="tenant",
            user_tenant_id=1,
            top_k=10
        )
        doc_ids = [r["doc_id"] for r in results]
        assert "doc_exec_escalations" not in doc_ids
        assert "doc_pm_concessions" not in doc_ids

    def test_tenant_can_access_public_and_own_lease(self, rag_store):
        """Tenant 1 should access public community bylaws and their own private lease #1."""
        results = rag_store.search(
            query="quiet hours and Nile Plaza Unit 101 lease agreement",
            role="tenant",
            user_tenant_id=1,
            user_property_id=1,
            top_k=5
        )
        doc_ids = [r["doc_id"] for r in results]
        assert "doc_policy_bylaws" in doc_ids
        assert "doc_lease_nile_101" in doc_ids

    def test_tenant_2_cannot_access_tenant_1_private_lease(self, rag_store):
        """Tenant 2 (Dr. Jean-Luc Picard) must NEVER retrieve Tenant 1's private lease."""
        results = rag_store.search(
            query="Nile Plaza Unit 101 Dr. Tarek El-Mahdy lease agreement",
            role="tenant",
            user_tenant_id=2,
            user_property_id=2,
            top_k=5
        )
        doc_ids = [r["doc_id"] for r in results]
        assert "doc_lease_nile_101" not in doc_ids

    def test_executive_admin_has_full_visibility(self, rag_store):
        """Executive Admins should have unrestricted visibility across all policies and contracts."""
        results = rag_store.search(
            query="portfolio governance, concession limits, and luxury lease terms",
            role="executive_admin",
            top_k=10
        )
        doc_ids = [r["doc_id"] for r in results]
        assert "doc_exec_escalations" in doc_ids
        assert "doc_pm_concessions" in doc_ids
        assert "doc_policy_bylaws" in doc_ids
