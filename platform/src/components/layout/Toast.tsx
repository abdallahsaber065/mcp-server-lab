/**
 * Toast Notification Container (platform/src/components/layout/Toast.tsx)
 */

import React from 'react';
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from 'lucide-react';
import { useAppStore, ToastMessage } from '../../stores/useAppStore';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useAppStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          onClick={() => toast.onClick?.()}
          className={`pointer-events-auto flex items-center justify-between p-3.5 rounded-xl shadow-2xl border backdrop-blur-lg animate-in slide-in-from-bottom-2 fade-in transition-all cursor-pointer hover:scale-[1.02] ${
            toast.type === 'success'
              ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
              : toast.type === 'error'
              ? 'bg-rose-950/90 border-rose-500/40 text-rose-200'
              : toast.type === 'warning'
              ? 'bg-amber-950/90 border-amber-500/40 text-amber-200'
              : 'bg-slate-900/90 border-slate-700 text-slate-200'
          } ${toast.onClick ? 'hover:ring-1 hover:ring-white/20' : ''}`}
          title={toast.onClick ? 'Click to open chat' : undefined}
        >
          <div className="flex items-center space-x-2.5">
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            {toast.type === 'error' && <XCircle className="w-4 h-4 text-rose-400" />}
            {toast.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
            {toast.type === 'info' && <Info className="w-4 h-4 text-cyan-400" />}
            <span className="text-xs font-medium">{toast.message}</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); removeToast(toast.id); }}
            className="p-1 rounded text-slate-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
