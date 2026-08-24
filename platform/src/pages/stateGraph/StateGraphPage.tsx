/**
 * State Graph Studio & Checkpoint Visualizer - ReactFlow + dagre + persistence
 * Spec-aligned to STATEFUL_PROBLEMS_EGYPTIAN_ARABIC.md
 */

import React, { useState, useEffect } from 'react';
import { GitBranch, Play, Layers, Clock, ShieldAlert, Eye, History, Save, RotateCcw } from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import { GraphCanvas, type GraphDef } from '../../components/stateGraph/GraphCanvas';
import { CheckpointTimeline } from '../../components/stateGraph/CheckpointTimeline';

const GRAPH_CATALOG: Record<string, GraphDef & { narrative: string; variablesPrefill: Record<string, any> }> = {
  commercial_lease_flow: {
    graph_id: 'commercial_lease_flow',
    narrative: 'Commercial Lease Onboarding & Escrow Verification — Suite-301 clinic lease (60k base, 48k proposed, 20% discount), 144k escrow deposit, multimodal Gemini OCR, Chief Accountant verification, and Executive concession authorization.',
    variablesPrefill: { unit_id: 301, base_rent: 60000, proposed_rent: 48000, applicant_name: 'Dr. Tarek El-Mahdy', receipt_image_urls: ['/receipts/bank_misr_escrow_deposit_suite301.png'], request_text: 'Suite-301 commercial clinic lease in Giza Business Corridor' },
    nodes: [
      { name: 'decompose_requirements', label: '1. Requirements Decomposition', description: 'Decompose lease into credit, abatement, escrow, and sign-off milestones', type: 'glass', llmTag: 'TaskDecomp' },
      { name: 'audit_unit_and_credit', label: '2. Unit & Credit Audit', description: 'Query available units, tenant status, calculate 20% discount & 144k escrow', type: 'glass', llmTag: 'ReAct' },
      { name: 'verify_receipt_vision', label: '3. Multimodal Vision OCR', description: 'Extract bank, amount, depositor name, and reference from receipt images', type: 'glass', llmTag: 'Vision' },
      { name: 'accountant_verification', label: '4. Accountant Review', description: 'Chief Accountant verifies bank deposit confirmation in ledger', type: 'webhook', llmTag: 'HITL-wait' },
      { name: 'executive_concession', label: '5. Executive Concession Gate', description: 'Executive sign-off required when discount >15% or monthly rent >40k EGP', type: 'hitl', llmTag: 'HITL' },
      { name: 'execute_lease', label: '6. Execute Lease Contract', description: 'Activate lease agreement and update property registry status', type: 'glass' },
    ],
    edges: [
      { source: 'decompose_requirements', target: 'audit_unit_and_credit' },
      { source: 'audit_unit_and_credit', target: 'verify_receipt_vision' },
      { source: 'verify_receipt_vision', target: 'accountant_verification', label: 'Readable = Yes' },
      { source: 'accountant_verification', target: 'verify_receipt_vision', label: 'Needs Fix -> Retry', isCycle: true },
      { source: 'accountant_verification', target: 'executive_concession', label: 'Confirmed' },
      { source: 'executive_concession', target: 'execute_lease', label: 'Approved' },
      { source: 'executive_concession', target: 'decompose_requirements', label: 'Counter 10% = Cycle', isCycle: true },
    ],
  },
  renovation_permit_flow: {
    graph_id: 'renovation_permit_flow',
    narrative: 'Emergency Maintenance Dispatch & Contractor Tendering — Egyptian Law 4/1996 liability RAG, LATS Monte Carlo contractor scoring, Chief Engineer sign-off (>10k EGP), crew dispatch, and tenant satisfaction rating.',
    variablesPrefill: { location: 'Nile Heights Tower', property_name: 'Nile Heights Tower', issue_description: 'Emergency structural pipe burst flooding clinic floor' },
    nodes: [
      { name: 'retrieve_policy', label: '1. Law 4/1996 Policy Audit', description: 'Hybrid RAG retrieval classifying structural vs cosmetic liability and emergency SLAs', type: 'glass', llmTag: 'RAG' },
      { name: 'lats_tender_search', label: '2. LATS Contractor Scoring', description: 'MCTS evaluation exploring 3 contractor quotes, speed, and warranty matrices', type: 'glass', llmTag: 'LATS' },
      { name: 'engineer_approval', label: '3. Chief Engineer Sign-off', description: 'Chief Engineer approval required for work orders exceeding 10,000 EGP', type: 'hitl', llmTag: 'HITL' },
      { name: 'check_availability', label: '4. Contractor Dispatch & Availability', description: 'Confirm contractor dispatch and verify crew arrival window', type: 'glass' },
      { name: 'tenant_rating', label: '5. Tenant Service Rating', description: 'Tenant verifies completed repairs and rates service quality (1-5 stars)', type: 'webhook' },
      { name: 'close_ticket', label: '6. Finalize & Close Ticket', description: 'Work order marked COMPLETED, invoice logged, and satisfaction registered', type: 'glass' },
    ],
    edges: [
      { source: 'retrieve_policy', target: 'lats_tender_search', label: 'Owner Pays' },
      { source: 'retrieve_policy', target: 'close_ticket', label: 'Tenant Pays -> Close' },
      { source: 'lats_tender_search', target: 'engineer_approval' },
      { source: 'engineer_approval', target: 'check_availability', label: 'Approved' },
      { source: 'engineer_approval', target: 'lats_tender_search', label: 'Cheaper Needed = Re-tender', isCycle: true },
      { source: 'engineer_approval', target: 'close_ticket', label: 'Rejected -> Close' },
      { source: 'check_availability', target: 'lats_tender_search', label: 'Busy = Re-tender', isCycle: true },
      { source: 'check_availability', target: 'tenant_rating', label: 'Fix Executed' },
      { source: 'tenant_rating', target: 'close_ticket', label: '5 Stars = Done' },
      { source: 'tenant_rating', target: 'tenant_rating', label: 'Low Stars = Follow-up', isCycle: true },
    ],
  },
  rent_arrears_settlement_flow: {
    graph_id: 'rent_arrears_settlement_flow',
    narrative: 'Arrears Remediation & Debt Restructuring — Constrained ReAct invoice audit, Tree of Thoughts 3-path recovery proposal generation, tenant plan selection, and Legal Counsel contract amendment sign-off.',
    variablesPrefill: { tenant_id: 1, unpaid_months: 2, monthly_rent: 45000 },
    nodes: [
      { name: 'audit_arrears', label: '1. Payment Ledger Audit', description: 'Audit overdue invoices and tenant payment compliance history via MCP', type: 'glass' },
      { name: 'tot_offers_generator', label: '2. Tree of Thoughts Proposals', description: 'Explore 3 distinct settlement trajectories: balanced, upfront discount, extended grace', type: 'glass', llmTag: 'ToT' },
      { name: 'await_tenant_response', label: '3. Tenant Plan Selection', description: 'Tenant selects preferred restructuring plan or requests customized schedule', type: 'webhook' },
      { name: 'finance_legal_approval', label: '4. Legal & Finance Sign-off', description: 'Legal Counsel and Finance Officer sign off on contract restructuring terms', type: 'hitl', llmTag: 'HITL' },
      { name: 'activate_plan', label: '5. Activate Restructuring', description: 'Activate restructured payment plan and update ledger schedule', type: 'glass' },
      { name: 'escalate_refusal', label: '6. Statutory Escalation', description: 'Escalate to formal legal proceedings upon negotiation deadlock', type: 'glass' },
    ],
    edges: [
      { source: 'audit_arrears', target: 'tot_offers_generator' },
      { source: 'tot_offers_generator', target: 'await_tenant_response' },
      { source: 'await_tenant_response', target: 'finance_legal_approval', label: 'Accept Offer' },
      { source: 'await_tenant_response', target: 'tot_offers_generator', label: 'Counter Schedule = ToT Cycle', isCycle: true },
      { source: 'await_tenant_response', target: 'escalate_refusal', label: 'Refusal / 15-Day Silence' },
      { source: 'finance_legal_approval', target: 'activate_plan', label: 'Approved -> Active' },
      { source: 'finance_legal_approval', target: 'tot_offers_generator', label: 'Adjust = ToT Cycle', isCycle: true },
      { source: 'finance_legal_approval', target: 'escalate_refusal', label: 'Rejected -> Legal' },
    ],
  },
};

const ALIAS_MAP: Record<string, string> = {
  graph_commercial_lease: 'commercial_lease_flow',
  maintenance_dispatch_flow: 'renovation_permit_flow',
  graph_renovation_dag: 'renovation_permit_flow',
  arrears_care_flow: 'rent_arrears_settlement_flow',
  graph_eviction_resolution: 'rent_arrears_settlement_flow',
};


interface SavedSession {
  runId: string;
  graphId: string;
  status: string;
  history: any[];
  variables: Record<string, any>;
  createdAt: string;
}

export const StateGraphPage: React.FC = () => {
  const [selectedGraph, setSelectedGraph] = useState<string>('commercial_lease_flow');
  const [runId, setRunId] = useState<string>('');
  const [graphStatus, setGraphStatus] = useState<string>('idle');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeNode, setActiveNode] = useState<string>('');
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, string>>({});
  const [variables, setVariables] = useState<Record<string, any>>(() => GRAPH_CATALOG.commercial_lease_flow.variablesPrefill);
  const [history, setHistory] = useState<any[]>([]);
  const [checkpoints, setCheckpoints] = useState<any[]>([]);
  const [pendingHitl, setPendingHitl] = useState<any>(null);
  const [inspector, setInspector] = useState<any>(null);
  const [diffData, setDiffData] = useState<any>(null);
  const [savedSessions, setSavedSessions] = useState<SavedSession[]>(() => {
    try { return JSON.parse(localStorage.getItem('sg_sessions') || '[]'); } catch { return []; }
  });

  const { addToast } = useAppStore();

  const handleSelectGraph = (newGraph: string) => {
    setSelectedGraph(newGraph);
    const last = localStorage.getItem(`sg_last_${newGraph}`);
    if (last) {
      try {
        const p = JSON.parse(last);
        if (p.runId) {
          setRunId(p.runId);
          setGraphStatus(p.status || 'idle');
          setHistory(p.history || []);
          setVariables(p.variables || GRAPH_CATALOG[newGraph]?.variablesPrefill);
          setNodeStatuses(p.nodeStatuses || {});
          setActiveNode(p.activeNode || '');
          setCheckpoints(p.checkpoints || []);
          setPendingHitl(p.pendingHitl || null);
          setInspector(null);
          setDiffData(null);
          return;
        }
      } catch {}
    }
    // Clean everything if no session for this graph
    setRunId('');
    setGraphStatus('idle');
    setHistory([]);
    setVariables(GRAPH_CATALOG[newGraph]?.variablesPrefill || {});
    setNodeStatuses({});
    setActiveNode('');
    setCheckpoints([]);
    setPendingHitl(null);
    setInspector(null);
    setDiffData(null);
  };

  // Persist current session whenever it changes
  useEffect(() => {
    if (!runId) return;
    const payload = { runId, graphId: selectedGraph, status: graphStatus, history, variables, nodeStatuses, activeNode, checkpoints, createdAt: new Date().toISOString() };
    localStorage.setItem(`sg_last_${selectedGraph}`, JSON.stringify(payload));
    // Also save to sessions list if completed/paused/awaiting
    if (['completed', 'paused', 'awaiting_webhook', 'failed'].includes(graphStatus)) {
      const existing: SavedSession[] = JSON.parse(localStorage.getItem('sg_sessions') || '[]');
      const idx = existing.findIndex(s => s.runId === runId);
      const session: SavedSession = { runId, graphId: selectedGraph, status: graphStatus, history, variables, createdAt: new Date().toISOString() };
      if (idx >= 0) existing[idx] = session;
      else existing.unshift(session);
      // keep last 20
      const trimmed = existing.slice(0, 20);
      localStorage.setItem('sg_sessions', JSON.stringify(trimmed));
      setSavedSessions(trimmed);
    }
  }, [runId, graphStatus, history, variables, nodeStatuses, activeNode, checkpoints, selectedGraph]);

  const handleRunGraph = async () => {
    const newRunId = `run-${Math.random().toString(36).slice(2, 10)}`;
    setRunId(newRunId);
    setIsStreaming(true);
    setGraphStatus('running');
    setPendingHitl(null);
    setHistory([]);
    setCheckpoints([]);
    setNodeStatuses({});
    setInspector(null);
    setDiffData(null);
    try {
      const res = await fetch('/api/state-graph/run/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('cornerstone_access_token') || ''}` },
        body: JSON.stringify({ graph_id: selectedGraph, run_id: newRunId, variables }),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.replace('data: ', '').trim();
            if (raw === '[DONE]') continue;
            try {
              const evt = JSON.parse(raw);
              if (evt.type === 'node_start') {
                setActiveNode(evt.node);
                setNodeStatuses(prev => ({ ...prev, [evt.node]: 'running' }));
              } else if (evt.type === 'node_complete') {
                setHistory(prev => [...prev, { step: evt.step, node: evt.node, status: evt.status, message: evt.message }]);
                setNodeStatuses(prev => ({ ...prev, [evt.node]: evt.status === 'CONTINUE' ? 'completed' : evt.status === 'PAUSE_HITL' ? 'paused_hitl' : evt.status === 'WAIT_WEBHOOK' ? 'awaiting_webhook' : evt.status === 'FINISH' ? 'completed' : 'idle' }));
                if (evt.status === 'PAUSE_HITL' || evt.status === 'WAIT_WEBHOOK') setActiveNode(evt.next_node || evt.node);
                if (evt.variables) setVariables(evt.variables);
                if (evt.pending_hitl) setPendingHitl(evt.pending_hitl);
                setCheckpoints(prev => [...prev, { step: evt.step, node: evt.node, status: evt.status, created_at: new Date().toISOString(), checkpoint_id: `cp-${evt.step}` }]);
              } else if (evt.type === 'final') {
                const rawStatus = String(evt.graph_status || evt.status || 'idle');
                setGraphStatus(rawStatus === 'COMPLETED' ? 'completed' : rawStatus === 'PAUSED_HITL' ? 'paused' : rawStatus === 'AWAITING_WEBHOOK' ? 'awaiting_webhook' : rawStatus.toLowerCase());
                setRunId(evt.run_id || newRunId);
                setVariables(evt.variables || {});
                setHistory(evt.history || []);
                setPendingHitl(evt.pending_hitl);
                if (rawStatus === 'COMPLETED') {
                  const def = GRAPH_CATALOG[selectedGraph];
                  const doneMap: Record<string, string> = {};
                  def.nodes.forEach(n => (doneMap[n.name] = 'completed'));
                  setNodeStatuses(doneMap);
                  addToast('State graph completed — contract / work order active', 'success');
                } else if (rawStatus === 'PAUSED_HITL') {
                  addToast('Paused at HITL — approve inline or in Admin Center', 'warning');
                }
                if (evt.run_id) {
                  try {
                    const cpRes = await apiClient(`/api/state-graph/${evt.run_id}/history`);
                    if (cpRes.checkpoints) setCheckpoints(cpRes.checkpoints);
                  } catch {}
                }
              }
            } catch {}
          }
        }
      }
    } catch (err: any) {
      setGraphStatus('failed');
      addToast(err.message || 'State graph execution failed', 'error');
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSelectCheckpoint = async (step: number) => {
    if (!runId) {
      addToast('No runId — run a graph first', 'info');
      return;
    }
    try {
      const res = await apiClient(`/api/state-graph/${runId}/checkpoint/${step}`);
      setInspector(res);
      setDiffData(null);
    } catch (e: any) {
      addToast(e.message || 'Failed to load checkpoint', 'error');
    }
  };

  const handleDiff = async (a: number, b: number) => {
    if (!runId) return;
    try {
      const ra = await apiClient(`/api/state-graph/${runId}/checkpoint/${a}`);
      const rb = await apiClient(`/api/state-graph/${runId}/checkpoint/${b}`);
      const varsA = (ra.state as any).variables || (ra.state as any) || {};
      const varsB = (rb.state as any).variables || (rb.state as any) || {};
      const vA = varsA.variables ? varsA.variables : varsA;
      const vB = varsB.variables ? varsB.variables : varsB;
      const added: any = {}; const modified: any = {}; const removed: string[] = [];
      for (const k of Object.keys(vB)) if (!(k in vA)) added[k] = vB[k]; else if (JSON.stringify(vA[k]) !== JSON.stringify(vB[k])) modified[k] = { from: vA[k], to: vB[k] };
      for (const k of Object.keys(vA)) if (!(k in vB)) removed.push(k);
      setDiffData({ from: a, to: b, added, modified, removed });
    } catch (e: any) {
      addToast(e.message || 'Diff failed — checkpoint may not exist', 'error');
    }
  };

  const handleRollback = async (step: number) => {
    if (!runId) return;
    try {
      const res = await apiClient(`/api/state-graph/${runId}/rollback/${step}`, { method: 'POST' });
      addToast(`Rolled back to step ${step}`, 'success');
      const cpRes = await apiClient(`/api/state-graph/${runId}/history`);
      if (cpRes.checkpoints) setCheckpoints(cpRes.checkpoints);
      if (res.state) {
        setVariables(res.state);
        setInspector({ step, node: res.node || res.next?.[0] || 'checkpoint', status_at_step: 'ROLLED_BACK', state: res.state });
      }

      const def = GRAPH_CATALOG[selectedGraph];
      const targetNodeName = res.node || (res.next && res.next[0]) || def.nodes[0]?.name;
      const targetIdx = def.nodes.findIndex(n => n.name === targetNodeName);
      
      const newStatuses: Record<string, string> = {};
      const hasHitl = Boolean(res.pending_hitl || (res.tasks && res.tasks.length > 0));

      def.nodes.forEach((n, idx) => {
        if (targetIdx >= 0 && idx < targetIdx) {
          newStatuses[n.name] = 'completed';
        } else if (idx === targetIdx) {
          newStatuses[n.name] = hasHitl ? 'paused_hitl' : 'running';
        } else {
          newStatuses[n.name] = 'idle';
        }
      });

      setNodeStatuses(newStatuses);
      setActiveNode(targetNodeName);
      setPendingHitl(res.pending_hitl || null);
      setGraphStatus(hasHitl ? 'paused' : 'idle');
    } catch (e: any) {
      addToast(e.message || 'Rollback failed', 'error');
    }
  };

  const handleContinueExecution = async () => {
    if (!runId) return;
    setIsStreaming(true);
    setGraphStatus('running');
    try {
      const res = await fetch('/api/state-graph/run/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('cornerstone_access_token') || ''}` },
        body: JSON.stringify({ graph_id: selectedGraph, run_id: runId, variables }),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.replace('data: ', '').trim();
            if (raw === '[DONE]') continue;
            try {
              const evt = JSON.parse(raw);
              if (evt.type === 'node_start') {
                setActiveNode(evt.node);
                setNodeStatuses(prev => ({ ...prev, [evt.node]: 'running' }));
              } else if (evt.type === 'node_complete') {
                setHistory(prev => [...prev, { step: evt.step, node: evt.node, status: evt.status, message: evt.message }]);
                setNodeStatuses(prev => ({ ...prev, [evt.node]: evt.status === 'CONTINUE' ? 'completed' : evt.status === 'PAUSE_HITL' ? 'paused_hitl' : 'idle' }));
                if (evt.status === 'PAUSE_HITL') setActiveNode(evt.node);
                if (evt.variables) setVariables(evt.variables);
                if (evt.pending_hitl) setPendingHitl(evt.pending_hitl);
                setCheckpoints(prev => [...prev, { step: evt.step, node: evt.node, status: evt.status, created_at: new Date().toISOString(), checkpoint_id: `cp-${evt.step}` }]);
              } else if (evt.type === 'final') {
                const rawStatus = String(evt.graph_status || evt.status || 'idle');
                setGraphStatus(rawStatus === 'COMPLETED' ? 'completed' : rawStatus === 'PAUSED_HITL' ? 'paused' : rawStatus.toLowerCase());
                setVariables(evt.variables || {});
                setPendingHitl(evt.pending_hitl || null);
                if (rawStatus === 'COMPLETED') {
                  const def = GRAPH_CATALOG[selectedGraph];
                  const doneMap: Record<string, string> = {};
                  def.nodes.forEach(n => (doneMap[n.name] = 'completed'));
                  setNodeStatuses(doneMap);
                  addToast('State graph completed — execution finalized', 'success');
                } else if (rawStatus === 'PAUSED_HITL') {
                  addToast('Paused at HITL — approve inline or in Admin Center', 'warning');
                }
              }
            } catch {}
          }
        }
      }
    } catch (err: any) {
      setGraphStatus('failed');
      addToast(err.message || 'Continuation failed', 'error');
    } finally {
      setIsStreaming(false);
    }
  };

  const handleWebhookResume = async (payloadKey: string, payload: any) => {
    const resumePayload = { [payloadKey]: payload, decision: payload, approved: payload === 'APPROVED' || payload === true };
    setGraphStatus('running');
    try {
      const res = await apiClient('/api/state-graph/run', {
        method: 'POST',
        body: JSON.stringify({
          graph_id: selectedGraph,
          run_id: runId,
          resume_value: resumePayload,
          variables: { ...variables, ...resumePayload },
        }),
      });
      const rawStatus = String(res.graph_status || (res.is_paused ? 'PAUSED_HITL' : 'COMPLETED'));
      const isPaused = res.is_paused || rawStatus === 'PAUSED_HITL';
      setGraphStatus(isPaused ? 'paused' : 'completed');
      setPendingHitl(res.pending_hitl || null);
      if (res.values) setVariables(res.values);

      const nextNode = res.next_nodes && res.next_nodes.length > 0 ? res.next_nodes[0] : null;
      if (nextNode) {
        setActiveNode(nextNode);
        setNodeStatuses(prev => {
          const updated = { ...prev };
          if (activeNode) updated[activeNode] = 'completed';
          updated[nextNode] = 'paused_hitl';
          return updated;
        });
      } else if (!isPaused) {
        const def = GRAPH_CATALOG[selectedGraph];
        const doneMap: Record<string, string> = {};
        def.nodes.forEach(n => (doneMap[n.name] = 'completed'));
        setNodeStatuses(doneMap);
      }

      // Refresh checkpoints
      try {
        const cpRes = await apiClient(`/api/state-graph/${runId}/history`);
        if (cpRes.checkpoints) setCheckpoints(cpRes.checkpoints);
      } catch {}
      addToast(isPaused ? 'Resumed -> Paused at next HITL review' : 'Resumed -> State Graph Completed!', isPaused ? 'warning' : 'success');
    } catch (e: any) {
      addToast(e.message || 'Resume failed', 'error');
    }
  };


  const loadSession = async (session: SavedSession) => {
    setSelectedGraph(session.graphId);
    setRunId(session.runId);
    setGraphStatus(session.status);
    setHistory(session.history || []);
    setVariables(session.variables || GRAPH_CATALOG[session.graphId]?.variablesPrefill);
    setActiveNode(session.history?.[session.history.length - 1]?.node || '');
    // Try to fetch latest checkpoints for that run
    try {
      const cpRes = await apiClient(`/api/state-graph/${session.runId}/history`);
      if (cpRes.checkpoints) setCheckpoints(cpRes.checkpoints);
      const stateRes = await apiClient(`/api/state-graph/${session.runId}`);
      if (stateRes.state) {
        setVariables(stateRes.state.variables || session.variables);
        setPendingHitl(stateRes.state.pending_hitl);
      }
    } catch {}
    // Build nodeStatuses from history
    const statuses: Record<string, string> = {};
    session.history?.forEach((h: any) => {
      statuses[h.node] = h.status === 'CONTINUE' ? 'completed' : h.status === 'PAUSE_HITL' ? 'paused_hitl' : h.status === 'WAIT_WEBHOOK' ? 'awaiting_webhook' : h.status === 'FINISH' ? 'completed' : 'idle';
    });
    setNodeStatuses(statuses);
    addToast(`Loaded session ${session.runId} (${session.status})`, 'info');
  };

  const graphDef = GRAPH_CATALOG[selectedGraph];

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-indigo-400" />
            State Graph Studio & Checkpoint Visualizer
          </h1>
          <p className="text-xs text-slate-400 mt-1">Live ReactFlow + dagre • SSE streaming • Time-travel • Persistent sessions</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={selectedGraph} onChange={e => handleSelectGraph(e.target.value)} className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200">
            <option value="commercial_lease_flow">Graph 1: Lease & Receipt (TaskDecomp+ReAct+Vision)</option>
            <option value="renovation_permit_flow">Graph 2: Maintenance & Tender (RAG+LATS)</option>
            <option value="rent_arrears_settlement_flow">Graph 3: Arrears & Mediation (ToT+ReAct)</option>
          </select>
          {runId && graphStatus !== 'completed' && graphStatus !== 'running' && (
            <button onClick={handleContinueExecution} disabled={isStreaming} className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white shadow-lg shadow-emerald-600/30 flex items-center gap-2">
              <Play className={`w-3.5 h-3.5 ${isStreaming ? 'animate-spin' : ''}`} />
              Continue Run
            </button>
          )}
          <button onClick={handleRunGraph} disabled={isStreaming} className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white shadow-lg shadow-indigo-600/30 flex items-center gap-2">
            <Play className={`w-3.5 h-3.5 ${isStreaming ? 'animate-spin' : ''}`} />
            {isStreaming ? 'Streaming...' : 'New Run'}
          </button>
        </div>
      </div>

      {/* Presentation hero — Arabic RTL */}
      <div className="glass-card p-5 border border-indigo-500/20 bg-gradient-to-br from-indigo-950/30 to-slate-900/40 rounded-2xl space-y-3" dir="rtl" lang="ar">
        {selectedGraph === 'commercial_lease_flow' && (
          <div className="space-y-2 text-right">
            <h2 className="text-sm font-extrabold text-indigo-200">الجراف الأول — دورة تأجير الوحدات وفحص الإيصالات بالذكاء الاصطناعي</h2>
            <p className="text-xs leading-6 text-slate-200">مستأجر يطلب استئجار <span className="text-indigo-300 font-bold">Suite-301</span> بقيمة 60,000 ج.م بخصم 20% إلى 48,000 ج.م. يجزّئ الوكيل المتطلبات إلى 4 مهام، يدقّق عبر <span className="text-violet-300">Constrained ReAct</span> (lookup_available_units + get_tenant_lease) ليحسب 144,000 ج.م ضمان، يرفع إيصالًا، يستخرج <span className="text-cyan-300">Gemini Vision</span> {"{البنك، المبلغ، المودع، المرجع}"} كـ JSON، يؤكّد <span className="text-amber-300">المحاسب</span> المطابقة، ثم يتوقف لموافقة <span className="text-amber-300">المدير التنفيذي</span> إذا الخصم &gt;15% — Cycle عند الرفض، Ticket إذا تالف، ثم record_rent_payment.</p>
            <div className="flex flex-wrap gap-1.5 justify-start" dir="ltr">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300">Task Decomposition</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">Constrained ReAct</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-cyan-300">Gemini Vision</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300">HITL محاسب + تنفيذي</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300">Ticket</span>
            </div>
          </div>
        )}
        {selectedGraph === 'renovation_permit_flow' && (
          <div className="space-y-2 text-right">
            <h2 className="text-sm font-extrabold text-indigo-200">الجراف الثاني — إدارة بلاغات الصيانة ومفاضلة المقاولين</h2>
            <p className="text-xs leading-6 text-slate-200">بلاغ طارئ في <span className="text-indigo-300">Cornerstone Heights</span> عبر get_my_maintenance_requests، يسترجع لوائح 4/1996 عبر <span className="text-cyan-300">RAG</span>، يشغّل <span className="text-violet-300">LATS</span> للمفاضلة بين 3 مقاولين، يتوقف لموافقة <span className="text-amber-300">المهندس</span> إذا &gt;10,000 ج.م، ثم انتظار <span className="text-cyan-300">تقييم المستأجر 1-5</span>، Ticket إذا تأخر، ويُغلق RESOLVED.</p>
            <div className="flex flex-wrap gap-1.5 justify-start" dir="ltr">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-cyan-300">RAG</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300">LATS MCTS</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300">HITL مهندس</span>
            </div>
          </div>
        )}
        {selectedGraph === 'rent_arrears_settlement_flow' && (
          <div className="space-y-2 text-right">
            <h2 className="text-sm font-extrabold text-indigo-200">الجراف الثالث — التفاوض على المتأخرات وجدولة الدفعات</h2>
            <p className="text-xs leading-6 text-slate-200">متأخرات 90,000 ج.م، يفحص <span className="text-indigo-300">list_tenant_payments</span> + <span className="text-indigo-300">get_tenant_lease</span> (ReAct)، يولّد <span className="text-violet-300">ToT</span> 3 مسارات (6ش/انتقال/15% خصم)، ينتظر رد <span className="text-cyan-300">المستأجر</span> (قبول/عرض 9ش→Cycle/رفض)، ثم موافقة <span className="text-amber-300">القانوني</span>، Ticket 15 يوم، ويُفعّل الجدول.</p>
            <div className="flex flex-wrap gap-1.5 justify-start" dir="ltr">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 border border-violet-500/30 text-violet-300">Tree of Thoughts</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">ReAct</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300">HITL قانوني</span>
            </div>
          </div>
        )}
        <div className="text-[11px] text-slate-500 text-left" dir="ltr">Spec: STATEFUL_PROBLEMS_EGYPTIAN_ARABIC.md • 2 LLM/graph • Cycles • HITL vs Ticket distinct • Persistent sessions</div>
      </div>

      {/* Sessions bar */}
      {savedSessions.length > 0 && (
        <div className="glass-card p-3 flex items-center gap-2 overflow-x-auto">
          <span className="text-xs font-bold text-slate-400 flex items-center gap-1"><Save className="w-3.5 h-3.5" /> Sessions ({savedSessions.length}):</span>
          {savedSessions.map(s => (
            <button key={s.runId} onClick={() => loadSession(s)} className={`px-3 py-1.5 rounded-xl text-xs font-mono border whitespace-nowrap ${s.runId === runId ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-indigo-500/50'}`}>
              {s.graphId.split('_')[0]} • {s.runId.slice(4,10)} • {s.status}
            </button>
          ))}
          <button onClick={() => { localStorage.removeItem('sg_sessions'); savedSessions.forEach(s => localStorage.removeItem(`sg_last_${s.graphId}`)); setSavedSessions([]); addToast('Sessions cleared', 'info'); }} className="text-xs text-rose-400 hover:text-rose-300 ml-auto">Clear</button>
        </div>
      )}

      {/* MAIN GRAPH — full width */}
      <section className="glass-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Live Graph — {selectedGraph} {runId && <span className="text-indigo-400 normal-case">• {runId}</span>}</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold capitalize ${graphStatus === 'completed' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : graphStatus === 'paused' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : graphStatus === 'awaiting_webhook' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : graphStatus === 'failed' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : graphStatus === 'running' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-slate-800 text-slate-400'}`}>{graphStatus}</span>
        </div>
        <GraphCanvas graphDef={graphDef} activeNode={activeNode} nodeStatuses={nodeStatuses} onNodeClick={setActiveNode} />
        {(graphStatus === 'paused' || graphStatus === 'awaiting_webhook') && (
          <div className={`p-3 rounded-xl border text-xs flex items-center justify-between ${graphStatus === 'paused' ? 'bg-amber-950/40 border-amber-500/40 text-amber-200' : 'bg-cyan-950/40 border-cyan-500/40 text-cyan-200'}`}>
            <div className="flex items-center gap-2">
              {graphStatus === 'paused' ? <ShieldAlert className="w-5 h-5 text-amber-400" /> : <Clock className="w-5 h-5 text-cyan-400" />}
              <div>
                <div className="font-bold">{graphStatus === 'paused' ? 'HITL Pause — Admin sign-off required' : 'Webhook Wait — Human action required'}</div>
                <div className="text-[11px] opacity-80">{pendingHitl?.reason || 'Resume via buttons below or Admin Center'}</div>
              </div>
            </div>
          </div>
        )}
        {(graphStatus === 'paused' || graphStatus === 'awaiting_webhook') && selectedGraph === 'commercial_lease_flow' && (
          <div className="flex flex-wrap gap-2 pt-1">
            {pendingHitl?.role_required === 'accountant' ? (
              <>
                <button onClick={() => handleWebhookResume('accountant_confirmed', true)} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-md shadow-emerald-600/30">✓ Confirm Escrow Deposit (Accountant)</button>
                <button onClick={() => handleWebhookResume('accountant_confirmed', false)} className="text-xs px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 font-semibold text-white">✕ Reject Deposit (Escrow Missing)</button>
              </>
            ) : (
              <>
                <button onClick={() => handleWebhookResume('executive_decision', 'APPROVED')} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-md shadow-emerald-600/30">✓ Approve Concession (Executive)</button>
                <button onClick={() => handleWebhookResume('executive_decision', 'COUNTER_10PCT')} className="text-xs px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 font-semibold text-white">Counter 10% Discount (Cycle)</button>
                <button onClick={() => handleWebhookResume('executive_decision', 'REJECTED')} className="text-xs px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 font-semibold text-white">✕ Reject Concession</button>
              </>
            )}
          </div>
        )}
        {(graphStatus === 'paused' || graphStatus === 'awaiting_webhook') && selectedGraph === 'renovation_permit_flow' && (
          <div className="flex flex-wrap gap-2 pt-1">
            {pendingHitl?.role_required === 'tenant' ? (
              <>
                <button onClick={() => handleWebhookResume('tenant_rating', 5)} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white">★★★★★ Rate 5 Stars (Complete)</button>
                <button onClick={() => handleWebhookResume('tenant_rating', 3)} className="text-xs px-3.5 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 font-semibold text-slate-200">★★★ Rate 3 Stars</button>
              </>
            ) : (
              <>
                <button onClick={() => handleWebhookResume('engineer_decision', 'APPROVED')} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-md shadow-emerald-600/30">✓ Approve Tender (Chief Engineer)</button>
                <button onClick={() => handleWebhookResume('engineer_decision', 'REJECTED')} className="text-xs px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 font-semibold text-white">✕ Reject → Re-tender Cycle</button>
              </>
            )}
          </div>
        )}
        {(graphStatus === 'paused' || graphStatus === 'awaiting_webhook') && selectedGraph === 'rent_arrears_settlement_flow' && (
          <div className="flex flex-wrap gap-2 pt-1">
            {pendingHitl?.role_required === 'legal_counsel' || pendingHitl?.role_required === 'finance_admin' ? (
              <>
                <button onClick={() => handleWebhookResume('counsel_decision', 'APPROVED')} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white shadow-md shadow-emerald-600/30">✓ Legal Counsel Sign-off</button>
                <button onClick={() => handleWebhookResume('counsel_decision', 'REJECTED')} className="text-xs px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 font-semibold text-white">✕ Request Amendment → ToT Cycle</button>
              </>
            ) : (
              <>
                <button onClick={() => handleWebhookResume('tenant_selection', 'A')} className="text-xs px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white">Accept Plan A (6-Month Installment)</button>
                <button onClick={() => handleWebhookResume('tenant_selection', 'B')} className="text-xs px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white">Accept Plan B (Unit Downsize)</button>
                <button onClick={() => handleWebhookResume('tenant_selection', 'REFUSE')} className="text-xs px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 font-semibold text-white">✕ Refuse All → Statutory Notice</button>
              </>
            )}
          </div>
        )}
      </section>

      {/* BOTTOM BOXES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-4 space-y-3">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2"><History className="w-4 h-4 text-violet-400" />Checkpoint Timeline {runId && <span className="text-[10px] text-slate-500">{checkpoints.length} steps</span>}</h3>
          <CheckpointTimeline checkpoints={checkpoints.length ? checkpoints : history.map((h: any) => ({ step: h.step, node: h.node, status: h.status, created_at: '', checkpoint_id: `h-${h.step}` }))} currentStep={history[history.length - 1]?.step} onSelect={handleSelectCheckpoint} onRollback={handleRollback} />
          {checkpoints.length >= 2 && (
            <div className="flex gap-2">
              <button onClick={() => handleDiff(checkpoints[0].step, checkpoints[checkpoints.length - 1].step)} className="text-[11px] px-2 py-1 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30">Diff first→last</button>
              <button onClick={() => checkpoints.length >= 2 && handleDiff(checkpoints[checkpoints.length - 2].step, checkpoints[checkpoints.length - 1].step)} className="text-[11px] px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">Diff last 2</button>
            </div>
          )}
        </div>

        <div className="glass-card p-4 space-y-2">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2"><Layers className="w-4 h-4 text-indigo-400" />Variables (editable, JSON)</h3>
          <textarea value={JSON.stringify(variables, null, 2)} onChange={e => { try { setVariables(JSON.parse(e.target.value)); } catch {} }} className="w-full h-48 p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-emerald-400 font-mono" />
        </div>

        <div className="glass-card p-4 space-y-2">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2"><Eye className="w-4 h-4 text-cyan-400" />Checkpoint Inspector</h3>
          {!inspector ? (
            <div className="text-xs text-slate-500 p-3 border border-dashed border-slate-800 rounded-xl">Click Inspect on a checkpoint step.</div>
          ) : (
            <div className="space-y-2">
              <div className="text-xs text-slate-300">Step {inspector.step} • {inspector.node} • {inspector.status_at_step}</div>
              <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono max-h-48 overflow-auto">{(JSON.stringify(inspector.state?.variables || inspector.state || inspector.values || inspector || {}, null, 2) || '').slice(0, 4000)}</pre>
              {diffData && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono">
                  <div className="font-bold text-slate-200 mb-1">Diff {diffData.from} → {diffData.to}</div>
                  <div className="text-emerald-400">+ added: {(JSON.stringify(diffData.added, null, 2) || '').slice(0, 800)}</div>
                  <div className="text-amber-400">~ modified: {(JSON.stringify(diffData.modified, null, 2) || '').slice(0, 800)}</div>
                  <div className="text-rose-400">- removed: {(diffData.removed || []).join(', ')}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="glass-card p-4 space-y-2">
        <h3 className="text-xs font-bold text-slate-300">Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500" />Running</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />HITL Pause</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500" />Webhook Wait</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Completed</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" />Ticket (failed)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-500" />Cycle (loop)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-rose-500" />Error branch</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-slate-500" />Normal</span>
        </div>
        <div className="text-[11px] text-slate-500">Vertical hierarchy (dagre TB) • Arrows bottom→top, cycles to right with amber dashed, errors rose • HITL vs Ticket distinct — Ticket persists to graph_failure_tickets, HITL to hitl_tasks</div>
      </div>
    </div>
  );
};
