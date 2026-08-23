/**
 * Enterprise Navbar with Role Badge, Demo Quick-Switcher, and Navigation (platform/src/components/layout/Navbar.tsx)
 */

import React from 'react';
import {
  Building2,
  Menu,
} from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore } from '../../stores/useAppStore';

export const Navbar: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const { currentPage, setCurrentPage, toggleSidebar } = useAppStore();

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

      {/* Auth Actions */}
      <div className="flex items-center space-x-3">
        {!isAuthenticated && (
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
