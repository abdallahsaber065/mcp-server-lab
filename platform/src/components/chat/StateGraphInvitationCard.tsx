import React from 'react';
import { GitBranch, ArrowRight, ExternalLink } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export interface StateGraphInvitation {
  graph_id: string;
  label: string;
  narrative: string;
  variables_prefill: Record<string, any>;
  deep_link: string;
}

export const StateGraphInvitationCard: React.FC<{ invitation: StateGraphInvitation }> = ({ invitation }) => {
  const { setCurrentPage } = useAppStore();
  const handleOpen = () => {
    window.history.pushState(null, '', invitation.deep_link);
    setCurrentPage('stateGraph' as any);
    // also dispatch popstate for App.tsx listener
    window.dispatchEvent(new PopStateEvent('popstate'));
  };
  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 to-slate-900/60 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
          <GitBranch className="w-4 h-4 text-indigo-400" />
        </div>
        <div>
          <div className="text-xs font-bold text-indigo-200">{invitation.label}</div>
          <div className="text-[11px] text-slate-400">State Graph workflow — live streaming & checkpoint time-travel</div>
        </div>
      </div>
      <div className="text-xs text-slate-300 bg-slate-950/50 rounded-xl p-3 border border-slate-800">{invitation.narrative}</div>
      <div className="flex gap-2">
        <button onClick={handleOpen} className="flex-1 text-xs px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center justify-center gap-1.5">
          <ExternalLink className="w-3.5 h-3.5" /> Open in State Graph Studio <ArrowRight className="w-3 h-3" />
        </button>
      </div>
      <div className="text-[10px] text-slate-500 font-mono">Graph: {invitation.graph_id} • Variables: {JSON.stringify(invitation.variables_prefill).slice(0, 80)}</div>
    </div>
  );
};
