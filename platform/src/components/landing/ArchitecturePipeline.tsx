import React from 'react';
import { Boxes, Compass, Workflow, Cpu, Radio, Database } from 'lucide-react';

export const ArchitecturePipeline: React.FC = () => {
  return (
    <section className="glass-card p-8 space-y-6 border-indigo-500/20">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 flex items-center gap-2">
            <Boxes className="w-5 h-5 text-indigo-400" />
            <span>Full-Stack Architecture & Execution Pipeline</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end trace from web client SSE streaming down to PGVector storage and LangGraph checkpoints.
          </p>
        </div>
        <span className="hidden sm:inline-block px-3 py-1 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
          Clean Modular Architecture
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-indigo-400 font-bold">
            <Compass className="w-4 h-4" />
            <span>1. Client Gateway</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Vite + React SPA with Server-Sent Events (SSE) streaming and live sub-task trace rendering.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold">
            <Workflow className="w-4 h-4" />
            <span>2. Router & State Graph</span>
          </div>
          <p className="text-[11px] text-slate-400">
            FastAPI intent router dispatching to LangGraph cyclic state machines and topological DAG planners.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-amber-400 font-bold">
            <Cpu className="w-4 h-4" />
            <span>3. Planning Sandbox</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Dynamic decomposition, Tree of Thoughts (ToT), Grounded LATS MCTS, and Reflexion self-healing.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-purple-400 font-bold">
            <Radio className="w-4 h-4" />
            <span>4. FastMCP Server</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Model Context Protocol gateway handling elicitation gates, progress tracking, and notifications.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold">
            <Database className="w-4 h-4" />
            <span>5. Dual DB & Vector Store</span>
          </div>
          <p className="text-[11px] text-slate-400">
            SQLAlchemy 2.0 ORM, PGVector (768-dim Gemini Embedding 2), and SQLite WAL / Async Redis.
          </p>
        </div>
      </div>
    </section>
  );
};
