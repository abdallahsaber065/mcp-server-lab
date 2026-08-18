import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { RichContent } from '../common/RichContent';

interface SubtaskItem {
  instruction: string;
  method: string;
  output: string;
  status?: string;
}

interface SubtaskCardProps {
  subtask: SubtaskItem;
}

export const SubtaskCard: React.FC<SubtaskCardProps> = ({ subtask }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const getMethodBadge = (m: string) => {
    switch (m) {
      case 'ToT':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'LATS':
        return 'bg-pink-500/20 text-pink-300 border-pink-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="rounded-xl bg-slate-950/70 border border-indigo-500/20 overflow-hidden text-xs transition-all">
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-900/60 transition-colors select-none"
      >
        <div className="flex items-center space-x-2 truncate">
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${getMethodBadge(
              subtask.method
            )}`}
          >
            {subtask.method} ROUTED
          </span>
          <span className="font-semibold text-slate-200 truncate">{subtask.instruction}</span>
        </div>
        <div className="flex items-center space-x-1.5 text-slate-500 shrink-0 ml-2">
          <span className="text-[10px]">Sub-Task</span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
          />
        </div>
      </div>
      {isExpanded && subtask.output && (
        <div className="p-3.5 bg-slate-950/90 border-t border-slate-800/80 text-slate-300">
          <RichContent content={subtask.output} />
        </div>
      )}
    </div>
  );
};
