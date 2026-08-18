import React from 'react';
import { Database, Sparkles, CheckCircle2 } from 'lucide-react';

interface MemoryCardProps {
  memory: {
    type?: string;
    fact?: string;
    action?: string;
  };
}

export const MemoryCard: React.FC<MemoryCardProps> = ({ memory }) => {
  return (
    <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 space-y-1.5 text-xs font-mono">
      <div className="flex items-center space-x-2 text-purple-300 font-bold">
        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
        <span>Semantic Memory Consolidated</span>
      </div>
      <div className="text-[11px] text-slate-300">
        <strong className="text-purple-200">Consolidated Fact:</strong> {memory.fact || 'Updated tenant preference & operational knowledge in long-term store.'}
      </div>
    </div>
  );
};
