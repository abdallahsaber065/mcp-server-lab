"""
Master Benchmark Runner for Week 3 Lab.
Executes MCP Server performance benchmarks, Context Window Management benchmarks,
and Retrieval Architecture benchmarks.
Outputs structured metrics to benchmarks/benchmark_results.json.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from context_eval.run_context_benchmarks import run_all_context_benchmarks
from mcp_server.server import CornerstoneMCPServer
from rag.agentic_rag import AgenticRAGRouter
from rag.graph_rag import PropertyPolicyKnowledgeGraph
from rag.hybrid_rag import HybridSearchEngine
from rag.naive_rag import naive_rag_search
from rag.pipeline import build_and_seed_vector_store
from retrieval_eval.test_questions import TEST_QUESTIONS


def run_mcp_performance_benchmarks(trials: int = 5) -> List[Dict[str, Any]]:
    """Execute reproducible MCP server performance trials."""
    server = CornerstoneMCPServer()
    results = []

    operations_to_test = [
        ("initialize_handshake", lambda: server.get_capabilities()),
        ("list_tools_discovery", lambda: server.list_tools("property_manager")),
        ("read_lease_policy_resource", lambda: server.read_resource("realty://policies/lease_terms")),
        ("query_available_units", lambda: server.call_tool("lookup_available_units", {"city": "Cairo"})),
        ("submit_maintenance_request", lambda: server.call_tool("submit_maintenance_request", {
            "tenant_id": 1, "unit_id": 101, "issue_description": "HVAC unit noisy", "priority": "medium"
        })),
        ("modify_lease_terms_elicitation", lambda: server.call_tool("modify_lease_terms", {
            "lease_id": 1, "new_monthly_rent": 9500.0, "duration_months": 12, "executive_approval_given": False
        })),
        ("run_property_audit_progress", lambda: server.call_tool("run_property_audit", {"property_id": 1}))
    ]

    print("\n=== RUNNING MCP SERVER PERFORMANCE BENCHMARKS ===")
    for op_name, op_func in operations_to_test:
        latencies = []
        statuses = []
        for _ in range(trials):
            t0 = time.perf_counter()
            res = op_func()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)
            status = res.get("status", "ok") if isinstance(res, dict) else "ok"
            statuses.append(status)

        avg_lat = sum(latencies) / len(latencies)
        entry = {
            "operation": op_name,
            "trial_count": trials,
            "avg_latency_ms": round(avg_lat, 3),
            "min_latency_ms": round(min(latencies), 3),
            "max_latency_ms": round(max(latencies), 3),
            "statuses": list(set(statuses)),
        }
        results.append(entry)
        print(f"  [{op_name}] Avg: {avg_lat:.3f} ms | Statuses: {set(statuses)}")

    return results


def run_retrieval_architecture_benchmarks() -> List[Dict[str, Any]]:
    """Benchmark all 4 RAG architectures against 12 domain test questions."""
    vdb = build_and_seed_vector_store()
    hybrid = HybridSearchEngine(vdb)
    agentic = AgenticRAGRouter(hybrid)
    graph = PropertyPolicyKnowledgeGraph()

    architectures = [
        ("Naive RAG", lambda q: naive_rag_search(q, vdb, top_k=2)),
        ("Hybrid Search (Vector + BM25)", lambda q: hybrid.search(q, top_k=2)),
        ("Agentic RAG (Multi-Hop)", lambda q: agentic.reason_and_retrieve(q)),
        ("Graph RAG (Entity Traversal)", lambda q: graph.query_graph(q)),
    ]

    results = []
    print("\n=== RUNNING RETRIEVAL ARCHITECTURE BENCHMARKS (12 DOMAIN QUESTIONS) ===")

    for name, arch_fn in architectures:
        correct = 0
        total_tokens = 0
        t0 = time.time()

        for tq in TEST_QUESTIONS:
            q = tq["query"]
            expected = tq["expected_keywords"]
            out = arch_fn(q)
            out_str = str(out)
            tokens = len(out_str) // 4
            total_tokens += tokens
            if any(k.lower() in out_str.lower() for k in expected):
                correct += 1

        elapsed = time.time() - t0
        entry = {
            "architecture": name,
            "accuracy_score": f"{correct}/{len(TEST_QUESTIONS)}",
            "accuracy_pct": round((correct / len(TEST_QUESTIONS)) * 100, 1),
            "avg_tokens_per_query": total_tokens // len(TEST_QUESTIONS),
            "avg_latency_sec": round(elapsed / len(TEST_QUESTIONS), 3),
        }
        results.append(entry)
        print(f"  [{name}] Score: {entry['accuracy_score']} | Tokens: {entry['avg_tokens_per_query']} | Latency: {entry['avg_latency_sec']}s")

    return results


def run_context_management_benchmarks() -> List[Dict[str, Any]]:
    """Run Ahmed's context pruning strategy benchmarks."""
    return run_all_context_benchmarks()


def main():
    mcp_results = run_mcp_performance_benchmarks(trials=5)
    retrieval_results = run_retrieval_architecture_benchmarks()
    context_results = run_context_management_benchmarks()

    master_results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mcp_server_benchmarks": mcp_results,
        "retrieval_architecture_benchmarks": retrieval_results,
        "context_management_benchmarks": context_results,
    }

    out_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2)
    print(f"\n[SUCCESS] Master benchmarks saved to {out_file}")


if __name__ == "__main__":
    main()
