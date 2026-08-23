/**
 * Authentication Page with Sign In, Create Account (Register), & 1-Click Personas
 * (platform/src/pages/auth/LoginPage.tsx)
 */

import React, { useState } from 'react';
import { Lock, Mail, Shield, User, Layers, ArrowRight, UserPlus, Phone } from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore } from '../../stores/useAppStore';

export const LoginPage: React.FC = () => {
  const [tab, setTab] = useState<'login' | 'register'>('login');

  // Sign In state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register state
  const [fullName, setFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regRole, setRegRole] = useState<'tenant' | 'property_manager'>('tenant');

  const [errorMsg, setErrorMsg] = useState('');
  const { login, register, quickLoginAs, isLoading } = useAuthStore();
  const { setCurrentPage, addToast } = useAppStore();

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    try {
      await login(email, password);
      addToast('Signed in successfully', 'success');
      setCurrentPage('dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid email or password.');
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    try {
      await register(fullName, regEmail, regPassword, regRole, regPhone || undefined);
      addToast(`Account created! Signed in as ${regRole.replace('_', ' ').toUpperCase()}`, 'success');
      setCurrentPage('dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed. Please try a different email.');
    }
  };

  const handleQuick = async (role: 'executive_admin' | 'property_manager' | 'tenant') => {
    setErrorMsg('');
    try {
      await quickLoginAs(role);
      addToast(`Signed in as ${role.replace('_', ' ').toUpperCase()}`, 'success');
      setCurrentPage('dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to authenticate quick persona.');
    }
  };

  return (
    <div className="max-w-md mx-auto py-8 space-y-6">
      {/* Auth Card */}
      <div className="glass-card p-8 space-y-6">
        <div className="text-center space-y-1.5">
          <h1 className="text-xl font-bold text-slate-100">
            {tab === 'login' ? 'Sign in to Cornerstone Portal' : 'Create a Live Test Account'}
          </h1>
          <p className="text-xs text-slate-400">
            {tab === 'login'
              ? 'Access role-tailored dashboards and autonomous AI agents'
              : 'Register a new profile for live multi-turn agent testing'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-xl bg-slate-950/80 p-1 border border-slate-800">
          <button
            type="button"
            onClick={() => {
              setTab('login');
              setErrorMsg('');
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              tab === 'login'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab('register');
              setErrorMsg('');
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              tab === 'register'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
            {errorMsg}
          </div>
        )}

        {tab === 'login' ? (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@cornerstonerealty.eg"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <span>{isLoading ? 'Signing In...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Dr. Sherif Mansour"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="sherif.mansour@example.com"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Role</label>
                <select
                  value={regRole}
                  onChange={(e) => setRegRole(e.target.value as any)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="tenant">Tenant</option>
                  <option value="property_manager">Property Manager</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Phone (Optional)</label>
                <div className="relative">
                  <Phone className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                  <input
                    type="tel"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    placeholder="+20 100 000 0000"
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-8 pr-2 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <UserPlus className="w-4 h-4" />
              <span>{isLoading ? 'Creating Account...' : 'Register & Enter Portal'}</span>
            </button>
          </form>
        )}
      </div>

      {/* 1-Click Demo Persona Launcher */}
      <div className="glass-card p-6 space-y-3 border-indigo-500/20">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          1-Click Evaluator Personas
        </div>
        <div className="space-y-2">
          <button
            onClick={() => handleQuick('executive_admin')}
            className="w-full p-3 rounded-xl bg-rose-950/30 hover:bg-rose-900/40 border border-rose-500/30 text-left flex items-center justify-between transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-rose-300">Executive Admin</div>
              <div className="text-[10px] text-slate-400">admin@cornerstonerealty.eg</div>
            </div>
            <Shield className="w-4 h-4 text-rose-400" />
          </button>

          <button
            onClick={() => handleQuick('property_manager')}
            className="w-full p-3 rounded-xl bg-indigo-950/30 hover:bg-indigo-900/40 border border-indigo-500/30 text-left flex items-center justify-between transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-indigo-300">Property Manager</div>
              <div className="text-[10px] text-slate-400">abdallahsaber065@gmail.com</div>
            </div>
            <Layers className="w-4 h-4 text-indigo-400" />
          </button>

          <button
            onClick={() => handleQuick('tenant')}
            className="w-full p-3 rounded-xl bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/30 text-left flex items-center justify-between transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-emerald-300">Tenant (Tarek Mahdy)</div>
              <div className="text-[10px] text-slate-400">tarek.mahdy@cairomed.org</div>
            </div>
            <User className="w-4 h-4 text-emerald-400" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
