import React from 'react';
import { Layers } from 'lucide-react';

export const MilestoneGrid: React.FC = () => {
  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <span>Autonomous Agents Lab — 4-Milestone Engineering Suite</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Production implementations developed across all four lab milestones.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card-hover p-6 space-y-3 border-indigo-500/20">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Milestone 1</div>
            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300">Verified</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Agent Design & Context Management</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Constrained vs Unconstrained ReAct, Single-Path Intent Routing, FIFO rolling context window pruning,
            and quadratic token tax mitigation ($O(N^2) \rightarrow O(N)$).
          </p>
        </div>

        <div className="glass-card-hover p-6 space-y-3 border-cyan-500/20">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Milestone 2</div>
            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300">Verified</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Model Context Protocol (FastMCP)</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            FastMCP server implementation enforcing the 8 protocol concerns: Capability Negotiation,
            Notifications (`tools/list_changed`), Human Elicitation, Resources, Prompts, and Progress Tracking.
          </p>
        </div>

        <div className="glass-card-hover p-6 space-y-3 border-emerald-500/20">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Milestone 3</div>
            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300">Verified</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Cognitive Memory & Multi-Architecture RAG</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Rolling STM buffer + decoupled scratchpad, promote-or-drop router, episodic memory, semantic consolidation,
            plus Naive, BM25+Vector Hybrid, Agentic Multi-Hop, GraphRAG, and PGVector embedding engines.
          </p>
        </div>

        <div className="glass-card-hover p-6 space-y-3 border-amber-500/20">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">Milestone 4</div>
            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300">Verified</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">DAG Decomposition & MCTS Planning Sandbox</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Static vs Dynamic Task Decomposition, Sub-Task Routing (Plan-and-Solve, Tree of Thoughts, LATS MCTS),
            Self-Refine, Reflexion, and grounded Egyptian Law 4/1996 real-database verification.
          </p>
        </div>
      </div>
    </section>
  );
};
