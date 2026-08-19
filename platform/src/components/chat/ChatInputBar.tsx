import React from 'react';
import { Send, StopCircle, Sparkles } from 'lucide-react';
import { UserRole } from '../../types';

interface ChatInputBarProps {
  inputValue: string;
  onChangeInput: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isStreaming: boolean;
  onStopStream: () => void;
  onSelectPrompt?: (prompt: string) => void;
  role?: UserRole;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  inputValue,
  onChangeInput,
  onSubmit,
  isStreaming,
  onStopStream,
  onSelectPrompt,
  role = 'property_manager',
}) => {
  const getQuickPrompts = () => {
    switch (role) {
      case 'tenant':
        return [
          'What are my active lease terms and monthly rent?',
          'Submit repair request for kitchen plumbing leak',
          'Check building quiet hours and guest rules',
          'Lookup available 2-bedroom units in Cairo',
        ];
      case 'executive_admin':
        return [
          'Run portfolio occupancy and revenue audit',
          'Review pending high-value lease concessions',
          'Simulate multi-unit eviction & escrow state graph',
          'Emergency structural facade repair escalation',
        ];
      case 'property_manager':
      default:
        return [
          'Audit compliance for Property #1',
          'Lookup available 2-bedroom units in Cairo',
          'Emergency plumbing burst at Nile Tower',
          'Modify lease terms for Unit 101 rent discount',
        ];
    }
  };

  const quickPrompts = getQuickPrompts();

  return (
    <div className="p-3 sm:p-4 border-t border-slate-800/80 bg-slate-900/70 backdrop-blur-md shrink-0 space-y-2.5">
      {/* Quick Prompt Chips */}
      {onSelectPrompt && (
        <div className="max-w-4xl mx-auto flex items-center gap-1.5 overflow-x-auto pb-1 text-slate-400 text-[11px] no-scrollbar">
          <div className="flex items-center space-x-1 text-[10px] uppercase font-bold text-indigo-400 shrink-0 mr-1">
            <Sparkles className="w-3 h-3" />
            <span>{role?.replace('_', ' ')} Prompts:</span>
          </div>
          {quickPrompts.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectPrompt(q)}
              className="px-2.5 py-1 rounded-lg bg-slate-800/70 hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-200 border border-slate-700/60 hover:border-indigo-500/40 transition-all text-left truncate shrink-0 text-[11px]"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={onSubmit} className="max-w-4xl mx-auto flex items-end space-x-3">
        <textarea
          rows={Math.min(4, Math.max(1, inputValue.split('\n').length))}
          value={inputValue}
          onChange={(e) => onChangeInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (inputValue.trim() && !isStreaming) {
                onSubmit(e);
              }
            }
          }}
          placeholder={`Ask anything as ${role?.replace('_', ' ')} (e.g. units, lease terms, audits)...`}
          disabled={isStreaming}
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950/90 border border-slate-700/80 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-all resize-none leading-relaxed"
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onStopStream}
            className="px-4 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-rose-600/30 transition-all shrink-0"
            title="Interrupt Generation"
          >
            <StopCircle className="w-4 h-4 animate-pulse" />
            <span>Stop</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-indigo-600/30 border border-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        )}
      </form>
    </div>
  );
};
