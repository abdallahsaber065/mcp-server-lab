/**
 * Enterprise Navigation Sidebar (platform/src/components/layout/Sidebar.tsx)
 * Fixed viewport height, role-gated navigation, glassmorphism design tokens,
 * and integrated persona status footer.
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
  User,
  LogOut,
  Radio,
  Sparkles,
  ChevronRight,
  LogIn,
} from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore, AppPage } from '../../stores/useAppStore';

export const Sidebar: React.FC = () => {
  const { user, isAuthenticated, role, logout } = useAuthStore();
  const { currentPage, setCurrentPage, isSidebarOpen, addToast } = useAppStore();

  const getRoleBadgeStyle = (r: string) => {
    switch (r) {
      case 'executive_admin':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'property_manager':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'tenant':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const navItem = (page: AppPage, label: string, Icon: React.ElementType, badge?: string) => {
    const isActive = currentPage === page;
    return (
      <button
        key={page}
        onClick={() => setCurrentPage(page)}
        className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
          isActive
            ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-600/25 border border-indigo-500/40 font-semibold'
            : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 hover:translate-x-0.5'
        }`}
        title={!isSidebarOpen ? label : undefined}
      >
        <div className="flex items-center space-x-3 min-w-0">
          <Icon
            className={`w-4 h-4 shrink-0 transition-colors ${
              isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
            }`}
          />
          {isSidebarOpen && <span className="truncate">{label}</span>}
        </div>
        {isSidebarOpen && badge && (
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono tracking-tight shrink-0 border ${
              isActive
                ? 'bg-white/20 text-white border-white/30'
                : 'bg-slate-800/80 text-slate-400 border-slate-700/80 group-hover:border-slate-600 group-hover:text-slate-300'
            }`}
          >
            {badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside
      className={`h-full shrink-0 border-r border-slate-800/80 bg-slate-900/80 backdrop-blur-xl flex flex-col justify-between p-3.5 z-30 transition-all duration-300 ease-in-out select-none ${
        isSidebarOpen ? 'w-64' : 'w-18 items-center px-2'
      }`}
    >
      {/* Top Navigation Links */}
      <div className="space-y-6 w-full overflow-y-auto pr-0.5 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:bg-slate-800">
        {/* Public Exploration Section */}
        <div>
          {isSidebarOpen && (
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-3 mb-2 flex items-center justify-between">
              <span>Explore & Platform</span>
            </div>
          )}
          <div className="space-y-1">
            {navItem('home', 'Overview & Home', Home)}
            {navItem('properties', 'Properties & Units', Building)}
            {navItem('showcase', 'Showcase & Benchmarks', BarChart3, 'AI')}
            {navItem('status', 'MCP Protocol Health', Activity)}
          </div>
        </div>

        {/* Authenticated Workspace Section */}
        {isAuthenticated && (
          <div>
            {isSidebarOpen && (
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-3 mb-2 flex items-center justify-between">
                <span>Workspace</span>
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded-full border capitalize font-normal ${getRoleBadgeStyle(
                    role
                  )}`}
                >
                  {role.replace('_', ' ')}
                </span>
              </div>
            )}
            <div className="space-y-1">
              {navItem('dashboard', 'Role Dashboard', LayoutDashboard)}
              {navItem('chat', 'Multi-Agent Chat Studio', MessageSquare, 'SSE')}
              {navItem('stateGraph', 'State Graph Studio', GitBranch, 'Flow')}
              {navItem('admin', 'My Tasks & Reviews', ShieldCheck, role === 'executive_admin' ? 'HITL' : 'Review')}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Footer: User Status & Telemetry */}
      <div className="w-full pt-3 mt-auto border-t border-slate-800/80 space-y-2.5 shrink-0">
        {isAuthenticated && user ? (
          <div
            className={`p-2 rounded-xl bg-slate-800/40 border border-slate-700/40 transition-all ${
              isSidebarOpen ? 'flex items-center justify-between' : 'flex flex-col items-center justify-center'
            }`}
          >
            <div className="flex items-center space-x-2.5 min-w-0">
              <div className="relative">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-indigo-600/20 shrink-0">
                  {(user.full_name || 'U').charAt(0)}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 border-2 border-slate-900 rounded-full animate-pulse" />
              </div>
              {isSidebarOpen && (
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-slate-200 truncate">{user.full_name}</div>
                  <div className="text-[10px] text-slate-400 truncate">{user.email}</div>
                </div>
              )}
            </div>

            <button
              onClick={() => {
                logout();
                addToast('Signed out successfully', 'info');
                setCurrentPage('home');
              }}
              className={`p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors ${
                !isSidebarOpen ? 'mt-1.5' : ''
              }`}
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setCurrentPage('login')}
            className={`w-full flex items-center justify-center rounded-xl text-xs font-semibold bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 transition-all ${
              isSidebarOpen ? 'space-x-2 px-3 py-2' : 'p-2'
            }`}
            title="Sign In / Personas"
          >
            <LogIn className="w-3.5 h-3.5" />
            {isSidebarOpen && <span>Sign In / Personas</span>}
          </button>
        )}

        {/* Live MCP Gateway Status Indicator */}
        {isSidebarOpen ? (
          <div className="px-2 py-1 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-slate-400">MCP Gateway 4.0</span>
            </div>
            <span className="text-indigo-400/80">Online</span>
          </div>
        ) : (
          <div className="flex justify-center py-1" title="MCP Gateway 4.0 Online">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
