import React from 'react';
import {
  Award,
  CheckCircle2,
  Layers,
  Wrench,
  Database,
  Cpu,
  Users,
} from 'lucide-react';
import { Card } from '../common/Card';

function BrainCircuitIcon(props: any) {
  return (
    <svg
      {...props}
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
      <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
      <path d="M12 18v4" />
      <path d="M8 22h8" />
    </svg>
  );
}

export const HeroStats: React.FC = () => {
  const stats = [
    {
      label: 'Target Grade',
      value: '105/100',
      sub: '100 Fixed + 5 Bonus',
      icon: Award,
      color: 'text-amber-400',
      bgGlow: 'from-amber-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-amber-500/30 hover:border-amber-400/60',
    },
    {
      label: 'Automated Tests',
      value: '97 / 97',
      sub: '100% Clean Pass',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgGlow: 'from-emerald-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-emerald-500/30 hover:border-emerald-400/60',
    },
    {
      label: 'Core Subsystems',
      value: '22 Modules',
      sub: 'Across Weeks 2, 3, 4',
      icon: Layers,
      color: 'text-indigo-400',
      bgGlow: 'from-indigo-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-indigo-500/30 hover:border-indigo-400/60',
    },
    {
      label: 'MCP Tools',
      value: '14 Active',
      sub: 'Dynamic listChanged',
      icon: Wrench,
      color: 'text-cyan-400',
      bgGlow: 'from-cyan-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-cyan-500/30 hover:border-cyan-400/60',
    },
    {
      label: 'RAG Strategies',
      value: '4 Engines',
      sub: 'Naive, Hybrid, Agentic, Graph',
      icon: Database,
      color: 'text-blue-400',
      bgGlow: 'from-blue-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-blue-500/30 hover:border-blue-400/60',
    },
    {
      label: 'Memory Stores',
      value: '3 Layers',
      sub: 'STM, Episodic, Semantic',
      icon: BrainCircuitIcon,
      color: 'text-purple-400',
      bgGlow: 'from-purple-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-purple-500/30 hover:border-purple-400/60',
    },
    {
      label: 'Planning Solvers',
      value: '4 Models',
      sub: 'PS, ToT, LATS, Reflexion',
      icon: Cpu,
      color: 'text-rose-400',
      bgGlow: 'from-rose-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-rose-500/30 hover:border-rose-400/60',
    },
    {
      label: 'Team Contributed',
      value: '3 Leads',
      sub: 'Cornerstone Realty Lab',
      icon: Users,
      color: 'text-teal-400',
      bgGlow: 'from-teal-500/10 via-slate-900/80 to-slate-950/90',
      borderColor: 'border-teal-500/30 hover:border-teal-400/60',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <div
            key={idx}
            className={`p-5 sm:p-6 rounded-2xl bg-gradient-to-b ${stat.bgGlow} border ${stat.borderColor} backdrop-blur-xl shadow-lg transition-all duration-200 hover:-translate-y-1 hover:shadow-2xl flex flex-col justify-between space-y-3`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold uppercase tracking-wider text-[10px] text-slate-400">{stat.label}</span>
              <div className={`p-1.5 rounded-lg bg-slate-950/60 border border-slate-800 ${stat.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className={`text-2xl sm:text-3xl font-black ${stat.color} font-mono tracking-tight`}>
                {stat.value}
              </div>
              <div className="text-xs text-slate-400 font-medium truncate">{stat.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default HeroStats;
