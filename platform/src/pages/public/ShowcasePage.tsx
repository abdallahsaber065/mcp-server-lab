/**
 * Showcase & Empirical Benchmarks Page (platform/src/pages/public/ShowcasePage.tsx)
 * Faithfully preserves and elevates the benchmark tables and causal analysis from legacy showcase.js
 */

import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  Cpu,
  Layers,
  Shield,
  Zap,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { apiClient } from '../../services/api';

export const ShowcasePage: React.FC = () => {
  const [benchmarkData, setBenchmarkData] = useState<any>(null);

  useEffect(() => {
    async function fetchBenchmarks() {
      try {
        const res = await apiClient<{ benchmarks: any }>('/api/showcase/benchmarks', { skipAuth: true });
        setBenchmarkData(res.benchmarks);
      } catch (err) {
        console.error('Failed to fetch benchmarks:', err);
      }
    }
    fetchBenchmarks();
  }, []);

  return (
    <div className="space-y-10 pb-16">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
          <Activity className="w-3.5 h-3.5" />
          <span>Empirical Evaluation Suite & Architectural Benchmarks</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100">
          Architectural Performance & Trade-off Analysis
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-3xl">
          Comprehensive empirical measurements across Agent Decision Architectures (Week 1), Model Context Protocol
          Integration (Week 2), Episodic & Semantic Memory (Week 3), and Task Decomposition & Planning (Week 4).
        </p>
      </div>

      {/* Key Metric Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Self-RAG Precision</div>
          <div className="text-2xl font-black text-emerald-400">95.0%</div>
          <div className="text-[10px] text-slate-400">Verified via grounded citations</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">MCTS (LATS) Success</div>
          <div className="text-2xl font-black text-indigo-400">95.0%</div>
          <div className="text-[10px] text-slate-400">19/20 on complex emergency scenarios</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">ReAct History Tax</div>
          <div className="text-2xl font-black text-amber-400">O(N²)</div>
          <div className="text-[10px] text-slate-400">Quadratic token re-transmission</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Dynamic Tool Matrix</div>
          <div className="text-2xl font-black text-cyan-400">14 Tools</div>
          <div className="text-[10px] text-slate-400">MCP listChanged event notifications</div>
        </div>
      </div>

      {/* Planning & Decomposition Comparison Table (Week 4) */}
      <section className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Task Decomposition & Planning Algorithms Comparison</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Empirical trials across 20 emergency multi-step property management scenarios.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            N=20 Trials
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                <th className="p-3">Architecture Strategy</th>
                <th className="p-3">Success Rate</th>
                <th className="p-3">Avg LLM Calls</th>
                <th className="p-3">Avg Tokens</th>
                <th className="p-3">Avg Latency</th>
                <th className="p-3">Est. Cost / Run</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              <tr className="hover:bg-slate-800/30">
                <td className="p-3 font-semibold text-slate-100">Plan-and-Solve (Static)</td>
                <td className="p-3 text-amber-400">12 / 20 (60%)</td>
                <td className="p-3">1.0 call</td>
                <td className="p-3">1,500 tokens</td>
                <td className="p-3">0.9s</td>
                <td className="p-3">$0.01</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="p-3 font-semibold text-slate-100">Tree of Thoughts (ToT)</td>
                <td className="p-3 text-indigo-400">17 / 20 (85%)</td>
                <td className="p-3">4.0 calls</td>
                <td className="p-3">5,200 tokens</td>
                <td className="p-3">3.8s</td>
                <td className="p-3">$0.04</td>
              </tr>
              <tr className="hover:bg-slate-800/30 bg-indigo-950/20 font-medium">
                <td className="p-3 font-bold text-cyan-300">LATS / MCTS (Autonomous Tree Search)</td>
                <td className="p-3 font-bold text-emerald-400">19 / 20 (95%)</td>
                <td className="p-3 font-bold">8.5 calls</td>
                <td className="p-3 font-bold">11,400 tokens</td>
                <td className="p-3 font-bold">8.2s</td>
                <td className="p-3 font-bold">$0.08</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="p-3 font-semibold text-slate-100">Static DAG Execution</td>
                <td className="p-3 text-amber-400">14 / 20 (70%)</td>
                <td className="p-3">5.0 calls</td>
                <td className="p-3">6,200 tokens</td>
                <td className="p-3">3.1s</td>
                <td className="p-3">$0.04</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="p-3 font-semibold text-slate-100">Dynamic Interleaved Re-planning</td>
                <td className="p-3 text-indigo-400">17 / 20 (85%)</td>
                <td className="p-3">~7 calls</td>
                <td className="p-3">8,900 tokens</td>
                <td className="p-3">5.4s</td>
                <td className="p-3">$0.06</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Causal Tradeoff Analysis Cards (from showcase.js) */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 space-y-3 border-amber-500/20">
          <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm">
            <Zap className="w-4 h-4" />
            <span>The ReAct Re-transmission Tax: O(N²) Quadratic Growth</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            In standard ReAct loops, every step re-transmits the complete conversation transcript and prior tool
            observations back to the model. As the execution trajectory grows from 1 to 10 steps, token usage scales
            quadratically (N*(N+1)/2), drastically inflating API costs and increasing latency.
          </p>
        </div>

        <div className="glass-card p-6 space-y-3 border-cyan-500/20">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold text-sm">
            <Shield className="w-4 h-4" />
            <span>State Graph Checkpointing vs Free-Form ReAct</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            LangGraph-style State Graphs replace open-ended ReAct loops with structured state transitions. Each node
            modifies a strongly-typed graph state stored in SQLite/Postgres. This guarantees deterministic recovery,
            enables Human-in-the-Loop review, and prevents infinite validation loops.
          </p>
        </div>
      </section>
    </div>
  );
};
