import React, { useState } from 'react';
import { User, Bot, Copy, Check } from 'lucide-react';
import { IntentBadge } from './IntentBadge';
import { SubtaskCard } from './SubtaskCard';
import { ToolTraceCard } from './ToolTraceCard';
import { ElicitationCard } from './ElicitationCard';
import { SelfRagBadge } from './SelfRagBadge';
import { MemoryCard } from './MemoryCard';
import { RichContent } from '../common/RichContent';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
  intent?: {
    type: string;
    rationale: string;
  };
  subtasks?: Array<{
    instruction: string;
    method: string;
    output: string;
    status?: string;
  }>;
  toolTraces?: Array<{
    tool: string;
    args: any;
    result: any;
    status?: string;
  }>;
  elicitation?: {
    prompt: string;
    lease_id?: number;
    proposed_rent?: number;
  };
  selfRag?: {
    is_relevant?: boolean;
    is_supported?: boolean;
    score?: number;
    citations?: string[];
  };
  memory?: {
    type?: string;
    fact?: string;
    action?: string;
  };
}

interface ChatMessageItemProps {
  message: ChatMessage;
  userName?: string;
  isStreaming?: boolean;
  onRespondElicitation: (leaseId: number, proposedRent: number, approved: boolean) => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  userName,
  isStreaming,
  onRespondElicitation,
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in duration-200`}>
      <div
        className={`max-w-3xl w-full rounded-2xl p-4 sm:p-5 space-y-3.5 ${
          isUser
            ? 'bg-gradient-to-tr from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-600/20 ml-8 sm:ml-16'
            : 'bg-slate-900/80 border border-slate-800/80 text-slate-200 mr-8 sm:mr-16 shadow-xl shadow-black/20'
        }`}
      >
        {/* Message Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div className="flex items-center space-x-2">
            {isUser ? (
              <>
                <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                  <User className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-xs font-bold text-white">{userName || 'You'}</span>
              </>
            ) : (
              <>
                <div className="w-6 h-6 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shadow-sm">
                  <Bot className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-100">Cornerstone Autonomous Agent</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    MCP Gateway
                  </span>
                </div>
              </>
            )}
          </div>

          {!isUser && message.content && (
            <button
              onClick={handleCopy}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              title="Copy response"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>

        {/* Intent Router Badge (if present) */}
        {message.intent && <IntentBadge intent={message.intent} />}

        {/* Subtask Planning Cards (Week 4) */}
        {message.subtasks && message.subtasks.length > 0 && (
          <div className="space-y-2">
            {message.subtasks.map((st, i) => (
              <SubtaskCard key={i} subtask={st} />
            ))}
          </div>
        )}

        {/* Tool Execution Traces */}
        {message.toolTraces && message.toolTraces.length > 0 && (
          <div className="space-y-2">
            {message.toolTraces.map((trace, i) => (
              <ToolTraceCard key={i} trace={trace} />
            ))}
          </div>
        )}

        {/* Human Elicitation Card */}
        {message.elicitation && (
          <ElicitationCard
            elicitation={message.elicitation}
            onRespond={onRespondElicitation}
          />
        )}

        {/* Self-RAG Verification Badge */}
        {message.selfRag && <SelfRagBadge selfRag={message.selfRag} />}

        {/* Memory Consolidation Card */}
        {message.memory && <MemoryCard memory={message.memory} />}

        {/* Main Text Content */}
        {message.content ? (
          <RichContent content={message.content} />
        ) : isStreaming ? (
          <div className="text-xs sm:text-sm text-indigo-300 italic flex items-center space-x-2 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
            <span>Thinking and executing reasoning chain...</span>
          </div>
        ) : null}
      </div>
    </div>
  );
};
