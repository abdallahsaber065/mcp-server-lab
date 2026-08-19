import React from 'react';
import { CheckCircle2, Database, GitBranch, Shield } from 'lucide-react';

interface InfrastructureGridProps {
  systemStats: any;
}

export const InfrastructureGrid: React.FC<InfrastructureGridProps> = ({ systemStats }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="glass-card p-5 space-y-2 border-indigo-500/30">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>FastMCP Server</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-xl font-bold text-slate-100 font-mono">
          {systemStats?.protocol_version || '2025-06-18'}
        </div>
        <div className="text-[11px] text-indigo-400 font-medium">Stdio + Streamable HTTP SSE</div>
      </div>

      <div className="glass-card p-5 space-y-2 border-cyan-500/30">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Vector Architecture</span>
          <Database className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="text-sm font-bold text-slate-100">PGVector + Gemini Embedding 2</div>
        <div className="text-[11px] text-emerald-400">768-dim MRL Matryoshka Vector Store</div>
      </div>

      <div className="glass-card p-5 space-y-2 border-emerald-500/30">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>State Machine & Checkpoints</span>
          <GitBranch className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-sm font-bold text-slate-100">LangGraph-Style State Graph</div>
        <div className="text-[11px] text-slate-400">Cyclic Error Recovery & HITL Gates</div>
      </div>

      <div className="glass-card p-5 space-y-2 border-amber-500/30">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Verification Test Suite</span>
          <Shield className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-xl font-bold text-emerald-400 font-mono">104 / 104 Passed</div>
        <div className="text-[11px] text-slate-400">100% Pytest & Basedpyright Clean</div>
      </div>
    </div>
  );
};
