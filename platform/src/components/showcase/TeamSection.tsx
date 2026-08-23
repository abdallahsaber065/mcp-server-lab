import React from 'react';
import { Users } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';

export const TeamSection: React.FC = () => {
  const teamMembers = [
    {
      name: 'Abdallah Saber',
      role: 'Team Lead & RAG / Planning Architect',
      initials: 'AS',
      accent: 'from-indigo-600 to-cyan-500',
      contributions: [
        'DAG Task Decomposition Engine & Dynamic Interleaved Execution (#18)',
        'Planning Agent Architecture, MCP Loop & Master Benchmarks (#23)',
        'FastMCP Server Core & 8 Protocol Concerns (Week 2)',
        'Multi-Architecture RAG (Naive, Hybrid, Agentic, Graph) (Week 3)',
        'Enterprise React Platform, SSE Chat Streaming & Full DB Persistence',
      ],
    },
    {
      name: 'Nour Salem',
      role: 'Planning Algorithms & Memory Lead',
      initials: 'NS',
      accent: 'from-purple-600 to-pink-500',
      contributions: [
        'Plan-and-Solve (PS) & Tree of Thoughts (ToT Beam Search) (#19)',
        'Monte Carlo Tree Search (LATS / MCTS Grounded Engine) (#20)',
        'Short-Term Memory Buffer & Decoupled Scratchpad (Week 3)',
        'Episodic Memory Store & Semantic Consolidation Engine (Week 3)',
        'Contradiction Resolution & Memory Router (Week 3)',
      ],
    },
    {
      name: 'Ahmed Wael',
      role: 'Self-Correction, Protocol & Eval Lead',
      initials: 'AW',
      accent: 'from-emerald-600 to-teal-500',
      contributions: [
        'Self-Refine, Reflexion & Grounded Environment Feedback (#21)',
        'Planning Evaluation Benchmark Suite & Empirical Comparison (#22)',
        'MCP Client Agent, Role Notifications & Progress Tracking (Week 2)',
        '4 Context Window Pruning Strategies & 40-Turn Test Suite (Week 3)',
        'Self-RAG Verification ([IsRel], [IsSup]) & Retrieval Eval (Week 3)',
      ],
    },
  ];

  return (
    <Card className="p-6 sm:p-8 space-y-6">
      <SectionHeader
        icon={Users}
        title="Team & Modular Ownership"
        subtitle="Cornerstone Realty Group B — 3 contributors, 22 subsystems across Weeks 2, 3, and 4"
        iconColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {teamMembers.map((m, idx) => (
          <div
            key={idx}
            className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4 hover:border-indigo-500/30 transition-all"
          >
            <div className="flex items-center space-x-3">
              <div
                className={`w-12 h-12 rounded-2xl bg-gradient-to-tr ${m.accent} flex items-center justify-center font-black text-white text-base shadow-lg`}
              >
                {m.initials}
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">{m.name}</h3>
                <p className="text-xs text-indigo-400 font-medium">{m.role}</p>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <div className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">Owned Subsystems</div>
              <ul className="space-y-1.5 text-xs text-slate-400">
                {m.contributions.map((c, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-indigo-400 mt-0.5">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
