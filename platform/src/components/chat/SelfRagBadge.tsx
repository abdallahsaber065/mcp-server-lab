import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, BookOpen, CheckCircle2, AlertTriangle } from 'lucide-react';

export interface SelfRagPayload {
  strategy?: string;
  is_relevant?: boolean | string;
  is_supported?: boolean | string;
  score?: number;
  citations?: string[];
  preview?: string;
}

interface SelfRagBadgeProps {
  selfRag: SelfRagPayload;
}

export const SelfRagBadge: React.FC<SelfRagBadgeProps> = ({ selfRag }) => {
  const [isOpen, setIsOpen] = useState(false);

  const isSupported =
    selfRag.is_supported === true ||
    selfRag.is_supported === 'fully_supported' ||
    selfRag.is_supported === 'supported';

  const isRelevant =
    selfRag.is_relevant === true ||
    selfRag.is_relevant === 'relevant';

  const citations = selfRag.citations || [];

  return (
    <div
      className={`rounded-xl border overflow-hidden text-xs transition-all ${
        isSupported
          ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
          : 'bg-amber-950/20 border-amber-500/30 text-amber-300'
      }`}
    >
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors select-none font-mono text-[11px]"
      >
        <div className="flex items-center space-x-2 truncate">
          {isSupported ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          )}
          <span className="font-bold text-slate-200 truncate">
            Self-RAG Verified: Grounded in Policy ({selfRag.strategy ? selfRag.strategy.toUpperCase() : 'PGVECTOR'})
          </span>
          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            [IsRel: {String(isRelevant)}]
          </span>
          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            [IsSup: {String(isSupported)}]
          </span>
          {selfRag.score !== undefined && (
            <span className="text-[10px] text-slate-400">({(selfRag.score * 100).toFixed(0)}%)</span>
          )}
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 shrink-0 ml-2 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </div>

      {isOpen && (
        <div className="p-3 bg-slate-950/90 border-t border-white/10 space-y-2.5 text-[11px] font-mono">
          {citations.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                <BookOpen className="w-3 h-3 text-cyan-400" />
                <span>Retrieved Grounding Citations</span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {citations.map((c, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 text-[10px]"
                  >
                    📄 {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {selfRag.preview && (
            <div className="space-y-1 pt-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Grounded Knowledge Snippet:
              </div>
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-[10px] line-clamp-3">
                {selfRag.preview}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
