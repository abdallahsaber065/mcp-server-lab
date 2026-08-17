/**
 * Modern Luxury Landing Page (platform/src/pages/public/LandingPage.tsx)
 */

import React from 'react';
import {
  Building2,
  Sparkles,
  ShieldCheck,
  Zap,
  ArrowRight,
  BarChart3,
  GitBranch,
  Bot,
  Database,
  Lock,
} from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { useAuthStore } from '../../stores/useAuthStore';

export const LandingPage: React.FC = () => {
  const { setCurrentPage } = useAppStore();
  const { quickLoginAs } = useAuthStore();

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-indigo-950/40 via-slate-900/60 to-slate-950/80 border border-slate-800 p-8 sm:p-12">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Autonomous Multi-Agent Real Estate Operations Platform</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Next-Generation Property Management Driven by{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400">
              State Graphs & MCP
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            Cornerstone Realty Group pairs state-of-the-art LangGraph-style state machines,
            multi-architecture RAG, and Human-in-the-Loop governance with standard Model Context
            Protocol (MCP) server endpoints.
          </p>

          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => setCurrentPage('properties')}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition-all"
            >
              <span>Explore Available Units</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage('showcase')}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-2 transition-all"
            >
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <span>View Empirical Benchmarks</span>
            </button>
          </div>
        </div>
      </section>

      {/* Highlights Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card-hover p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100">Cyclic State Graphs</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Deterministic state machines with checkpointing, cyclical error-recovery, and Human-in-the-Loop pause/resume hooks for commercial leasing and renovations.
          </p>
        </div>

        <div className="glass-card-hover p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Database className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100">Clean Architecture & Concurrency</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            SQLAlchemy 2.0 ORM, SQLite WAL mode, async Redis cache, and full PostgreSQL migration readiness with zero raw SQL queries.
          </p>
        </div>

        <div className="glass-card-hover p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100">Executive Governance & HITL</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Discount sign-off workflows, dynamic tool matrix with real-time MCP notifications, and failure ticket self-healing workbenches.
          </p>
        </div>
      </section>

      {/* Quick Access Card for Evaluators */}
      <section className="glass-card p-6 sm:p-8 space-y-4 border-indigo-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">Interactive Evaluator Quick-Start</h2>
            <p className="text-xs text-slate-400">Select a pre-seeded persona to explore role-tailored dashboards instantly:</p>
          </div>
          <Lock className="w-5 h-5 text-indigo-400" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <button
            onClick={() => {
              quickLoginAs('executive_admin');
              setCurrentPage('dashboard');
            }}
            className="p-4 rounded-xl bg-rose-950/30 hover:bg-rose-900/40 border border-rose-500/30 text-left transition-all group"
          >
            <div className="font-bold text-xs text-rose-300 group-hover:text-rose-200">1. Executive Admin</div>
            <div className="text-[11px] text-slate-400 mt-1">Review HITL discount queue, toggle tool matrix, inspect failure tickets.</div>
          </button>

          <button
            onClick={() => {
              quickLoginAs('property_manager');
              setCurrentPage('dashboard');
            }}
            className="p-4 rounded-xl bg-indigo-950/30 hover:bg-indigo-900/40 border border-indigo-500/30 text-left transition-all group"
          >
            <div className="font-bold text-xs text-indigo-300 group-hover:text-indigo-200">2. Property Manager</div>
            <div className="text-[11px] text-slate-400 mt-1">Execute state graphs, review commercial leases, dispatch maintenance contractors.</div>
          </button>

          <button
            onClick={() => {
              quickLoginAs('tenant');
              setCurrentPage('dashboard');
            }}
            className="p-4 rounded-xl bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/30 text-left transition-all group"
          >
            <div className="font-bold text-xs text-emerald-300 group-hover:text-emerald-200">3. Registered Tenant</div>
            <div className="text-[11px] text-slate-400 mt-1">View active lease, check payment status, submit emergency repair requests.</div>
          </button>
        </div>
      </section>
    </div>
  );
};
