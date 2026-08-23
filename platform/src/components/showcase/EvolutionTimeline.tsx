import React from 'react';
import { GitBranch, CheckCircle2, Shield, Database, Cpu } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';
import { Badge } from '../common/Badge';

export const EvolutionTimeline: React.FC = () => {
  return (
    <Card className="p-6 sm:p-8 space-y-6">
      <SectionHeader
        icon={GitBranch}
        title="System Architectural Evolution"
        subtitle="From Week 2 FastMCP protocol foundations to Week 3 RAG and Week 4 Autonomous Planning"
        iconColor="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-indigo-500/20 space-y-2.5 hover:border-indigo-500/40 transition-all">
          <div className="flex items-center justify-between">
            <Badge variant="indigo" size="sm">Week 2 · Protocol</Badge>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">FastMCP & 8 Core Concerns</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Capability negotiation, listChanged live notifications, human elicitation, progress tracking, defensive
            Pydantic validation, and provider-agnostic LiteLLM engine.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-blue-500/20 space-y-2.5 hover:border-blue-500/40 transition-all">
          <div className="flex items-center justify-between">
            <Badge variant="cyan" size="sm">Week 3 · Memory & RAG</Badge>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">5 RAG Modes & Consolidation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Naive, Hybrid BM25+RRF, Agentic multi-hop, and Graph RAG. 3-tier memory consolidation (STM, Episodic,
            Semantic) with real contradiction resolution.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-purple-500/20 space-y-2.5 hover:border-purple-500/40 transition-all">
          <div className="flex items-center justify-between">
            <Badge variant="purple" size="sm">Week 4 · Planning</Badge>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">DAG Decomposition & MCTS</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Dynamic interleaved DAG planner, Plan-and-Solve, Tree of Thoughts Beam Search, Grounded MCTS (LATS),
            Self-Refine, and Reflexion memory loops.
          </p>
        </div>
      </div>
    </Card>
  );
};
