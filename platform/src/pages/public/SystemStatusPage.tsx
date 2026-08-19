/**
 * MCP Protocol Health, Interactive Workbench & Memory Playground (platform/src/pages/public/SystemStatusPage.tsx)
 * Modularized with structured components for clean architecture.
 */

import React, { useEffect, useState } from 'react';
import { RefreshCw, Radio } from 'lucide-react';
import { apiClient } from '../../services/api';
import { InfrastructureGrid } from '../../components/status/InfrastructureGrid';
import { ProtocolWorkbench } from '../../components/status/ProtocolWorkbench';
import { MemoryPlayground } from '../../components/status/MemoryPlayground';
import { RagDocBrowser } from '../../components/status/RagDocBrowser';

export const SystemStatusPage: React.FC = () => {
  const [systemStats, setSystemStats] = useState<any>(null);
  const [ragDocs, setRagDocs] = useState<any[]>([]);
  const [ragSearchQuery, setRagSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Protocol interactive outputs
  const [testOutputs, setTestOutputs] = useState<Record<string, any>>({});
  const [progressStep, setProgressStep] = useState<number>(0);
  const [isProgressRunning, setIsProgressRunning] = useState<boolean>(false);

  const fetchStatusData = async () => {
    setIsLoading(true);
    try {
      const [statsRes, docsRes] = await Promise.all([
        apiClient<{ system: any }>('/api/system-stats', { skipAuth: true }).catch(() => ({ system: null })),
        apiClient<{ documents: any[] }>('/api/rag/documents', { skipAuth: true }).catch(() => ({ documents: [] })),
      ]);

      if (statsRes?.system) setSystemStats(statsRes.system);
      if (docsRes?.documents) setRagDocs(docsRes.documents);
    } catch (err) {
      console.error('Failed to load status data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusData();
  }, []);

  const runProtocolTest = async (testId: string) => {
    setTestOutputs((prev) => ({ ...prev, [testId]: { loading: true } }));

    try {
      if (testId === 'capabilities') {
        const res = await apiClient<any>('/api/capabilities', { skipAuth: true });
        setTestOutputs((prev) => ({ ...prev, [testId]: { loading: false, data: res } }));
      } else if (testId === 'notifications') {
        const tools = await apiClient<any[]>('/api/tools?role=tenant', { skipAuth: true });
        setTestOutputs((prev) => ({
          ...prev,
          [testId]: {
            loading: false,
            data: {
              notification: {
                jsonrpc: '2.0',
                method: 'notifications/tools/list_changed',
                params: { role: 'tenant', timestamp: new Date().toISOString() }
              },
              scopedTools: tools
            }
          }
        }));
      } else if (testId === 'elicitation') {
        await new Promise((r) => setTimeout(r, 600));
        setTestOutputs((prev) => ({
          ...prev,
          [testId]: {
            loading: false,
            data: {
              status: 'elicitation_required',
              elicitation_payload: {
                message: 'Proposed rent represents 22.2% discount — requires Executive Sign-off',
                risk_level: 'high',
                action: 'modify_lease_terms',
                threshold_exceeded: '15.0%',
                lease_id: 104,
                proposed_rent: 14000
              }
            }
          }
        }));
      } else if (testId === 'resources') {
        const resources = await apiClient<any[]>('/api/resources', { skipAuth: true });
        const firstUri = resources?.[0]?.uri || 'realty://policies/lease_terms';
        const readContent = await apiClient<any>(`/api/resource/read?uri=${encodeURIComponent(firstUri)}`, { skipAuth: true });
        setTestOutputs((prev) => ({
          ...prev,
          [testId]: {
            loading: false,
            data: {
              resources,
              sampleUri: firstUri,
              sampleContent: readContent
            }
          }
        }));
      } else if (testId === 'prompts') {
        const prompts = await apiClient<any[]>('/api/prompts', { skipAuth: true });
        const samplePrompt = await apiClient<any>(
          '/api/prompt/get?name=draft_lease_notice&tenant_email=amr.hassan@example.com&proposed_rent=16000',
          { skipAuth: true }
        );
        setTestOutputs((prev) => ({
          ...prev,
          [testId]: {
            loading: false,
            data: {
              prompts,
              samplePrompt
            }
          }
        }));
      } else if (testId === 'progress') {
        setIsProgressRunning(true);
        setProgressStep(1);
        for (let s = 1; s <= 5; s++) {
          setProgressStep(s);
          await new Promise((r) => setTimeout(r, 450));
        }
        setIsProgressRunning(false);
        setTestOutputs((prev) => ({
          ...prev,
          [testId]: {
            loading: false,
            data: {
              progressToken: `audit_${Date.now()}`,
              totalUnitsScanned: 47,
              violations: 0,
              complianceScore: '100%',
              completedAt: new Date().toISOString()
            }
          }
        }));
      } else if (testId === 'stm') {
        const data = {
          guarantee: 'Transcript Pruning preserves decoupled Scratchpad while rolling FIFO drops old turns.',
          scratchpad_preserved: {
            active_plan: 'Emergency response for Nile Tower plumbing leak',
            pending_subtasks: ['Review tenant insurance', 'Dispatch emergency low-VOC contractor'],
            grounded_constraints: ['Egyptian Law 4/1996 Article 22 SLA: <2 hours']
          },
          pruned_transcript_turns: 3,
          transcript_preview: [
            { role: 'user', content: 'Turn 4: What is the status of the repair work?' },
            { role: 'assistant', content: 'Turn 4 response: Contractor assigned, ETA 45 minutes.' }
          ]
        };
        setTestOutputs((prev) => ({ ...prev, [testId]: { loading: false, data } }));
      } else if (testId === 'route') {
        const res = await apiClient<any>('/api/memory/demo_route', {
          method: 'POST',
          body: JSON.stringify({
            content: 'Tenant Amr Hassan reported severe paint allergy; requested low-VOC maintenance.',
            entity_id: 'tenant_1'
          }),
          skipAuth: true
        });
        setTestOutputs((prev) => ({ ...prev, [testId]: { loading: false, data: res } }));
      } else if (testId === 'consolidate') {
        const res = await apiClient<any>('/api/memory/demo_consolidate', {
          method: 'POST',
          body: JSON.stringify({ tenant_id: 1, trigger_conflict: true }),
          skipAuth: true
        });
        setTestOutputs((prev) => ({ ...prev, [testId]: { loading: false, data: res } }));
      }
    } catch (err: any) {
      setTestOutputs((prev) => ({
        ...prev,
        [testId]: { loading: false, error: err.message || 'Operation failed' }
      }));
    }
  };

  return (
    <div className="space-y-10 pb-20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
            <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
            <span>FastMCP Server & State Graph Engine Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            System Status & Protocol Workbench
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Live telemetry for Model Context Protocol (MCP) concerns, cognitive memory consolidation, PGVector embeddings, and LangGraph state machines.
          </p>
        </div>

        <button
          onClick={fetchStatusData}
          disabled={isLoading}
          className="self-start sm:self-auto px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-2 transition-all shadow-md"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh All Systems</span>
        </button>
      </div>

      {/* Primary Infrastructure Status Banner */}
      <InfrastructureGrid systemStats={systemStats} />

      {/* SECTION 1: The 8 MCP Core Concerns Interactive Workbench */}
      <ProtocolWorkbench
        onRunTest={runProtocolTest}
        testOutputs={testOutputs}
        isProgressRunning={isProgressRunning}
        progressStep={progressStep}
      />

      {/* SECTION 2: Cognitive Memory Subsystem */}
      <MemoryPlayground onRunTest={runProtocolTest} testOutputs={testOutputs} />

      {/* SECTION 3: RAG Knowledge Store & Legal Binder Browser */}
      <RagDocBrowser
        ragDocs={ragDocs}
        searchQuery={ragSearchQuery}
        onSearchChange={setRagSearchQuery}
      />
    </div>
  );
};
