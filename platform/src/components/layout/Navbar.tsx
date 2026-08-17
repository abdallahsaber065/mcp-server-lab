/**
 * Enterprise Navbar with Role Badge, Demo Quick-Switcher, and Navigation (platform/src/components/layout/Navbar.tsx)
 */

import React from 'react';
import {
  Building2,
  Shield,
  Layers,
  Activity,
  User,
  LogOut,
  Sparkles,
  Menu,
  ChevronDown,
} from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore, AppPage } from '../../stores/useAppStore';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, role, logout, quickLoginAs } = useAuthStore();
  const { currentPage, setCurrentPage, toggleSidebar, addToast } = useAppStore();
  const [showDemoMenu, setShowDemoMenu] = React.useState(false);

  const handleQuickSwitch = async (targetRole: 'executive_admin' | 'property_manager' | 'tenant') => {
    try {
      await quickLoginAs(targetRole);
      setShowDemoMenu(false);
      addToast(`Switched persona to ${targetRole.replace('_', ' ').toUpperCase()}`, 'success');
      setCurrentPage('dashboard');
    } catch {
      addToast('Failed to switch persona', 'error');
    }
  };

  const getRoleBadge = () => {
    switch (role) {
      case 'executive_admin':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">Executive Admin</span>;
      case 'property_manager':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Property Manager</span>;
      case 'tenant':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Tenant</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-300 border border-slate-600/50">Guest Visitor</span>;
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 px-4 flex items-center justify-between">
      {/* Brand & Sidebar Toggle */}
      <div className="flex items-center space-x-3">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div
          onClick={() => setCurrentPage('home')}
          className="flex items-center space-x-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-sm text-slate-100 tracking-tight flex items-center gap-1.5">
              CORNERSTONE <span className="text-indigo-400 font-mono text-xs px-1.5 py-0.2 bg-indigo-500/10 rounded border border-indigo-500/20">MCP 4.0</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium">Realty Autonomous Portal</div>
          </div>
        </div>
      </div>

      {/* Public Nav Links */}
      <nav className="hidden md:flex items-center space-x-1">
        <button
          onClick={() => setCurrentPage('home')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            currentPage === 'home' ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          Home
        </button>
        <button
          onClick={() => setCurrentPage('properties')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            currentPage === 'properties' ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          Properties & Units
        </button>
        <button
          onClick={() => setCurrentPage('showcase')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            currentPage === 'showcase' ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          Showcase & Benchmarks
        </button>
        <button
          onClick={() => setCurrentPage('status')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            currentPage === 'status' ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          System Health
        </button>
      </nav>

      {/* Auth & Demo Switcher */}
      <div className="flex items-center space-x-3">
        {/* 1-Click Demo Persona Switcher */}
        <div className="relative">
          <button
            onClick={() => setShowDemoMenu(!showDemoMenu)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 text-indigo-300 hover:border-indigo-500/40 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Switch Role</span>
            <ChevronDown className="w-3.5 h-3.5" />
          </button>

          {showDemoMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="text-[11px] font-semibold text-slate-400 px-2 py-1 uppercase tracking-wider">
                1-Click Persona Login
              </div>
              <button
                onClick={() => handleQuickSwitch('executive_admin')}
                className="w-full text-left px-2.5 py-2 rounded-lg text-xs text-rose-300 hover:bg-rose-500/10 flex items-center justify-between"
              >
                <span>Executive Admin</span>
                <Shield className="w-3.5 h-3.5 text-rose-400" />
              </button>
              <button
                onClick={() => handleQuickSwitch('property_manager')}
                className="w-full text-left px-2.5 py-2 rounded-lg text-xs text-indigo-300 hover:bg-indigo-500/10 flex items-center justify-between"
              >
                <span>Property Manager</span>
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
              </button>
              <button
                onClick={() => handleQuickSwitch('tenant')}
                className="w-full text-left px-2.5 py-2 rounded-lg text-xs text-emerald-300 hover:bg-emerald-500/10 flex items-center justify-between"
              >
                <span>Tenant (Tarek Mahdy)</span>
                <User className="w-3.5 h-3.5 text-emerald-400" />
              </button>
            </div>
          )}
        </div>

        {/* Current User Badge & Profile */}
        {isAuthenticated && user ? (
          <div className="flex items-center space-x-2.5 pl-2 border-l border-slate-800">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-xs font-medium text-slate-200">{user.full_name}</span>
              {getRoleBadge()}
            </div>
            <button
              onClick={() => {
                logout();
                addToast('Logged out successfully', 'info');
                setCurrentPage('home');
              }}
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
              title="Log Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setCurrentPage('login')}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all"
          >
            Sign In
          </button>
        )}
      </div>
    </header>
  );
};
