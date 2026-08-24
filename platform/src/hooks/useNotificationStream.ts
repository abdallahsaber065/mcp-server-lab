import { useEffect, useRef } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { useAppStore } from '../stores/useAppStore';

export function useNotificationStream(enabled: boolean = true) {
  const { user, isAuthenticated } = useAuthStore();
  const { addToast, setCurrentPage } = useAppStore();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!enabled || !isAuthenticated || !user) return;

    const token = localStorage.getItem('cornerstone_access_token');
    if (!token) return;

    const controller = new AbortController();
    abortRef.current = controller;

    const connect = async () => {
      try {
        const res = await fetch('/api/notifications/stream', {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (!res.ok || !res.body) {
          setTimeout(connect, 5000);
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.replace('data: ', '').trim();
            if (!raw || raw === '[DONE]') continue;
            try {
              const evt = JSON.parse(raw);
              if (evt.type === 'hello') continue;
              if (evt.type === 'state_graph_update' || evt.type === 'state_graph_failed' || evt.type === 'state_graph_launching') {
                const dedupKey = `${evt.run_id || ''}:${evt.node || ''}:${evt.status || ''}`;
                const seenKey = `sg_seen_${dedupKey}`;
                if (sessionStorage.getItem(seenKey)) continue;
                sessionStorage.setItem(seenKey, '1');
                setTimeout(() => sessionStorage.removeItem(seenKey), 120000);
                const graphLabel = evt.graph_id || 'State Graph';
                const sessionId = evt.session_id;
                const runId = evt.run_id;
                const status = evt.status || evt.graph_status || 'update';
                const msg = evt.message ? ` — ${String(evt.message).slice(0, 160)}` : '';
                const toastMsg = `🔔 ${graphLabel} ${status}${msg} — click to open chat`;
                const onClick = () => {
                  if (sessionId) {
                    window.history.pushState({ page: 'chat' }, '', `/chat/${sessionId}`);
                    window.dispatchEvent(new PopStateEvent('popstate'));
                    setCurrentPage('chat' as any);
                    window.dispatchEvent(new CustomEvent('sg-notification-open', { detail: { sessionId, runId, graphId: evt.graph_id } }));
                  }
                };
                (addToast as any)(toastMsg, status === 'FAILED_TICKET' ? 'error' : status === 'PAUSED_HITL' || status === 'AWAITING_WEBHOOK' ? 'warning' : 'info', onClick);
                window.dispatchEvent(new CustomEvent('sg-notification', { detail: evt }));
                try {
                  const key = 'sg_notifications';
                  const existing = JSON.parse(localStorage.getItem(key) || '[]');
                  if (existing.some((e: any) => e.run_id === evt.run_id && e.node === evt.node && e.status === evt.status)) continue;
                  existing.unshift({ ...evt, receivedAt: new Date().toISOString() });
                  localStorage.setItem(key, JSON.stringify(existing.slice(0, 50)));
                } catch {}
              }
            } catch {}
          }
        }
      } catch (e: any) {
        if (e.name !== 'AbortError') {
          setTimeout(connect, 5000);
        }
      }
    };

    connect();

    return () => {
      controller.abort();
      abortRef.current = null;
    };
  }, [isAuthenticated, user?.id, enabled]);
}
