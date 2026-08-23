import React from 'react';

interface IntentBadgeProps {
  intent: {
    type: string;
    rationale: string;
  };
}

export const IntentBadge: React.FC<IntentBadgeProps> = ({ intent }) => {
  const isPlanning = intent.type === 'PLANNING';

  return (
    <div
      className={`flex items-center space-x-2.5 p-2.5 rounded-xl border text-xs ${
        isPlanning
          ? 'bg-purple-500/10 border-purple-500/30 text-purple-200'
          : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-200'
      }`}
    >
      <span
        className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono text-white ${
          isPlanning ? 'bg-purple-600' : 'bg-indigo-600'
        }`}
      >
        {isPlanning ? '🧩 PLANNING' : `⚡ ${intent.type}`}
      </span>
      <span className="text-[11px] text-slate-300 truncate">
        <strong className="text-slate-100">Intent Router:</strong> {intent.rationale}
      </span>
    </div>
  );
};
