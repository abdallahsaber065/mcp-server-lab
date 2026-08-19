import React from 'react';
import { Database, Play } from 'lucide-react';

interface MemoryPlaygroundProps {
  onRunTest: (testId: string) => Promise<void>;
  testOutputs: Record<string, any>;
}

export const MemoryPlayground: React.FC<MemoryPlaygroundProps> = ({ onRunTest, testOutputs }) => {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            <span>Cognitive Memory Subsystem (Week 3 Interactive Playground)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Explore short-term buffer pruning, decoupled scratchpad, promote-or-drop routing, and semantic conflict resolution.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* 1. STM Pruning & Scratchpad */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="text-xs font-bold text-emerald-300">STM Buffer & Scratchpad Preservation</div>
            <p className="text-xs text-slate-400">
              Rolling message buffer with FIFO turn-pruning that preserves active planning state in the decoupled scratchpad.
            </p>
          </div>
          <button
            onClick={() => onRunTest('stm')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-600 text-white flex items-center justify-center space-x-1.5 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Simulate STM Pruning</span>
          </button>
          {testOutputs.stm && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              <pre>{JSON.stringify(testOutputs.stm.data, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* 2. Promote-or-Drop Router */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="text-xs font-bold text-indigo-300">Promote-or-Drop Router</div>
            <p className="text-xs text-slate-400">
              Routes aging dialogue turns: drops conversational filler and promotes operational facts to the episodic store with logged rationale.
            </p>
          </div>
          <button
            onClick={() => onRunTest('route')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-indigo-700 hover:bg-indigo-600 text-white flex items-center justify-center space-x-1.5 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Test Allergy Routing Decision</span>
          </button>
          {testOutputs.route && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              <pre>{JSON.stringify(testOutputs.route.data, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* 3. Semantic Consolidation */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="text-xs font-bold text-amber-300">Semantic Consolidation & Contradiction Resolution</div>
            <p className="text-xs text-slate-400">
              Background pass over episodic history: updates entity facts and automatically resolves contradictions (e.g. Renewal vs Vacate).
            </p>
          </div>
          <button
            onClick={() => onRunTest('consolidate')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-amber-700 hover:bg-amber-600 text-white flex items-center justify-center space-x-1.5 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Trigger Fact Superseding Pass</span>
          </button>
          {testOutputs.consolidate && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              <pre>{JSON.stringify(testOutputs.consolidate.data, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
