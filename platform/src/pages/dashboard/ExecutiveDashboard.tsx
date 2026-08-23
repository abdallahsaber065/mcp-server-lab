/**
 * Executive Admin Dashboard (platform/src/pages/dashboard/ExecutiveDashboard.tsx)
 */

import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  DollarSign,
  AlertTriangle,
  Sliders,
  ArrowRight,
  CheckCircle2,
  FileCheck,
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';

export const ExecutiveDashboard: React.FC = () => {
  const { setCurrentPage } = useAppStore();
  const [hitlCount, setHitlCount] = useState<number>(0);
  const [ticketCount, setTicketCount] = useState<number>(0);

  useEffect(() => {
    async function loadStats() {
      try {
        const hitlRes = await apiClient('/api/admin/hitl/tasks').catch(() => null);
        if (hitlRes?.tasks) setHitlCount(hitlRes.tasks.length);

        const ticketRes = await apiClient('/api/admin/tickets').catch(() => null);
        if (ticketRes?.tickets) setTicketCount(ticketRes.tickets.length);
      } catch (err) {
        console.error('Failed to load executive stats:', err);
      }
    }
    loadStats();
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Executive Command Center</h1>
        <p className="text-xs text-slate-400 mt-1">
          Governance portal for Human-in-the-Loop discount sign-offs, tool permissions, and node recovery.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Monthly Portfolio Rent</div>
          <div className="text-2xl font-black text-emerald-400">428,000 EGP</div>
          <div className="text-[10px] text-slate-400">Across 6 prime properties</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Pending HITL Approvals</div>
          <div className="text-2xl font-black text-amber-400">{hitlCount} Tasks</div>
          <div className="text-[10px] text-slate-400">Paused state graph runs</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Failure Tickets</div>
          <div className="text-2xl font-black text-rose-400">{ticketCount} Tickets</div>
          <div className="text-[10px] text-slate-400">State graph node errors</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">MCP Dynamic Tools</div>
          <div className="text-2xl font-black text-indigo-400">14 Active</div>
          <div className="text-[10px] text-slate-400">Hot-toggleable with listChanged</div>
        </div>
      </div>

      {/* Quick Access Governance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card-hover p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-amber-400" />
              <span>HITL Review Queue</span>
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30">
              {hitlCount} Pending
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Sign off on commercial lease rental discounts exceeding the 10% policy threshold before graph progression.
          </p>
          <button
            onClick={() => setCurrentPage('admin')}
            className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 pt-2"
          >
            <span>Open HITL Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="glass-card-hover p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              <span>Dynamic Tool Matrix</span>
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
              14 Tools
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Dynamically toggle tools at runtime for each agent persona, pushing MCP notifications/tools/list_changed.
          </p>
          <button
            onClick={() => setCurrentPage('admin')}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 pt-2"
          >
            <span>Configure Tool Matrix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="glass-card-hover p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Failure Ticket Workbench</span>
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30">
              {ticketCount} Open
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Inspect captured state graph node failure traces, resolve underlying issues, and resume runs from checkpoint.
          </p>
          <button
            onClick={() => setCurrentPage('admin')}
            className="text-xs font-semibold text-rose-400 hover:text-rose-300 flex items-center gap-1 pt-2"
          >
            <span>Inspect Failure Tickets</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
