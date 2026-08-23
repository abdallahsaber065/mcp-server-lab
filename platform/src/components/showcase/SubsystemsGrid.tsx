import React, { useState } from 'react';
import {
  Layers,
  Cpu,
  Shield,
  GitBranch,
  Sliders,
  Zap,
  Activity,
  UserCheck,
  Clock,
  Lock,
  Database,
  ExternalLink,
} from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';
import { useAppStore } from '../../stores/useAppStore';

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

export const SubsystemsGrid: React.FC = () => {
  const { addToast } = useAppStore();
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const featuresList = [
    // Planning (Week 4)
    {
      cat: 'planning',
      icon: Cpu,
      title: 'Dynamic DAG Task Planner',
      desc: 'Interleaved execution dynamically reshaping topological plan on intermediate observation failure with cycle prevention.',
      color: 'border-indigo-500/30 text-indigo-400',
      file: 'planning/dynamic_decomposition.py',
    },
    {
      cat: 'planning',
      icon: Shield,
      title: 'MCTS Search Engine (LATS)',
      desc: 'Monte Carlo Tree Search with UCT selection, node expansion, grounded DB environmental simulation & backpropagation.',
      color: 'border-pink-500/30 text-pink-400',
      file: 'planning/lats.py',
    },
    {
      cat: 'planning',
      icon: GitBranch,
      title: 'Tree of Thoughts (ToT)',
      desc: 'Beam Search over candidate reasoning states for multi-vendor comparison and emergency contractor ranking.',
      color: 'border-purple-500/30 text-purple-400',
      file: 'planning/tree_of_thoughts.py',
    },
    {
      cat: 'planning',
      icon: Sliders,
      title: 'Self-Refine & Reflexion',
      desc: 'Iterative verbal critique and reflective episodic memory buffers for autonomous self-correction without humans.',
      color: 'border-emerald-500/30 text-emerald-400',
      file: 'planning/self_refine.py',
    },
    {
      cat: 'planning',
      icon: Zap,
      title: 'Mistral 7B Sub-Task Router',
      desc: 'Structured LLM micro-router routing dynamic tasks to PS, ToT, or LATS with deterministic JSON schema validation.',
      color: 'border-cyan-500/30 text-cyan-400',
      file: 'agent/planning_agent.py',
    },

    // Protocol (Week 2)
    {
      cat: 'protocol',
      icon: Shield,
      title: 'Capability Negotiation',
      desc: 'Server declares elicitation, tools/listChanged, sampling, resources, and progress support during handshake.',
      color: 'border-indigo-500/30 text-indigo-400',
      file: 'mcp_server/server.py',
    },
    {
      cat: 'protocol',
      icon: Activity,
      title: 'Live Push Notifications',
      desc: 'Server pushes notifications/tools/list_changed when user role changes, updating client toolsets in real time.',
      color: 'border-blue-500/30 text-blue-400',
      file: 'mcp_server/notifications.py',
    },
    {
      cat: 'protocol',
      icon: UserCheck,
      title: 'Human-in-the-Loop Elicitation',
      desc: 'High-risk lease modifications trigger elicitation/create mid-call, pausing execution for manager approval.',
      color: 'border-rose-500/30 text-rose-400',
      file: 'mcp_server/server.py',
    },
    {
      cat: 'protocol',
      icon: Clock,
      title: 'Progress Tracking',
      desc: 'Batch property compliance audits report step-by-step percentage progress via progressToken.',
      color: 'border-amber-500/30 text-amber-400',
      file: 'mcp_server/progress.py',
    },
    {
      cat: 'protocol',
      icon: Lock,
      title: 'Defensive Pydantic Schemas',
      desc: 'Strict Pydantic models with extra="forbid", parameter bounds validation, and server-side RBAC authorization.',
      color: 'border-purple-500/30 text-purple-400',
      file: 'mcp_server/server.py',
    },

    // RAG & Memory (Week 3)
    {
      cat: 'rag_memory',
      icon: Database,
      title: 'Multi-Architecture RAG',
      desc: 'Naive, Hybrid (BM25+RRF with statute bonuses), Agentic multi-hop, and Graph RAG over realty knowledge bases.',
      color: 'border-cyan-500/30 text-cyan-400',
      file: 'rag/architectures.py',
    },
    {
      cat: 'rag_memory',
      icon: BrainCircuitIcon,
      title: 'Semantic Memory Consolidation',
      desc: 'STM buffer, episodic store, and semantic consolidation engine with real contradiction resolution.',
      color: 'border-emerald-500/30 text-emerald-400',
      file: 'memory/consolidation.py',
    },

    // LLM & UI
    {
      cat: 'llm_ui',
      icon: Cpu,
      title: 'Provider-Agnostic LLM Engine',
      desc: '10+ models via LiteLLM — Gemini 2.5 Pro, Llama 3.3 70B, Mistral Small, Gemma with streaming.',
      color: 'border-blue-500/30 text-blue-400',
      file: 'web/llm_engine.py',
    },
    {
      cat: 'llm_ui',
      icon: Layers,
      title: 'Interactive Web Portal',
      desc: 'Dark-mode glassmorphism UI with real-time SSE streaming, Intent badges, stop controls, and PostgreSQL persistence.',
      color: 'border-indigo-500/30 text-indigo-400',
      file: 'platform/src/',
    },
  ];

  const filteredFeatures =
    activeCategory === 'all'
      ? featuresList
      : featuresList.filter((f) => f.cat === activeCategory);

  const filterTabs = [
    { id: 'all', label: 'All (14)' },
    { id: 'planning', label: 'Planning (Week 4)' },
    { id: 'protocol', label: 'Protocol (Week 2)' },
    { id: 'rag_memory', label: 'RAG & Memory (Week 3)' },
    { id: 'llm_ui', label: 'LLM & UI' },
  ];

  return (
    <Card className="p-6 sm:p-8 space-y-6">
      <SectionHeader
        icon={Layers}
        title="System Features & Subsystems"
        subtitle="22 production-grade subsystems across Weeks 2, 3, and 4"
        iconColor="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
        action={
          <div className="flex flex-wrap gap-1.5 p-1 rounded-xl bg-slate-950/60 border border-slate-800">
            {filterTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveCategory(tab.id)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  activeCategory === tab.id
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFeatures.map((f, i) => {
          const Icon = f.icon;
          return (
            <div
              key={i}
              onClick={() => addToast(`Inspecting: ${f.title} (${f.file})`, 'info')}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/40 transition-all hover:translate-y-[-2px] space-y-3 cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-xl bg-slate-950 border ${f.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-mono text-slate-500 group-hover:text-indigo-400 transition-colors">
                  {f.file.split('/')[0]}
                </span>
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-200 group-hover:text-white transition-colors">
                  {f.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{f.desc}</p>
              </div>
              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                <span>{f.file}</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-indigo-400" />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
