import React from 'react';
import { Shield, Check, X } from 'lucide-react';

interface ElicitationPayload {
  prompt: string;
  lease_id?: number;
  proposed_rent?: number;
}

interface ElicitationCardProps {
  elicitation: ElicitationPayload;
  onRespond: (leaseId: number, proposedRent: number, approved: boolean) => void;
}

export const ElicitationCard: React.FC<ElicitationCardProps> = ({
  elicitation,
  onRespond,
}) => {
  const leaseId = elicitation.lease_id || 1;
  const proposedRent = elicitation.proposed_rent || 0;

  return (
    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3 shadow-lg shadow-amber-500/5">
      <div className="flex items-center space-x-2 text-xs font-bold text-amber-300">
        <Shield className="w-4 h-4 text-amber-400 shrink-0" />
        <span>Human-in-the-Loop Elicitation · Executive Approval Required</span>
      </div>
      <p className="text-xs text-slate-200 leading-relaxed">{elicitation.prompt}</p>
      <div className="flex items-center space-x-2 pt-1">
        <button
          onClick={() => onRespond(leaseId, proposedRent, true)}
          className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center space-x-1.5 transition-all shadow-md shadow-emerald-600/20"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Approve Override</span>
        </button>
        <button
          onClick={() => onRespond(leaseId, proposedRent, false)}
          className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white flex items-center space-x-1.5 transition-all"
        >
          <X className="w-3.5 h-3.5" />
          <span>Deny Request</span>
        </button>
      </div>
    </div>
  );
};
