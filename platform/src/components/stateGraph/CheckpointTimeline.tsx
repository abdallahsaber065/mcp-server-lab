import { Clock, RotateCcw, Eye } from 'lucide-react';

export function CheckpointTimeline({ checkpoints, currentStep, onSelect, onDiff, onRollback }: { checkpoints: any[]; currentStep?: number; onSelect: (step: number) => void; onDiff?: (a: number, b: number) => void; onRollback: (step: number) => void }) {
  if (!checkpoints || checkpoints.length === 0) {
    return <div className="text-xs text-slate-400 p-4 border border-dashed border-slate-800 rounded-xl">No checkpoints yet — run a graph.</div>;
  }
  return (
    <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
      {checkpoints.map((cp: any, idx: number) => {
        const step = cp.step ?? cp.step_number ?? idx + 1;
        const isCurrent = step === currentStep;
        return (
          <div key={cp.checkpoint_id || step} className={`p-3 rounded-xl border flex flex-col gap-2 ${isCurrent ? 'bg-indigo-950/40 border-indigo-500/50 shadow shadow-indigo-500/20' : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'}`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Step {step}: {cp.node || cp.node_name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${String(cp.status).includes('COMPLETED') ? 'bg-emerald-500/20 text-emerald-300' : String(cp.status).includes('PAUSED') ? 'bg-amber-500/20 text-amber-300' : String(cp.status).includes('WAIT') ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>{cp.status}</span>
            </div>
            <div className="text-[10px] text-slate-500 flex items-center gap-1"><Clock className="w-3 h-3" />{cp.created_at || 'just now'}</div>
            <div className="flex gap-2">
              <button onClick={() => onSelect(step)} className="flex-1 text-[11px] px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center justify-center gap-1"><Eye className="w-3 h-3" />Inspect</button>
              <button onClick={() => onRollback(step)} className="flex-1 text-[11px] px-2 py-1 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/30 flex items-center justify-center gap-1"><RotateCcw className="w-3 h-3" />Rollback</button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
