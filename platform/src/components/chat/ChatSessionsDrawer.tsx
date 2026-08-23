import React from 'react';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import { User, UserRole } from '../../types';

interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at: string;
  message_count?: number;
}

interface ChatSessionsDrawerProps {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  user: User | null;
  role: UserRole;
}

export const ChatSessionsDrawer: React.FC<ChatSessionsDrawerProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  user,
  role,
}) => {
  return (
    <div className="w-64 border-r border-slate-800/80 bg-slate-900/40 backdrop-blur-md flex flex-col justify-between shrink-0 p-3 select-none">
      <div className="space-y-3">
        <button
          onClick={onCreateSession}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-all hover:scale-[1.02] shadow-md shadow-indigo-600/10"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Conversation</span>
        </button>

        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">
          Chat History
        </div>

        <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-260px)] pr-1">
          {sessions.map((s) => (
            <div
              key={s.session_id}
              onClick={() => onSelectSession(s.session_id)}
              className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-all ${
                activeSessionId === s.session_id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-2 truncate">
                <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                <span className="truncate">{s.title || 'Conversation'}</span>
              </div>
              <button
                onClick={(e) => onDeleteSession(s.session_id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 transition-opacity"
                title="Delete Conversation"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Persona Details Strip in Sidebar Footer */}
      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 text-[11px]">
        <div className="text-slate-300 font-medium truncate">{user?.full_name || 'Active User'}</div>
        <div className="text-slate-500 font-mono text-[10px] truncate">{user?.email || 'user@realty.eg'}</div>
        <div className="text-indigo-400 font-semibold uppercase text-[9px]">
          {(role || 'property_manager').replace('_', ' ')}
        </div>
      </div>
    </div>
  );
};
