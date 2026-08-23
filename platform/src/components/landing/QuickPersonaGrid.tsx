import React from 'react';
import { Lock } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { useAuthStore } from '../../stores/useAuthStore';

export const QuickPersonaGrid: React.FC = () => {
  const { setCurrentPage } = useAppStore();
  const { quickLoginAs } = useAuthStore();

  return (
    <section className="glass-card p-6 sm:p-8 space-y-4 border-indigo-500/30 shadow-xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Interactive Evaluator Quick-Start</h2>
          <p className="text-xs text-slate-400">Select a pre-seeded persona to explore role-tailored dashboards instantly:</p>
        </div>
        <Lock className="w-5 h-5 text-indigo-400" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
        <button
          onClick={() => {
            quickLoginAs('executive_admin');
            setCurrentPage('dashboard');
          }}
          className="p-4 rounded-xl bg-rose-950/30 hover:bg-rose-900/40 border border-rose-500/30 text-left transition-all group hover:scale-[1.02]"
        >
          <div className="font-bold text-xs text-rose-300 group-hover:text-rose-200">1. Executive Admin (Laila Fouad)</div>
          <div className="text-[11px] text-slate-400 mt-1">Review HITL discount queue, toggle tool matrix, inspect failure tickets.</div>
        </button>

        <button
          onClick={() => {
            quickLoginAs('property_manager');
            setCurrentPage('dashboard');
          }}
          className="p-4 rounded-xl bg-indigo-950/30 hover:bg-indigo-900/40 border border-indigo-500/30 text-left transition-all group hover:scale-[1.02]"
        >
          <div className="font-bold text-xs text-indigo-300 group-hover:text-indigo-200">2. Property Manager (Tarek Mahmoud)</div>
          <div className="text-[11px] text-slate-400 mt-1">Execute state graphs, review commercial leases, dispatch maintenance contractors.</div>
        </button>

        <button
          onClick={() => {
            quickLoginAs('tenant');
            setCurrentPage('dashboard');
          }}
          className="p-4 rounded-xl bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/30 text-left transition-all group hover:scale-[1.02]"
        >
          <div className="font-bold text-xs text-emerald-300 group-hover:text-emerald-200">3. Registered Tenant (Amr Hassan)</div>
          <div className="text-[11px] text-slate-400 mt-1">View active lease, check payment status, submit emergency repair requests.</div>
        </button>
      </div>
    </section>
  );
};
