/**
 * Collapsible Role-Gated Sidebar (platform/src/components/layout/Sidebar.tsx)
 */

import React from 'react';
import {
  Home,
  Building,
  BarChart3,
  Activity,
  LayoutDashboard,
  MessageSquare,
  GitBranch,
  ShieldCheck,
  Wrench,
  FileText,
  Sliders,
  LogIn,
} from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore, AppPage } from '../../stores/useAppStore';

export const Sidebar: React.FC = () => {
  const { isAuthenticated, role } = useAuthStore();
  const { currentPage, setCurrentPage, isSidebarOpen } = useAppStore();

  const navItem = (page: AppPage, label: string, Icon: React.ElementType, badge?: string) => {
    const isActive = currentPage === page;
    return (
      <button
        onClick={() => setCurrentPage(page)}
        className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
          isActive
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
        }`}
      >
        <div className="flex items-center space-x-3">
          <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
          {isSidebarOpen && <span>{label}</span>}
        </div>
        {isSidebarOpen && badge && (
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono border border-slate-700">
            {badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside
      className={`border-r border-slate-800/80 bg-slate-900/60 backdrop-blur-md flex flex-col justify-between p-3 transition-all duration-300 ${
        isSidebarOpen ? 'w-64' : 'w-16 items-center'
      }`}
    >
      <div className="space-y-6 w-full">
        {/* Public & Explore */}
        <div>
          {isSidebarOpen && (
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
              Explore & Public
            </div>
          )}
          <div className="space-y-1">
            {navItem('home', 'Overview & Home', Home)}
            {navItem('properties', 'Properties & Units', Building)}
            {navItem('showcase', 'Showcase & Benchmarks', BarChart3, 'AI')}
            {navItem('status', 'MCP Protocol Health', Activity)}
          </div>
        </div>

        {/* Authenticated Role Workspaces */}
        {isAuthenticated && (
          <div>
            {isSidebarOpen && (
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
                Workspace ({role.replace('_', ' ')})
              </div>
            )}
            <div className="space-y-1">
              {navItem('dashboard', 'Role Dashboard', LayoutDashboard)}
              {navItem('chat', 'Multi-Agent Chat Studio', MessageSquare, 'SSE')}
              {(role === 'property_manager' || role === 'executive_admin') &&
                navItem('stateGraph', 'State Graph Studio', GitBranch, 'Flow')}
              {role === 'executive_admin' &&
                navItem('admin', 'Admin Command Center', ShieldCheck, 'HITL')}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      {isSidebarOpen && (
        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/40 text-[11px] text-slate-400">
          <div className="font-semibold text-slate-300 mb-1">State Machine Active</div>
          <div className="text-[10px] text-slate-400">
            Graph 1 (Escrow), Graph 2 (Renovation), Graph 3 (Eviction)
          </div>
        </div>
      )}
    </aside>
  );
};
