/**
 * Executive Admin Operations Center (platform/src/pages/admin/AdminCenterPage.tsx)
 * Features: Dynamic Tool Matrix, HITL Review Queue, Failure Ticket Workbench, and RAG Ingestion.
 */

import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Sliders,
  AlertTriangle,
  FileCheck,
  Upload,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Layers,
  Wrench,
  Eye,
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { HITLDetailModal } from '../../components/admin/HITLDetailModal';

const ROLE_CONFIG: Record<string, { title: string; subtitle: string; icon: string; hitlFilter: (t: any) => boolean; ticketFilter: (t: any) => boolean }> = {
  accountant: {
    title: 'Accountant Verification Center',
    subtitle: 'راجع مطابقة إيصالات 144,000 ج.م مع استخراج Gemini Vision وأكّد وصول المبلغ — كل طلب يظهر كـ HITL حتى تأكيدك.',
    icon: 'accountant',
    hitlFilter: (t) => t.node?.includes('accountant') || t.node?.includes('verify_receipt'),
    ticketFilter: (t) => t.node?.includes('verify_receipt') || t.error_type?.includes('Duplicate'),
  },
  chief_engineer: {
    title: 'Engineering Command Center',
    subtitle: 'اعتمد أوامر الشغل >10,000 ج.م ومفاضلة LATS بين 3 مقاولين — القرار يحدد مسار التنفيذ أو إعادة المناقصة.',
    icon: 'engineer',
    hitlFilter: (t) => t.node?.includes('engineer'),
    ticketFilter: (t) => t.node?.includes('lats') || t.node?.includes('Contractor'),
  },
  legal_counsel: {
    title: 'Legal & Counsel Review Center',
    subtitle: 'راجع جدولة المتأخرات واعتمد التسوية — القرار القانوني يفعّل الجدول أو يعيد ToT.',
    icon: 'legal',
    hitlFilter: (t) => t.node?.includes('counsel'),
    ticketFilter: (t) => t.graph_id?.includes('arrears'),
  },
  finance_officer: {
    title: 'Finance & Treasury Center',
    subtitle: 'دقّق الدفعات والضمانات المالية — نفس طابور المحاسب والقانوني للعرض التوضيحي.',
    icon: 'finance',
    hitlFilter: (t) => t.node?.includes('counsel') || t.node?.includes('accountant'),
    ticketFilter: () => true,
  },
  executive_admin: {
    title: 'Executive Governance Command Center',
    subtitle: 'Sign off on commercial lease discounts, dynamically manage MCP tool permissions, and inspect failure recovery tickets.',
    icon: 'executive',
    hitlFilter: (t) => t.node?.includes('await_bank') || t.node?.includes('execute') || t.node?.includes('counsel') || t.node?.includes('engineer') || t.node?.includes('accountant'),
    ticketFilter: () => true,
  },
  property_manager: {
    title: 'Property Manager Operations Center',
    subtitle: 'تابع الصيانة والمناقصات والحجوزات — نفس لوحة المهندس للعرض.',
    icon: 'manager',
    hitlFilter: (t) => t.node?.includes('engineer') || t.node?.includes('tenant_completion'),
    ticketFilter: (t) => t.graph_id?.includes('renovation') || t.graph_id?.includes('maintenance'),
  },
  site_supervisor: {
    title: 'Site Supervisor — Tickets & Dispatch',
    subtitle: 'تابع تذاكر فشل المقاولين وإعادة التوجيه الميداني.',
    icon: 'site',
    hitlFilter: () => false,
    ticketFilter: () => true,
  },
};

export const AdminCenterPage: React.FC = () => {
  const { addToast } = useAppStore();
  const { user } = useAuthStore();
  const role = (user?.role as string) || 'executive_admin';
  const cfg = ROLE_CONFIG[role] || ROLE_CONFIG.executive_admin;

  const getInitialTab = (): 'hitl' | 'tools' | 'tickets' | 'rag' => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('tab');
    if (t === 'hitl' || t === 'tools' || t === 'tickets' || t === 'rag') {
      return t;
    }
    return 'hitl';
  };

  const [activeTab, setActiveTabState] = useState<'hitl' | 'tools' | 'tickets' | 'rag'>(getInitialTab);

  const setActiveTab = (tab: 'hitl' | 'tools' | 'tickets' | 'rag') => {
    setActiveTabState(tab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.replaceState(null, '', url.toString());
  };

  // HITL State
  const [hitlTasks, setHitlTasks] = useState<any[]>([]);
  const [selectedTask, setSelectedTask] = useState<any>(null);

  // Tool Matrix State
  const [selectedAgent, setSelectedAgent] = useState('commercial_lease_agent');
  const [agentTools, setAgentTools] = useState<any[]>([]);

  // Failure Tickets State
  const [tickets, setTickets] = useState<any[]>([]);

  // RAG Ingestion State
  const [docId, setDocId] = useState('');
  const [docTitle, setDocTitle] = useState('');
  const [docCategory, setDocCategory] = useState('policy');
  const [docContent, setDocContent] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);

  const loadHITLTasks = async () => {
    try {
      const res = await apiClient('/api/admin/hitl/tasks');
      setHitlTasks(res.tasks || []);
    } catch (err) {
      console.error('Failed to load HITL tasks:', err);
    }
  };

  const loadTools = async (agentId: string) => {
    try {
      const res = await apiClient(`/api/admin/agents/${agentId}/tools`);
      setAgentTools(res.tools || []);
    } catch (err) {
      console.error('Failed to load agent tools:', err);
    }
  };

  const loadTickets = async () => {
    try {
      const res = await apiClient('/api/admin/tickets');
      setTickets(res.tickets || []);
    } catch (err) {
      console.error('Failed to load failure tickets:', err);
    }
  };

  useEffect(() => {
    loadHITLTasks();
    loadTools(selectedAgent);
    loadTickets();
  }, [selectedAgent]);

  const visibleHitl = hitlTasks.filter(cfg.hitlFilter);
  const visibleTickets = tickets.filter(cfg.ticketFilter);
  const isAdmin = role === 'executive_admin';
  useEffect(() => {
    if (!isAdmin && (activeTab === 'tools' || activeTab === 'rag')) setActiveTab('hitl');
  }, [isAdmin, activeTab]);

  const handleResolveHITL = async (taskId: string, decision: 'approved' | 'rejected') => {
    try {
      await apiClient(`/api/admin/hitl/tasks/${taskId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({
          decision,
          notes: `Executive sign-off ${decision} via Admin Command Center.`,
        }),
      });
      addToast(`HITL Task ${taskId} ${decision} successfully`, 'success');
      loadHITLTasks();
    } catch (err: any) {
      addToast(err.message || 'Failed to resolve HITL task', 'error');
    }
  };

  const handleToggleTool = async (toolName: string, isEnabled: boolean) => {
    try {
      await apiClient(`/api/admin/agents/${selectedAgent}/tools/toggle`, {
        method: 'POST',
        body: JSON.stringify({
          tool_name: toolName,
          is_enabled: !isEnabled,
        }),
      });
      addToast(`Tool '${toolName}' ${!isEnabled ? 'enabled' : 'disabled'} (MCP listChanged emitted)`, 'success');
      loadTools(selectedAgent);
    } catch (err: any) {
      addToast(err.message || 'Failed to toggle tool', 'error');
    }
  };

  const handleResolveTicket = async (ticketId: string) => {
    try {
      await apiClient(`/api/admin/tickets/${ticketId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ notes: 'Manually verified and unblocked.' }),
      });
      addToast(`Ticket ${ticketId} resolved`, 'success');
      loadTickets();
    } catch (err: any) {
      addToast(err.message || 'Failed to resolve ticket', 'error');
    }
  };

  const handleIngestRAG = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docId || !docTitle || !docContent) return;
    setIsIngesting(true);
    try {
      await apiClient('/api/admin/rag/documents', {
        method: 'POST',
        body: JSON.stringify({
          doc_id: docId,
          title: docTitle,
          category: docCategory,
          content: docContent,
        }),
      });
      addToast('Document successfully indexed into Vector Store', 'success');
      setDocId('');
      setDocTitle('');
      setDocContent('');
    } catch (err: any) {
      addToast(err.message || 'Failed to ingest document', 'error');
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header — role-aware */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-rose-400" />
          <span>{cfg.title}</span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">{role}</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1" dir={role === 'accountant' || role === 'chief_engineer' || role === 'legal_counsel' ? 'rtl' : undefined}>{cfg.subtitle}</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-2">
        <button
          onClick={() => setActiveTab('hitl')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
            activeTab === 'hitl'
              ? 'border-amber-400 text-amber-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          <span>HITL Queue ({hitlTasks.filter(cfg.hitlFilter).length}/{hitlTasks.length})</span>
        </button>

        {isAdmin && (
          <button
            onClick={() => setActiveTab('tools')}
            className={`px-4 py-2.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === 'tools' ? 'border-indigo-400 text-indigo-300' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Dynamic Tool Matrix</span>
          </button>
        )}

        <button
          onClick={() => setActiveTab('tickets')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
            activeTab === 'tickets'
              ? 'border-rose-400 text-rose-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Failure Tickets ({visibleTickets.length}/{tickets.length})</span>
        </button>

        {isAdmin && (
          <button
            onClick={() => setActiveTab('rag')}
            className={`px-4 py-2.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === 'rag' ? 'border-cyan-400 text-cyan-300' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>RAG Policy Ingestion</span>
          </button>
        )}
      </div>

      {/* Tab 1: HITL Review Queue — role-filtered */}
      {activeTab === 'hitl' && (
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-100">{role === 'accountant' ? 'مهام المحاسب — تأكيد الإيصالات' : role === 'chief_engineer' ? 'مهام المهندس — اعتماد أوامر الشغل' : role === 'legal_counsel' ? 'مهام القانوني — اعتماد الجدولة' : 'Pending Sign-offs'}</h2>
            <button
              onClick={loadHITLTasks}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          {visibleHitl.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-950/40 rounded-xl">
              No tasks currently awaiting review for your role ({role}).
            </div>
          ) : (
            <div className="space-y-4">
              {visibleHitl.map((task) => (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className="p-4 rounded-xl bg-slate-950/60 border border-amber-500/30 flex flex-wrap items-center justify-between gap-4 cursor-pointer hover:border-amber-500/50 hover:bg-slate-900/60 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-100">Task {task.task_id}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">
                        Node: {task.node}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300">{task.reason}</div>
                    <div className="text-[11px] text-slate-400 font-mono">Run: {task.run_id}</div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); setSelectedTask(task); }}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View & Edit</span>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleResolveHITL(task.task_id, 'approved'); }}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center space-x-1 shadow-md shadow-emerald-600/20"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleResolveHITL(task.task_id, 'rejected'); }}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white flex items-center space-x-1"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Dynamic Tool Matrix - admin only */}
      {isAdmin && activeTab === 'tools' && (
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100">Dynamic MCP Tool Permissions Matrix</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Toggle tool access per persona in real-time. Emits MCP notifications/tools/list_changed.
              </p>
            </div>

            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200"
            >
              <option value="commercial_lease_agent">Commercial Lease Agent</option>
              <option value="maintenance_dispatch_agent">Maintenance Dispatch Agent</option>
              <option value="autonomous_realty_agent">Autonomous Realty Master Agent</option>
              <option value="tenant_concierge">Tenant Concierge</option>
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {agentTools.map((tool) => (
              <div
                key={tool.name}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-bold text-slate-200 font-mono">{tool.name}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{tool.description}</div>
                </div>
                <button
                  onClick={() => handleToggleTool(tool.name, tool.is_enabled)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                    tool.is_enabled
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-slate-800 text-slate-500 border border-slate-700'
                  }`}
                >
                  {tool.is_enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Failure Tickets — role-filtered */}
      {activeTab === 'tickets' && (
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-base font-bold text-slate-100">State Graph Node Failure Tickets {visibleTickets.length !== tickets.length && <span className="text-xs text-slate-400">({visibleTickets.length}/{tickets.length} لدورك)</span>}</h2>
          {visibleTickets.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-950/40 rounded-xl">
              {tickets.length === 0 ? 'Zero active failure tickets. All nodes operating cleanly!' : 'لا توجد تذاكر لدورك — التذاكر الحالية تخص أدوارًا أخرى.'}
            </div>
          ) : (
            <div className="space-y-3">
              {visibleTickets.map((t) => (
                <div
                  key={t.ticket_id}
                  className="p-4 rounded-xl bg-slate-950/60 border border-rose-500/30 flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-bold text-rose-300">
                      {t.error_type} in node: {t.node}
                    </div>
                    <div className="text-[11px] text-slate-300 mt-0.5">{t.message}</div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">Ticket ID: {t.ticket_id}</div>
                  </div>
                  {t.status === 'open' && (
                    <button
                      onClick={() => handleResolveTicket(t.ticket_id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md"
                    >
                      Resolve & Resume
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: RAG Ingestion - admin only */}
      {isAdmin && activeTab === 'rag' && (
        <div className="glass-card p-6 space-y-4 max-w-2xl">
          <h2 className="text-base font-bold text-slate-100">Ingest Regulatory Document / Bylaw</h2>
          <form onSubmit={handleIngestRAG} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Document Identifier</label>
                <input
                  type="text"
                  required
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  placeholder="DOC-LAW-4-1996"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-2 text-xs text-slate-200"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="Egyptian Real Estate Law 4/1996"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-2 text-xs text-slate-200"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Document Text Body</label>
              <textarea
                rows={4}
                required
                value={docContent}
                onChange={(e) => setDocContent(e.target.value)}
                placeholder="Paste full text or regulatory clause..."
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-2.5 text-xs text-slate-200"
              />
            </div>

            <button
              type="submit"
              disabled={isIngesting}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white flex items-center space-x-2"
            >
              <span>{isIngesting ? 'Indexing...' : 'Index into Vector Store'}</span>
              <Upload className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
      <HITLDetailModal task={selectedTask} onClose={() => setSelectedTask(null)} onResolved={loadHITLTasks} />
    </div>
  );
};
