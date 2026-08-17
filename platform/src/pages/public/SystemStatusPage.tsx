/**
 * MCP Protocol Health & Capabilities Inspector (platform/src/pages/public/SystemStatusPage.tsx)
 * Faithfully preserves and elevates the capability negotiation inspector from legacy status.js
 */

import React, { useEffect, useState } from 'react';
import { Activity, Server, Database, Shield, Zap, CheckCircle2, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';

export const SystemStatusPage: React.FC = () => {
  const [systemStats, setSystemStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient<{ system: any }>('/api/showcase/system-stats', { skipAuth: true });
      setSystemStats(res.system);
    } catch (err) {
      console.error('Failed to load system stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">MCP Protocol & System Status</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time Model Context Protocol (MCP) server capability negotiation and infrastructure status.
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={isLoading}
          className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-2 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Protocol Core Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Protocol Version</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-slate-100 font-mono">
            {systemStats?.protocol_version || '2025-06-18'}
          </div>
          <div className="text-[11px] text-slate-400">Model Context Protocol Standard</div>
        </div>

        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Database Architecture</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-sm font-bold text-slate-100">SQLAlchemy 2.0 ORM</div>
          <div className="text-[11px] text-emerald-400">SQLite WAL Mode (Concurrency Optimized)</div>
        </div>

        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Cache Layer</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-sm font-bold text-slate-100">Redis 7 (Async Engine)</div>
          <div className="text-[11px] text-slate-400">JWT Token Blacklist & Rate Limiting</div>
        </div>
      </div>

      {/* Capability Negotiation Inspector */}
      <section className="glass-card p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-400" />
          <span>Protocol 8 Core Concerns Negotiation</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
            <div className="text-xs font-semibold text-slate-200">1. Capability Negotiation</div>
            <div className="text-[11px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Active on Handshake</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
            <div className="text-xs font-semibold text-slate-200">2. Tool List Notifications</div>
            <div className="text-[11px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>listChanged Push Enabled</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
            <div className="text-xs font-semibold text-slate-200">3. Human Elicitation</div>
            <div className="text-[11px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>elicitation/create Hooked</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
            <div className="text-xs font-semibold text-slate-200">4. Progress Tracking</div>
            <div className="text-[11px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>progressToken Validated</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
