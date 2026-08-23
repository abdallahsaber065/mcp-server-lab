import React from 'react';

export const MetricTickers: React.FC = () => {
  return (
    <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">104</div>
        <div className="text-[11px] text-slate-400 font-medium">Pytest Tests Passing</div>
      </div>
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400 font-mono">5</div>
        <div className="text-[11px] text-slate-400 font-medium">Planning Algorithms</div>
      </div>
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-cyan-400 font-mono">5</div>
        <div className="text-[11px] text-slate-400 font-medium">RAG Architectures</div>
      </div>
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-purple-400 font-mono">8</div>
        <div className="text-[11px] text-slate-400 font-medium">MCP Protocol Concerns</div>
      </div>
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 font-mono">4</div>
        <div className="text-[11px] text-slate-400 font-medium">Memory Subsystems</div>
      </div>
      <div className="glass-card p-4 text-center space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-rose-400 font-mono">3</div>
        <div className="text-[11px] text-slate-400 font-medium">Active Contributors</div>
      </div>
    </section>
  );
};
