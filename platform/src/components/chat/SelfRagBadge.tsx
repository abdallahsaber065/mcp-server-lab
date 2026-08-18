import React from 'react';
import { CheckCircle2 } from 'lucide-react';

interface SelfRagPayload {
  is_relevant?: boolean;
  is_supported?: boolean;
  score?: number;
  citations?: string[];
}

interface SelfRagBadgeProps {
  selfRag: SelfRagPayload;
}

export const SelfRagBadge: React.FC<SelfRagBadgeProps> = ({ selfRag }) => {
  return (
    <div className="flex items-center space-x-2 p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-[10px] font-mono text-emerald-400">
      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
      <span>
        Self-RAG Grounded: [IsRel: {String(selfRag.is_relevant ?? true)}] · [IsSup:{' '}
        {String(selfRag.is_supported ?? true)}]
      </span>
      {selfRag.score !== undefined && (
        <span className="text-slate-400">({(selfRag.score * 100).toFixed(0)}% confidence)</span>
      )}
    </div>
  );
};
