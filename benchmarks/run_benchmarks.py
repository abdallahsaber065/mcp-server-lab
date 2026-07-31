import os
import sys
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.server import CornerstoneMCPServer

def run_performance_benchmarks(trials: int = 5) -> Dict[str, Any]:
    """Execute reproducible performance trials and generate trace logs."""
    server = CornerstoneMCPServer()
    
    benchmark_data = {
        "metadata": {
            "server_name": server.name,
            "version": server.version,
            "protocol_version": server.protocol_version,
            "total_trials_per_operation": trials,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "operations": []
    }
    
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
    
    for op_name, op_func in operations_to_test:
        latencies = []
        statuses = []
        
        for _ in range(trials):
            t0 = time.perf_counter()
            res = op_func()
            t1 = time.perf_counter()
            duration_ms = (t1 - t0) * 1000.0
            latencies.append(duration_ms)
            
            if isinstance(res, dict) and "status" in res:
                statuses.append(res["status"])
            else:
                statuses.append("success")
                
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        op_result = {
            "operation": op_name,
            "trial_count": trials,
            "avg_latency_ms": round(avg_latency, 3),
            "min_latency_ms": round(min_latency, 3),
            "max_latency_ms": round(max_latency, 3),
            "statuses": list(set(statuses)),
            "sample_latencies_ms": [round(l, 3) for l in latencies]
        }
        benchmark_data["operations"].append(op_result)
        print(f"[{op_name}] Avg: {avg_latency:.3f} ms | Min: {min_latency:.3f} ms | Max: {max_latency:.3f} ms | Statuses: {set(statuses)}")
        
    out_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\nSaved raw benchmark traces to {out_file}")
    return benchmark_data

if __name__ == "__main__":
    run_performance_benchmarks(trials=5)
