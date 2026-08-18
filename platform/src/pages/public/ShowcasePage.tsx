/**
 * Showcase & Architectural Benchmarks Page (platform/src/pages/public/ShowcasePage.tsx)
 * Assembled from modular components in components/showcase/
 */

import React from 'react';
import { Sparkles } from 'lucide-react';
import { HeroStats } from '../../components/showcase/HeroStats';
import { EvolutionTimeline } from '../../components/showcase/EvolutionTimeline';
import { PlanningBenchmarks } from '../../components/showcase/PlanningBenchmarks';
import { RagBenchmarks } from '../../components/showcase/RagBenchmarks';
import { ContextBenchmarks } from '../../components/showcase/ContextBenchmarks';
import { SubsystemsGrid } from '../../components/showcase/SubsystemsGrid';
import { TeamSection } from '../../components/showcase/TeamSection';

export const ShowcasePage: React.FC = () => {
  return (
    <div className="space-y-10 pb-20 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Hero Header */}
      <div className="space-y-3 pt-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Week 2 + Week 3 + Week 4 Master Architectural Showcase</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
          Cornerstone Realty Autonomous AI System
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-4xl leading-relaxed">
          Production-grade FastMCP server, multi-architecture RAG, 3-tier memory consolidation, DAG task decomposition,
          and Monte Carlo Tree Search (LATS) planning engine benchmarked across enterprise property management workflows.
        </p>
      </div>

      <HeroStats />
      <EvolutionTimeline />
      <PlanningBenchmarks />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RagBenchmarks />
        <ContextBenchmarks />
      </div>

      <SubsystemsGrid />
      <TeamSection />
    </div>
  );
};

export default ShowcasePage;
