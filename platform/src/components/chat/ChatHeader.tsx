import React from 'react';
import { MessageSquare, Cpu, Database, Shield, GitBranch } from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';

export type ChatMode = 'standard' | 'lease_onboarding' | 'maintenance_tender' | 'arrears_mediation';

export const CHAT_MODE_META: Record<ChatMode, { label: string; shortLabel: string; graphId?: string }> = {
  standard: { label: 'Normal Chat', shortLabel: 'Normal' },
  lease_onboarding: { label: 'Lease Onboarding', shortLabel: 'Lease', graphId: 'commercial_lease_flow' },
  maintenance_tender: { label: 'Maintenance Tender', shortLabel: 'Maintenance', graphId: 'renovation_permit_flow' },
  arrears_mediation: { label: 'Arrears Mediation', shortLabel: 'Arrears', graphId: 'rent_arrears_settlement_flow' },
};

interface ChatHeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  selectedModel: string;
  onChangeModel: (model: string) => void;
  selectedRag: string;
  onChangeRag: (rag: any) => void;
  selectedMode: ChatMode;
  onChangeMode: (mode: ChatMode) => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  selectedModel,
  onChangeModel,
  selectedRag,
  onChangeRag,
  selectedMode,
  onChangeMode,
}) => {
  const { user, role } = useAuthStore();
  const effectiveRole = user?.role || role || 'prospect';
  const isGraphMode = selectedMode !== 'standard';

  const getRoleBadge = () => {
    switch (effectiveRole) {
      case 'executive_admin':
        return { label: 'Executive Admin', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' };
      case 'property_manager':
        return { label: 'Property Manager', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' };
      case 'tenant':
        return { label: 'Resident Tenant', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' };
      default:
        return { label: 'Guest / Prospect', color: 'bg-slate-800 text-slate-300 border-slate-700' };
    }
  };

  const badge = getRoleBadge();

  return (
    <div className="h-14 border-b border-slate-800/80 px-4 flex items-center justify-between bg-slate-900/70 backdrop-blur-md shrink-0 select-none gap-2">
      <div className="flex items-center space-x-3 shrink-0">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          title="Toggle Sessions Sidebar"
        >
          <MessageSquare className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isGraphMode ? 'bg-violet-500 animate-pulse' : 'bg-emerald-400 animate-pulse'}`} />
          <span className="text-xs font-bold text-slate-200 hidden lg:inline">Cornerstone Studio</span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badge.color} flex items-center space-x-1`}
            title={user?.email ? `Authenticated as ${user.email}` : 'Unauthenticated Guest'}
          >
            <Shield className="w-2.5 h-2.5" />
            <span>{badge.label}</span>
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-2 overflow-x-auto">
        {/* Chat Mode Selector — 4 options */}
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-xl border text-xs ${isGraphMode ? 'bg-violet-950/40 border-violet-500/40 text-violet-200' : 'bg-slate-950/80 border-slate-800 text-slate-300'}`}>
          <GitBranch className={`w-3.5 h-3.5 shrink-0 ${isGraphMode ? 'text-violet-400' : 'text-slate-500'}`} />
          <select
            value={selectedMode}
            onChange={(e) => onChangeMode(e.target.value as ChatMode)}
            className="bg-transparent text-xs font-semibold focus:outline-none cursor-pointer"
            title="Chat mode — Standard or 3 Final-Project graph agents (background, persistent)"
          >
            <option value="standard" className="bg-slate-900">Standard — Normal Chat</option>
            <option value="lease_onboarding" className="bg-slate-900">Lease Onboarding — Suite-301 (Vision)</option>
            <option value="maintenance_tender" className="bg-slate-900">Maintenance Tender — Zamalek (LATS)</option>
            <option value="arrears_mediation" className="bg-slate-900">Arrears Mediation — ToT (Counsel)</option>
          </select>
        </div>

        {/* Model Selector — always enabled, but hint when graph mode */}
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-xl border text-xs ${isGraphMode ? 'bg-slate-900/60 border-slate-700/60 text-slate-400' : 'bg-slate-950/80 border-slate-800 text-slate-300'}`} title={isGraphMode ? 'Model still used for intake interview; graph uses its own LLM additions' : undefined}>
          <Cpu className={`w-3.5 h-3.5 shrink-0 ${isGraphMode ? 'text-slate-500' : 'text-indigo-400'}`} />
          <select
            value={selectedModel}
            onChange={(e) => onChangeModel(e.target.value)}
            className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer disabled:opacity-50"
          >
            <option value="gemini/gemini-3.1-flash-lite" className="bg-slate-900">Gemini 3.1 Flash-Lite (Default)</option>
            <option value="gemini/gemini-3.5-flash" className="bg-slate-900">Gemini 3.5 Flash</option>
            <option value="gemini/gemini-2.5-flash" className="bg-slate-900">Gemini 2.5 Flash</option>
            <option value="gemini/gemini-2.5-flash-lite" className="bg-slate-900">Gemini 2.5 Flash-Lite</option>
            <option value="gemini/gemma-4-26b-a4b-it" className="bg-slate-900">Gemma 4 26B A4B IT</option>
            <option value="mistral/mistral-small-latest" className="bg-slate-900">Mistral Small Latest</option>
            <option value="mistral/open-mistral-7b" className="bg-slate-900">Open Mistral 7B</option>
            <option value="mistral/open-mixtral-8x7b" className="bg-slate-900">Open Mixtral 8x7B</option>
            <option value="mistral/codestral-latest" className="bg-slate-900">CodeStral Latest</option>
            <option value="mistral/mistral-large-latest" className="bg-slate-900">Mistral Large Latest</option>
          </select>
        </div>

        {/* RAG Selector — disabled in graph mode */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-xl border text-xs transition-all ${isGraphMode ? 'bg-slate-900/40 border-slate-800/50 text-slate-500 opacity-60 cursor-not-allowed' : 'bg-slate-950/80 border-slate-800 text-slate-300'}`}
          title={isGraphMode ? 'RAG is managed by the graph agent (RAG/LATS/ToT inside nodes) — disabled in graph mode' : 'RAG strategy for Standard chat'}
        >
          <Database className={`w-3.5 h-3.5 shrink-0 ${isGraphMode ? 'text-slate-600' : 'text-cyan-400'}`} />
          <select
            value={selectedRag}
            onChange={(e) => onChangeRag(e.target.value)}
            disabled={isGraphMode}
            className="bg-transparent text-xs focus:outline-none cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
          >
            <option value="pgvector" className="bg-slate-900">PGVector (HNSW)</option>
            <option value="agentic" className="bg-slate-900">Agentic (Multi-Hop)</option>
            <option value="hybrid" className="bg-slate-900">Hybrid (BM25+RRF)</option>
            <option value="naive" className="bg-slate-900">Naive RAG</option>
            <option value="graph" className="bg-slate-900">Graph (Entities)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
