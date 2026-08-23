/**
 * Tenant Portal Dashboard (platform/src/pages/dashboard/TenantDashboard.tsx)
 * Features Lease Overview, Maintenance Work Orders, and AI Memory & Preferences (Episodic & Semantic)
 */

import React, { useEffect, useState } from 'react';
import {
  Home,
  FileText,
  Wrench,
  AlertCircle,
  CheckCircle2,
  DollarSign,
  Send,
  BrainCircuit,
  Sparkles,
  Clock,
  Tag,
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore } from '../../stores/useAppStore';

interface MemoryItem {
  category?: string;
  event_summary: string;
  timestamp?: string;
  version?: number;
  status?: string;
}

export const TenantDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { addToast } = useAppStore();
  const [lease, setLease] = useState<any>(null);
  const [maintenanceRequests, setMaintenanceRequests] = useState<any[]>([]);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [issueType, setIssueType] = useState('plumbing');
  const [priority, setPriority] = useState('medium');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function loadTenantData() {
      try {
        const leaseRes = await apiClient('/api/leases/me').catch(() => null);
        if (leaseRes?.lease) setLease(leaseRes.lease);

        const maintRes = await apiClient('/api/maintenance').catch(() => null);
        if (maintRes?.requests) setMaintenanceRequests(maintRes.requests);

        const tenantId = user?.tenant_id || 1;
        const memoryRes = await apiClient<any>(`/api/memory/${tenantId}`).catch(() => null);
        if (memoryRes?.memories) {
          setMemories(memoryRes.memories);
        }
      } catch (err) {
        console.error('Tenant data fetch error:', err);
      }
    }
    loadTenantData();
  }, [user]);

  const handleMaintenanceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    setIsSubmitting(true);
    try {
      await apiClient('/api/maintenance', {
        method: 'POST',
        body: JSON.stringify({
          unit_id: user?.assigned_unit_id || 1,
          issue_type: issueType,
          priority: priority,
          description: description,
        }),
      });
      addToast('Maintenance request submitted successfully', 'success');
      setDescription('');
      const maintRes = await apiClient('/api/maintenance');
      if (maintRes?.requests) setMaintenanceRequests(maintRes.requests);
    } catch (err: any) {
      addToast(err.message || 'Failed to submit maintenance request', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Welcome Banner */}
      <div className="glass-card p-6 bg-gradient-to-r from-emerald-950/40 via-slate-900/60 to-slate-900/80 border-emerald-500/20">
        <h1 className="text-xl font-bold text-slate-100">Welcome back, {user?.full_name}</h1>
        <p className="text-xs text-slate-400 mt-1">Tenant Portal • Unit {lease?.unit_number || '101-Garden'}</p>
      </div>

      {/* Lease & Payment Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Lease Overview */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span>Active Lease Agreement</span>
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
              Active
            </span>
          </div>

          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Property:</span>
              <span className="font-semibold">{lease?.property_name || 'Nile Plaza Luxury Residences'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Unit Number:</span>
              <span className="font-semibold">{lease?.unit_number || 'Unit 101-Garden'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Monthly Rent:</span>
              <span className="font-bold text-emerald-400">
                {lease?.monthly_rent ? `${Number(lease.monthly_rent).toLocaleString()} EGP` : '42,000 EGP'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Payment Status:</span>
              <span className="font-semibold text-emerald-400 capitalize">{lease?.payment_status || 'Current'}</span>
            </div>
          </div>
        </div>

        {/* Submit Repair Request */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-cyan-400" />
            <span>Submit Maintenance Work Order</span>
          </h2>

          <form onSubmit={handleMaintenanceSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Issue Category</label>
                <select
                  value={issueType}
                  onChange={(e) => setIssueType(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-slate-200"
                >
                  <option value="plumbing">Plumbing</option>
                  <option value="electrical">Electrical</option>
                  <option value="hvac">HVAC / AC</option>
                  <option value="structural">Structural</option>
                  <option value="general">General Repair</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-2.5 py-1.5 text-xs text-slate-200"
                >
                  <option value="emergency">🚨 Emergency</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Issue Description</label>
              <textarea
                rows={2}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the maintenance issue in detail..."
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-2.5 text-xs text-slate-200"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 flex items-center justify-center space-x-2"
            >
              <span>{isSubmitting ? 'Submitting...' : 'Submit Request'}</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* AI Memory & Preferences (Episodic & Consolidated Semantic Profile) */}
      <section className="glass-card p-6 space-y-4 border-purple-500/20 bg-gradient-to-b from-purple-950/10 via-slate-900/60 to-slate-900/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-purple-500/20 border border-purple-500/30 text-purple-300">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                <span>AI Memory & Personalization Profile</span>
                <span className="px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono border border-purple-500/30">
                  Week 3 Architecture
                </span>
              </h2>
              <p className="text-[11px] text-slate-400">
                Episodic historical events and consolidated semantic facts tailored to your tenancy.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-purple-400 font-semibold">
            {memories.length} Recorded Memories
          </span>
        </div>

        {memories.length === 0 ? (
          <div className="text-xs text-slate-400 italic p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center">
            No long-term memories or preferences recorded yet. The agent learns from your conversations and maintenance requests automatically.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {memories.map((m, idx) => {
              const isEpisodic = m.category === 'episodic';
              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border space-y-2 transition-all ${
                    isEpisodic
                      ? 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      : 'bg-purple-950/20 border-purple-500/30 hover:border-purple-500/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase tracking-wider border ${
                        isEpisodic
                          ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
                          : 'bg-purple-500/20 text-purple-300 border-purple-500/30'
                      }`}
                    >
                      {isEpisodic ? 'Episodic Event' : `Semantic Fact · ${m.category}`}
                    </span>
                    {m.timestamp && (
                      <span className="text-[10px] text-slate-500 flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(m.timestamp).toLocaleDateString()}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans">{m.event_summary}</p>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Repair Tickets History */}
      <section className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-bold text-slate-100">My Maintenance Work Orders</h2>
        {maintenanceRequests.length === 0 ? (
          <div className="text-xs text-slate-400">No maintenance tickets filed for this unit.</div>
        ) : (
          <div className="space-y-2">
            {maintenanceRequests.map((req) => (
              <div
                key={req.request_id}
                className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200 capitalize">
                    {req.issue_type} Repair — Unit {req.unit_number}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{req.description}</div>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-medium capitalize border ${
                    req.status === 'resolved'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      : req.status === 'in_progress'
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                      : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                  }`}
                >
                  {req.status?.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default TenantDashboard;
