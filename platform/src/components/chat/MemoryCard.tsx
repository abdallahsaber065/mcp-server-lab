import React, { useState } from 'react';
import { Database, Sparkles, ChevronDown, Clock, ShieldCheck } from 'lucide-react';

export interface SemanticFactItem {
  fact_id?: number;
  fact_key?: string;
  category?: string;
  fact_value?: string;
  value?: string;
  version?: number;
}

export interface EpisodicItem {
  episode_id?: number;
  event_summary?: string;
  summary?: string;
  timestamp?: string;
}

export interface MemoryContextData {
  type?: string;
  persona_name?: string;
  fact?: string;
  action?: string;
  active_facts?: SemanticFactItem[];
  recent_episodes?: EpisodicItem[];
}

interface MemoryCardProps {
  memory: MemoryContextData;
}

export const MemoryCard: React.FC<MemoryCardProps> = ({ memory }) => {
  const [isOpen, setIsOpen] = useState(true);

  const facts = memory.active_facts || [];
  const episodes = memory.recent_episodes || [];

  // Single fact fallback if passed from streaming token
  const hasMultiple = facts.length > 0 || episodes.length > 0;

  return (
    <div className="rounded-xl bg-purple-950/20 border border-purple-500/30 overflow-hidden text-xs transition-all shadow-lg">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-3 flex items-center justify-between cursor-pointer hover:bg-purple-900/20 transition-colors select-none"
      >
        <div className="flex items-center space-x-2 truncate">
          <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          <span className="font-bold text-purple-200 truncate">
            Active Memory Context {memory.persona_name ? `— ${memory.persona_name}` : ''}
          </span>
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {hasMultiple ? `${facts.length} Facts • ${episodes.length} Episodes` : 'Consolidated Fact'}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-purple-400 transition-transform duration-200 shrink-0 ml-2 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </div>

      {isOpen && (
        <div className="p-3.5 bg-slate-950/80 border-t border-purple-500/20 space-y-3 font-mono text-[11px]">
          {/* Active Semantic Facts */}
          {facts.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-purple-400 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Consolidated Semantic Facts (Long-Term Memory)</span>
              </div>
              <div className="space-y-1">
                {facts.map((f, i) => (
                  <div
                    key={i}
                    className="p-2 rounded-lg bg-slate-900/90 border border-slate-800 flex items-baseline justify-between gap-2"
                  >
                    <div className="flex items-baseline space-x-2">
                      <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        [{(f.category || f.fact_key || 'FACT').toUpperCase()}]
                      </span>
                      <span className="text-slate-200">{f.fact_value || f.value}</span>
                    </div>
                    <span className="text-[9px] text-slate-500 shrink-0">v{f.version || 1}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Episodic Memories */}
          {episodes.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>Recent Episodic Store Events</span>
              </div>
              <div className="space-y-1">
                {episodes.map((e, i) => (
                  <div
                    key={i}
                    className="p-2 rounded-lg bg-slate-900/90 border border-slate-800 flex items-baseline justify-between gap-2"
                  >
                    <span className="text-slate-300">{e.event_summary || e.summary}</span>
                    <span className="text-[9px] text-cyan-400/80 font-mono shrink-0">
                      {e.timestamp ? e.timestamp.slice(0, 10) : 'Recent'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fallback Single Fact */}
          {!hasMultiple && memory.fact && (
            <div className="text-slate-300">
              <strong className="text-purple-300">Consolidated Fact:</strong> {memory.fact}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
