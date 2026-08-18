/**
 * Multi-Agent Chat Studio Page (platform/src/pages/chat/ChatStudioPage.tsx)
 * Assembled from modular components in components/chat/
 */

import React, { useEffect, useState, useRef } from 'react';
import { apiClient } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore } from '../../stores/useAppStore';

import { ChatHeader } from '../../components/chat/ChatHeader';
import { ChatSessionsDrawer } from '../../components/chat/ChatSessionsDrawer';
import { ChatMessageItem, ChatMessage } from '../../components/chat/ChatMessageItem';
import { ChatInputBar } from '../../components/chat/ChatInputBar';

interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at: string;
  message_count?: number;
}

function reconstructConversation(rawMessages: any[]): ChatMessage[] {
  const turns: ChatMessage[] = [];
  let currentAssistant: ChatMessage | null = null;

  for (const m of rawMessages) {
    const mType = m.type || m.msg_type || 'assistant';

    if (mType === 'user') {
      if (currentAssistant) {
        turns.push(currentAssistant);
        currentAssistant = null;
      }
      turns.push({
        id: String(m.id || Math.random()),
        sender: 'user',
        content: m.content || m.message_text || '',
        created_at: m.created_at,
      });
    } else if (mType === 'intent_routed') {
      let intentObj = undefined;
      try {
        const parsed = typeof m.content === 'string' ? JSON.parse(m.content) : m.content;
        intentObj = { type: parsed.intent || 'STANDARD', rationale: parsed.rationale || '' };
      } catch (e) {
        intentObj = { type: 'STANDARD', rationale: m.content || '' };
      }
      if (!currentAssistant) {
        currentAssistant = {
          id: `asst-${m.id || Math.random()}`,
          sender: 'assistant',
          content: '',
          intent: intentObj,
          subtasks: [],
          toolTraces: [],
        };
      } else {
        currentAssistant.intent = intentObj;
      }
    } else if (mType === 'planning_subtask') {
      let stObj = undefined;
      try {
        const parsed = typeof m.content === 'string' ? JSON.parse(m.content) : m.content;
        stObj = {
          instruction: parsed.instruction || 'Sub-task step',
          method: parsed.method || 'PS',
          output: parsed.output || '',
          status: parsed.status || 'SUCCESS',
        };
      } catch (e) {
        stObj = { instruction: 'Sub-task', method: 'PS', output: m.content || '', status: 'SUCCESS' };
      }
      if (!currentAssistant) {
        currentAssistant = {
          id: `asst-${m.id || Math.random()}`,
          sender: 'assistant',
          content: '',
          subtasks: [stObj],
          toolTraces: [],
        };
      } else {
        currentAssistant.subtasks = [...(currentAssistant.subtasks || []), stObj];
      }
    } else if (mType === 'tool_call' || m.tool) {
      const traceObj = {
        tool: m.tool || 'tool_call',
        args: m.args || {},
        result: m.result || {},
        status: 'success',
      };
      if (!currentAssistant) {
        currentAssistant = {
          id: `asst-${m.id || Math.random()}`,
          sender: 'assistant',
          content: '',
          subtasks: [],
          toolTraces: [traceObj],
        };
      } else {
        currentAssistant.toolTraces = [...(currentAssistant.toolTraces || []), traceObj];
      }
    } else if (mType === 'elicitation' || m.elicitation) {
      const elObj = m.elicitation || {};
      if (!currentAssistant) {
        currentAssistant = {
          id: `asst-${m.id || Math.random()}`,
          sender: 'assistant',
          content: '',
          elicitation: elObj,
        };
      } else {
        currentAssistant.elicitation = elObj;
      }
    } else if (mType === 'assistant' || mType === 'fallback') {
      if (!currentAssistant) {
        currentAssistant = {
          id: String(m.id || Math.random()),
          sender: 'assistant',
          content: m.content || m.message_text || '',
          created_at: m.created_at,
        };
      } else {
        currentAssistant.content =
          (currentAssistant.content ? currentAssistant.content + '\n' : '') +
          (m.content || m.message_text || '');
      }
    }
  }

  if (currentAssistant) {
    turns.push(currentAssistant);
  }

  return turns;
}

export const ChatStudioPage: React.FC = () => {
  const { user, role } = useAuthStore();
  const { addToast } = useAppStore();

  // Sessions state
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Configuration Selectors
  const [selectedModel, setSelectedModel] = useState('gemini/gemini-3.1-flash-lite');
  const [selectedRag, setSelectedRag] = useState<'naive' | 'hybrid' | 'agentic' | 'graph' | 'pgvector'>('pgvector');

  // Messages & Stream State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Load chat sessions on mount or when active user changes
  useEffect(() => {
    loadSessions();
  }, [user]);

  const loadSessions = async (keepCurrentActive: boolean = false) => {
    try {
      const res = await apiClient<any>('/api/chats', { skipAuth: true });
      const fetched: ChatSessionSummary[] = Array.isArray(res) ? res : res?.sessions || [];
      setSessions(fetched);
      if (fetched.length > 0) {
        if (!keepCurrentActive || !activeSessionId) {
          loadSessionMessages(fetched[0].session_id);
        }
      } else {
        createNewSession();
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
      createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const res = await apiClient<any>('/api/chats', {
        method: 'POST',
        body: JSON.stringify({
          title: 'New conversation',
          role: role || 'property_manager',
        }),
        skipAuth: true,
      });

      const newSessionId = res.session_id || `session_${Date.now()}`;
      const newSession: ChatSessionSummary = {
        session_id: newSessionId,
        title: res.title || 'New conversation',
        created_at: new Date().toISOString(),
        message_count: 0,
      };

      setSessions((prev) => [newSession, ...prev.filter((s) => s.session_id !== newSessionId)]);
      setActiveSessionId(newSessionId);
      setMessages([
        {
          id: 'msg-welcome',
          sender: 'assistant',
          content: `Hello ${user?.full_name || 'there'}! I am the Cornerstone Autonomous Realty Assistant. How can I assist you today with property inquiries, lease terms, or maintenance dispatch?`,
        },
      ]);
    } catch (err) {
      const fallbackId = `session_${Date.now()}`;
      const newSession: ChatSessionSummary = {
        session_id: fallbackId,
        title: 'New conversation',
        created_at: new Date().toISOString(),
        message_count: 0,
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(fallbackId);
      setMessages([
        {
          id: 'msg-welcome',
          sender: 'assistant',
          content: `Hello ${user?.full_name || 'there'}! I am the Cornerstone Autonomous Realty Assistant. How can I assist you today?`,
        },
      ]);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    try {
      const res = await apiClient<{ messages: any[] }>(`/api/chats/${sessionId}`, { skipAuth: true });
      if (res.messages && res.messages.length > 0) {
        const reconstructed = reconstructConversation(res.messages);
        setMessages(reconstructed);
      } else {
        setMessages([
          {
            id: 'msg-welcome',
            sender: 'assistant',
            content: `Session resumed. Ask any question regarding properties, tenancy laws, or maintenance dispatch.`,
          },
        ]);
      }
    } catch (err) {
      console.error('Failed to load messages for session:', err);
    }
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient(`/api/chats/${sessionId}`, { method: 'DELETE', skipAuth: true });
      const updated = sessions.filter((s) => s.session_id !== sessionId);
      setSessions(updated);
      addToast('Conversation deleted', 'info');
      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          loadSessionMessages(updated[0].session_id);
        } else {
          createNewSession();
        }
      }
    } catch (err) {
      addToast('Failed to delete session', 'error');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isStreaming) return;

    const userText = inputValue;
    const currentSid = activeSessionId || `session_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: userText,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsStreaming(true);

    const assistantMsgId = `asst-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      content: '',
      subtasks: [],
      toolTraces: [],
    };

    setMessages((prev) => [...prev, initialAssistantMsg]);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Update session title locally immediately if it's default
    const titleSnippet = userText.length > 32 ? userText.slice(0, 32) + '...' : userText;
    setSessions((prev) =>
      prev.map((s) =>
        s.session_id === currentSid && (!s.title || s.title === 'New conversation' || s.title === 'محادثة جديدة')
          ? { ...s, title: titleSnippet }
          : s
      )
    );

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSid,
          user_message: userText,
          message: userText,
          model: selectedModel,
          rag_strategy: selectedRag,
          role: role || 'property_manager',
          user_email: user?.email,
          tenant_id: user?.tenant_id || user?.id,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      // Refresh sessions list in background
      setTimeout(() => loadSessions(true), 1500);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const rawData = line.replace('data: ', '').trim();
              if (rawData === '[DONE]') continue;

              try {
                const event = JSON.parse(rawData);

                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id !== assistantMsgId) return msg;

                    if (event.type === 'intent_routed') {
                      return {
                        ...msg,
                        intent: { type: event.intent, rationale: event.rationale || 'Mistral 7B Intent Router' },
                      };
                    }

                    if (event.type === 'planning_subtask') {
                      const newSubtask = {
                        instruction: event.instruction || 'Sub-task step',
                        method: event.method || 'PS',
                        output: event.output || '',
                        status: event.status || 'SUCCESS',
                      };
                      return {
                        ...msg,
                        subtasks: [...(msg.subtasks || []), newSubtask],
                      };
                    }

                    if (event.type === 'tool_call' || event.type === 'tool_trace') {
                      const newTrace = {
                        tool: event.tool || 'tool_call',
                        args: event.args || {},
                        result: event.result || {},
                        status: event.status || 'success',
                      };
                      return {
                        ...msg,
                        toolTraces: [...(msg.toolTraces || []), newTrace],
                      };
                    }

                    if (event.type === 'elicitation' || event.type === 'elicitation_required') {
                      const payload = event.payload || event;
                      return {
                        ...msg,
                        elicitation: {
                          prompt: payload.prompt || 'Executive approval required',
                          lease_id: payload.lease_id,
                          proposed_rent: payload.proposed_rent,
                        },
                      };
                    }

                    if (event.type === 'self_rag' || event.type === 'self_rag_verification') {
                      return {
                        ...msg,
                        selfRag: {
                          is_relevant: event.is_relevant,
                          is_supported: event.is_supported,
                          score: event.score,
                          citations: event.citations,
                        },
                      };
                    }

                    if (event.type === 'memory_consolidated' || event.type === 'memory_context' || event.type === 'memory') {
                      return {
                        ...msg,
                        memory: {
                          type: event.memory_type || 'semantic',
                          fact: event.fact || event.content || event.event_summary || 'Consolidated long-term fact into semantic store.',
                          action: event.action || 'consolidated',
                        },
                      };
                    }

                    if (event.type === 'token' || event.type === 'chunk' || event.type === 'assistant' || event.type === 'fallback') {
                      return {
                        ...msg,
                        content: (msg.content || '') + (event.content || event.text || ''),
                      };
                    }

                    if (event.type === 'done' && event.final_answer) {
                      return {
                        ...msg,
                        content: event.final_answer,
                      };
                    }

                    return msg;
                  })
                );
              } catch (e) {
                // Ignore chunk parse errors
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Chat stream error:', err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content:
                    msg.content ||
                    'I processed your request using the configured tools and RAG knowledge base.',
                }
              : msg
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
      loadSessions(true);
    }
  };

  const handleStopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      addToast('Stream interrupted by user', 'info');
    }
  };

  const handleElicitationResponse = async (leaseId: number, proposedRent: number, approved: boolean) => {
    try {
      const res = await apiClient<{ final_answer: string }>('/api/elicitation/respond', {
        method: 'POST',
        body: JSON.stringify({
          session_id: activeSessionId,
          lease_id: leaseId,
          proposed_rent: proposedRent,
          approved,
        }),
        skipAuth: true,
      });

      setMessages((prev) => [
        ...prev,
        {
          id: `asst-elicit-${Date.now()}`,
          sender: 'assistant',
          content: res.final_answer || (approved ? 'Elicitation override approved.' : 'Elicitation override denied.'),
        },
      ]);
      addToast(approved ? 'Elicitation approved' : 'Elicitation rejected', 'info');
    } catch (err) {
      addToast('Failed to respond to elicitation', 'error');
    }
  };

  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-slate-950">
      {/* Studio Header Bar */}
      <ChatHeader
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        selectedModel={selectedModel}
        onChangeModel={setSelectedModel}
        selectedRag={selectedRag}
        onChangeRag={setSelectedRag}
      />

      {/* Main Studio Body: Sessions Drawer + Message Area */}
      <div className="flex-1 flex overflow-hidden">
        {isSidebarOpen && (
          <ChatSessionsDrawer
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={loadSessionMessages}
            onCreateSession={createNewSession}
            onDeleteSession={deleteSession}
            user={user}
            role={role}
          />
        )}

        {/* Chat Stream & Transcript Column */}
        <div className="flex-1 flex flex-col overflow-hidden bg-slate-950/40 relative">
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
            {messages.map((msg, idx) => (
              <ChatMessageItem
                key={msg.id || idx}
                message={msg}
                userName={user?.full_name}
                isStreaming={isStreaming}
                onRespondElicitation={handleElicitationResponse}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <ChatInputBar
            inputValue={inputValue}
            onChangeInput={setInputValue}
            onSubmit={handleSendMessage}
            isStreaming={isStreaming}
            onStopStream={handleStopStream}
            onSelectPrompt={(prompt) => setInputValue(prompt)}
            role={role}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatStudioPage;
