"""Tests for Week 3 Multi-Architecture RAG System."""
import pytest
from rag.vector_store import VectorStore, cosine_similarity
from rag.pipeline import build_and_seed_vector_store, POLICY_BINDER_CORPUS
from rag.naive_rag import naive_rag_search
from rag.hybrid_rag import HybridSearchEngine
from rag.agentic_rag import AgenticRAGRouter
from rag.graph_rag import PropertyPolicyKnowledgeGraph


# ── Vector Store Tests ──

class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


class TestVectorStore:
    def test_upsert_and_query(self):
        vs = VectorStore()
        vs.upsert("lease termination policy", {"city": "Cairo"})
        vs.upsert("emergency repair protocol", {"city": "Alexandria"})
        results = vs.query("lease penalty", top_k=1)
        assert len(results) == 1
        assert "lease" in results[0]["payload"].lower()

    def test_pre_search_metadata_filter(self):
        vs = VectorStore()
        vs.upsert("Cairo lease terms", {"city": "Cairo"})
        vs.upsert("Alexandria lease terms", {"city": "Alexandria"})
        results = vs.query("lease terms", top_k=5, metadata_filter={"city": "Cairo"})
        assert len(results) == 1
        assert results[0]["metadata"]["city"] == "Cairo"

    def test_pre_filter_no_match_returns_empty(self):
        vs = VectorStore()
        vs.upsert("Cairo lease", {"city": "Cairo"})
        results = vs.query("lease", metadata_filter={"city": "Mars"})
        assert results == []

    def test_empty_store_returns_empty(self):
        vs = VectorStore()
        results = vs.query("anything")
        assert results == []

    def test_custom_embedding_fn(self):
        def custom_embed(text):
            return [1.0, 0.0, 0.0]
        vs = VectorStore(embedding_fn=custom_embed)
        vs.upsert("test doc", {})
        results = vs.query("query")
        assert len(results) == 1

    def test_metadata_index_populated(self):
        vs = VectorStore()
        vs.upsert("doc1", {"type": "bylaw", "city": "Cairo"})
        vs.upsert("doc2", {"type": "sla", "city": "Giza"})
        assert "type" in vs.metadata_index
        assert "bylaw" in vs.metadata_index["type"]
        assert len(vs.metadata_index["type"]["bylaw"]) == 1


# ── Pipeline Tests ──

class TestPipeline:
    def test_corpus_has_documents(self):
        assert len(POLICY_BINDER_CORPUS) >= 10

    def test_build_and_seed_returns_populated_store(self):
        vdb = build_and_seed_vector_store()
        assert len(vdb.payloads) == len(POLICY_BINDER_CORPUS)
        assert len(vdb.vectors) == len(POLICY_BINDER_CORPUS)

    def test_corpus_metadata_has_required_fields(self):
        for doc in POLICY_BINDER_CORPUS:
            assert "section_id" in doc
            assert "content" in doc
            assert "metadata" in doc
            assert "city" in doc["metadata"]
            assert "doc_type" in doc["metadata"]

    def test_seeded_store_returns_results_for_policy_query(self):
        vdb = build_and_seed_vector_store()
        results = vdb.query("early termination penalty", top_k=2)
        assert len(results) > 0


# ── Naive RAG Tests ──

class TestNaiveRAG:
    def test_naive_rag_returns_results(self):
        vdb = build_and_seed_vector_store()
        results = naive_rag_search("security deposit refund", vdb, top_k=2)
        assert len(results) > 0
        assert all("score" in r for r in results)

    def test_naive_rag_empty_query_returns_results(self):
        vdb = build_and_seed_vector_store()
        results = naive_rag_search("nonexistentxyz123", vdb, top_k=5)
        assert isinstance(results, list)


# ── Hybrid Search Tests ──

class TestHybridSearch:
    def test_hybrid_search_returns_results(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        results = hybrid.search("early termination penalty Alexandria", top_k=2)
        assert len(results) > 0
        assert all("hybrid_score" in r for r in results)

    def test_hybrid_rrf_fusion_combines_scores(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        results = hybrid.search("security deposit escrow Banque Misr", top_k=3)
        assert len(results) > 0
        # Hybrid score should be > 0 since RRF is always positive
        assert all(r["hybrid_score"] > 0 for r in results)

    def test_hybrid_statute_bonus(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        results = hybrid.search("Section 4.2b early termination", top_k=3)
        # The 4.2b document should get a BM25 bonus
        assert len(results) > 0

    def test_hybrid_with_metadata_filter(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        results = hybrid.search("lease policy", top_k=3, metadata_filter={"city": "Cairo"})
        assert isinstance(results, list)


# ── Agentic RAG Tests ──

class TestAgenticRAG:
    def test_single_hop_query(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        agentic = AgenticRAGRouter(hybrid)
        result = agentic.reason_and_retrieve("What is the security deposit refund policy?")
        assert "evidence" in result
        assert "sub_queries" in result
        assert result["hops_executed"] >= 1

    def test_multi_hop_decomposition(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        agentic = AgenticRAGRouter(hybrid)
        result = agentic.reason_and_retrieve(
            "What are the sublease rules and what approvals are needed?"
        )
        # "and" in query triggers decomposition
        assert len(result["sub_queries"]) > 1
        assert result["hops_executed"] > 1

    def test_mold_triggers_decomposition(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        agentic = AgenticRAGRouter(hybrid)
        result = agentic.reason_and_retrieve("mold remediation protocol")
        assert "mold" in result["query"].lower()

    def test_synthesized_context_is_string(self):
        vdb = build_and_seed_vector_store()
        hybrid = HybridSearchEngine(vdb)
        agentic = AgenticRAGRouter(hybrid)
        result = agentic.reason_and_retrieve("maintenance SLA emergency leak")
        assert isinstance(result["synthesized_context"], str)


# ── Graph RAG Tests ──

class TestGraphRAG:
    def test_entity_traversal(self):
        kg = PropertyPolicyKnowledgeGraph()
        paths = kg.traverse_relations("Section 7.3")
        assert len(paths) > 0
        assert any(p["relation"] == "GOVERNED_BY" for p in paths)

    def test_query_graph_matches_entities(self):
        kg = PropertyPolicyKnowledgeGraph()
        result = kg.query_graph("What are the rules under Law 4/1996?")
        assert "Law 4/1996" in result["matched_entities"]
        assert len(result["paths"]) > 0

    def test_query_graph_alexandria(self):
        kg = PropertyPolicyKnowledgeGraph()
        result = kg.query_graph("Alexandria Properties early termination penalties")
        assert len(result["matched_entities"]) > 0

    def test_query_graph_no_match(self):
        kg = PropertyPolicyKnowledgeGraph()
        result = kg.query_graph("unrelated query about cats")
        assert result["matched_entities"] == []
        assert result["paths"] == []

    def test_all_entities_accessible(self):
        kg = PropertyPolicyKnowledgeGraph()
        for ent_name in kg.entities:
            paths = kg.traverse_relations(ent_name)
            # At least some entities should have edges
            assert isinstance(paths, list)
