/**
 * Property Manager Operations Dashboard (platform/src/pages/dashboard/ManagerDashboard.tsx)
 */

import React, { useEffect, useState } from 'react';
import {
  Building,
  FileText,
  Wrench,
  GitBranch,
  TrendingUp,
  Clock,
  ArrowRight,
  Play,
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';

export const ManagerDashboard: React.FC = () => {
  const { setCurrentPage, addToast } = useAppStore();
  const [leases, setLeases] = useState<any[]>([]);
  const [maintenance, setMaintenance] = useState<any[]>([]);
  const [isRunningGraph, setIsRunningGraph] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const leaseRes = await apiClient('/api/leases').catch(() => null);
        if (leaseRes?.leases) setLeases(leaseRes.leases);

        const maintRes = await apiClient('/api/maintenance').catch(() => null);
        if (maintRes?.requests) setMaintenance(maintRes.requests);
      } catch (err) {
        console.error('Failed to load manager dashboard:', err);
      }
    }
    loadData();
  }, []);

  const handleLaunchGraph = async (graphId: string) => {
    setIsRunningGraph(true);
    try {
      const res = await apiClient('/api/state-graph/run', {
        method: 'POST',
        body: JSON.stringify({
          graph_id: graphId,
          variables: {
            lease_id: 101,
            unit_id: 2,
            tenant_email: 'tarek.mahdy@cairomed.org',
            base_rent: 45000,
            proposed_rent: 42000,
          },
        }),
      });
      addToast(`Graph '${graphId}' executed (Status: ${res.graph_status})`, 'success');
      setCurrentPage('stateGraph');
    } catch (err: any) {
      addToast(err.message || 'Failed to start state graph', 'error');
    } finally {
      setIsRunningGraph(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Operations Command Dashboard</h1>
        <p className="text-xs text-slate-400 mt-1">
          Property management, commercial lease state machines, and contractor dispatch workflows.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Active Leases</div>
          <div className="text-2xl font-black text-indigo-400">{leases.length || 7}</div>
          <div className="text-[10px] text-slate-400">Commercial & Residential</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Open Maintenance</div>
          <div className="text-2xl font-black text-amber-400">{maintenance.length || 5}</div>
          <div className="text-[10px] text-slate-400">Work orders in progress</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Avg Occupancy</div>
          <div className="text-2xl font-black text-emerald-400">89.4%</div>
          <div className="text-[10px] text-slate-400">Across 6 properties</div>
        </div>

        <div className="glass-card p-4 space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">State Machine Engine</div>
          <div className="text-2xl font-black text-cyan-400">Online</div>
          <div className="text-[10px] text-slate-400">Graph 1 (Escrow Active)</div>
        </div>
      </div>

      {/* Autonomous State Machine Quick Runner */}
      <section className="glass-card p-6 space-y-4 border-indigo-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-indigo-400" />
              <span>Autonomous State Graph Execution</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Launch deterministic state machine runs with Human-in-the-Loop governance hooks:
            </p>
          </div>
          <button
            onClick={() => setCurrentPage('stateGraph')}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold"
          >
            <span>Open React Flow Canvas</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div>
              <div className="text-xs font-bold text-slate-200">Graph 1: Commercial Lease & Escrow</div>
              <div className="text-[11px] text-slate-400 mt-1">
                Background checks, discount audit, escrow verification, and lease execution.
              </div>
            </div>
            <button
              onClick={() => handleLaunchGraph('graph_commercial_lease')}
              disabled={isRunningGraph}
              className="w-full py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center space-x-1.5 shadow-md"
            >
              <Play className="w-3 h-3" />
              <span>{isRunningGraph ? 'Running...' : 'Execute Lease Graph'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div>
              <div className="text-xs font-bold text-slate-200">Graph 2: Emergency Renovation DAG</div>
              <div className="text-[11px] text-slate-400 mt-1">
                Structural assessment, contractor bids, municipal permits, and post-repair inspection.
              </div>
            </div>
            <button
              onClick={() => handleLaunchGraph('graph_renovation_dag')}
              disabled={isRunningGraph}
              className="w-full py-2 rounded-lg text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white flex items-center justify-center space-x-1.5 shadow-md"
            >
              <Play className="w-3 h-3" />
              <span>Execute Renovation Graph</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div>
              <div className="text-xs font-bold text-slate-200">Graph 3: Arrears & Eviction Notice</div>
              <div className="text-[11px] text-slate-400 mt-1">
                Statutory grace period, Egyptian Law 4/1996 compliance, and executive escalation.
              </div>
            </div>
            <button
              onClick={() => handleLaunchGraph('graph_eviction_resolution')}
              disabled={isRunningGraph}
              className="w-full py-2 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center space-x-1.5 shadow-md"
            >
              <Play className="w-3 h-3" />
              <span>Execute Arrears Graph</span>
            </button>
          </div>
        </div>
      </section>

      {/* Leases in Review Directory */}
      <section className="glass-card p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <FileText className="w-4 h-4 text-emerald-400" />
          <span>Active Leases Directory</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                <th className="p-3">Property</th>
                <th className="p-3">Unit</th>
                <th className="p-3">Tenant</th>
                <th className="p-3">Rent</th>
                <th className="p-3">Payment Status</th>
                <th className="p-3">Sign-off Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {leases.map((l) => (
                <tr key={l.lease_id} className="hover:bg-slate-800/30">
                  <td className="p-3 font-semibold text-slate-100">{l.property_name}</td>
                  <td className="p-3">{l.unit_number}</td>
                  <td className="p-3">{l.tenant_name || l.tenant_email}</td>
                  <td className="p-3 font-bold text-emerald-400">{Number(l.monthly_rent).toLocaleString()} EGP</td>
                  <td className="p-3 capitalize">{l.payment_status}</td>
                  <td className="p-3">
                    {l.requires_executive_signoff ? (
                      <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-semibold">
                        Needs Sign-off
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-semibold">
                        Approved
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
