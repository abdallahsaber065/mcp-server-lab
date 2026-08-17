/**
 * State Graph Studio & Visualizer (platform/src/pages/stateGraph/StateGraphPage.tsx)
 * Displays deterministic state transitions, node glow, variables inspector, and checkpoint history.
 */

import React, { useState } from 'react';
import {
  GitBranch,
  Play,
  CheckCircle2,
  AlertCircle,
  PauseCircle,
  Clock,
  RefreshCw,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';

interface NodeInfo {
  name: string;
  label: string;
  description: string;
}

const GRAPH_1_NODES: NodeInfo[] = [
  { name: 'verify_tenant_identity', label: '1. Tenant Verification', description: 'Query tenant background and KYC status' },
  { name: 'audit_discount_compliance', label: '2. Discount Policy Audit', description: 'Validate discount against 10% policy limit' },
  { name: 'escrow_bank_check', label: '3. Escrow Bank Check', description: 'Confirm bank deposit & liquidity' },
  { name: 'execute_commercial_lease', label: '4. Execute Lease', description: 'Persist lease and transition unit status' },
];

export const StateGraphPage: React.FC = () => {
  const { addToast } = useAppStore();
  const [selectedGraph, setSelectedGraph] = useState('graph_commercial_lease');
  const [activeNode, setActiveNode] = useState<string>('verify_tenant_identity');
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [graphStatus, setGraphStatus] = useState<string>('idle');
  const [pendingHITL, setPendingHITL] = useState<boolean>(false);
  const [variables, setVariables] = useState<Record<string, any>>({
    lease_id: 101,
    unit_id: 2,
    tenant_email: 'tarek.mahdy@cairomed.org',
    base_rent: 45000,
    proposed_rent: 42000,
  });
  const [history, setHistory] = useState<any[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleRunGraph = async () => {
    setIsExecuting(true);
    setGraphStatus('running');
    setCompletedNodes([]);
    setPendingHITL(false);

    try {
      const res = await apiClient('/api/state-graph/run', {
        method: 'POST',
        body: JSON.stringify({
          graph_id: selectedGraph,
          variables: variables,
        }),
      });

      setGraphStatus(res.graph_status);
      setActiveNode(res.current_node);
      setPendingHITL(res.pending_hitl);
      setVariables(res.variables || {});
      setHistory(res.history || []);

      if (res.graph_status === 'paused') {
        addToast('State graph paused at HITL node awaiting executive approval', 'warning');
      } else if (res.graph_status === 'completed') {
        setCompletedNodes(GRAPH_1_NODES.map((n) => n.name));
        addToast('State graph completed execution cleanly', 'success');
      } else {
        addToast(`Graph run finished with status: ${res.graph_status}`, 'info');
      }
    } catch (err: any) {
      setGraphStatus('failed');
      addToast(err.message || 'State graph execution failed', 'error');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-indigo-400" />
            <span>State Graph Studio & Checkpoint Visualizer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic LangGraph-style workflow execution with cyclical error recovery and HITL pauses.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedGraph}
            onChange={(e) => setSelectedGraph(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="graph_commercial_lease">Graph 1: Commercial Lease & Escrow</option>
            <option value="graph_renovation_dag">Graph 2: Renovation DAG</option>
            <option value="graph_eviction_resolution">Graph 3: Arrears & Eviction Notice</option>
          </select>

          <button
            onClick={handleRunGraph}
            disabled={isExecuting}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition-all"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isExecuting ? 'Executing...' : 'Run State Graph'}</span>
          </button>
        </div>
      </div>

      {/* State Graph Visual Pipeline */}
      <section className="glass-card p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Execution Pipeline: {selectedGraph}
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-400">Current Status:</span>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold capitalize ${
                graphStatus === 'completed'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : graphStatus === 'paused'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : graphStatus === 'failed'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {graphStatus}
            </span>
          </div>
        </div>

        {/* Node Transition Flow Pipeline */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 relative">
          {GRAPH_1_NODES.map((node, index) => {
            const isCompleted = completedNodes.includes(node.name);
            const isActive = activeNode === node.name && graphStatus !== 'idle';
            const isPausedHere = pendingHITL && activeNode === node.name;

            return (
              <div
                key={node.name}
                className={`p-4 rounded-2xl border transition-all space-y-2 relative ${
                  isPausedHere
                    ? 'bg-amber-950/40 border-amber-500/80 shadow-lg shadow-amber-500/20 glow-blue'
                    : isActive
                    ? 'bg-indigo-950/40 border-indigo-500/80 shadow-lg shadow-indigo-500/20'
                    : isCompleted
                    ? 'bg-emerald-950/30 border-emerald-500/40'
                    : 'bg-slate-950/50 border-slate-800 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Step {index + 1}</span>
                  {isPausedHere ? (
                    <PauseCircle className="w-4 h-4 text-amber-400 animate-pulse" />
                  ) : isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isActive ? (
                    <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />
                  ) : (
                    <Clock className="w-4 h-4 text-slate-600" />
                  )}
                </div>

                <div className="font-bold text-xs text-slate-100">{node.label}</div>
                <div className="text-[11px] text-slate-400">{node.description}</div>
              </div>
            );
          })}
        </div>

        {/* Pending HITL Notice */}
        {pendingHITL && (
          <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
              <div>
                <div className="font-bold">Human-in-the-Loop Interruption: Discount Sign-off Required</div>
                <div className="text-[11px] text-amber-300/80">
                  The state graph paused execution. An Executive Admin must approve this transaction in the Admin Center.
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Variables & Checkpoints Inspector */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Graph State Variables */}
        <div className="glass-card p-6 space-y-3">
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Active State Variables Inspector</span>
          </h2>
          <pre className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-emerald-400 font-mono overflow-x-auto">
            {JSON.stringify(variables, null, 2)}
          </pre>
        </div>

        {/* Checkpoint Execution History */}
        <div className="glass-card p-6 space-y-3">
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Deterministic Checkpoint History</span>
          </h2>
          {history.length === 0 ? (
            <div className="text-xs text-slate-400 p-4">No checkpoints recorded for this run yet.</div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {history.map((step, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-bold text-slate-200">Step {step.step}: {step.node}</span>
                    <div className="text-[10px] text-slate-400">{step.timestamp || 'Recorded'}</div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-emerald-500/20 text-emerald-300">
                    {step.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
