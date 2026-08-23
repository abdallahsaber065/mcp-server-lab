import React from 'react';
import { Sparkles, Bot, Workflow, Radio, ArrowRight } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export const LandingHero: React.FC = () => {
  const { setCurrentPage } = useAppStore();

  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-indigo-950/50 via-slate-900/70 to-slate-950/90 border border-slate-800 p-8 sm:p-14 shadow-2xl">
      <div className="absolute top-0 right-0 -mt-16 -mr-16 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-4xl space-y-6">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 shadow-inner">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Autonomous Multi-Agent Enterprise Operations & MCP Platform</span>
        </div>

        <h1 className="text-3xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
          Next-Generation Property Management Driven by{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400">
            State Graphs & FastMCP
          </span>
        </h1>

        <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-3xl">
          Cornerstone Realty Group integrates deterministic LangGraph state machines, multi-architecture RAG,
          cognitive memory consolidation, and Human-in-the-Loop governance with standard Model Context Protocol
          (MCP) endpoints and PGVector embeddings.
        </p>

        <div className="flex flex-wrap gap-3.5 pt-3">
          <button
            onClick={() => setCurrentPage('chat')}
            className="px-6 py-3 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <Bot className="w-4 h-4" />
            <span>Launch Autonomous Assistant</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>

          <button
            onClick={() => setCurrentPage('showcase')}
            className="px-6 py-3 rounded-xl text-xs sm:text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <Workflow className="w-4 h-4" />
            <span>Planning & Benchmarks Showcase</span>
          </button>

          <button
            onClick={() => setCurrentPage('status')}
            className="px-5 py-3 rounded-xl text-xs sm:text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-2 transition-all"
          >
            <Radio className="w-4 h-4 text-cyan-400" />
            <span>Protocol Status & Workbench</span>
          </button>
        </div>
      </div>
    </section>
  );
};
