/**
 * Cornerstone Realty — MCP Autonomous Portal Client Logic (v3.9.0)
 * Stable Tool Cards: data-attr toggle, no inline display fighting CSS
 */

const AVAILABLE_MODELS = [
  "gemini/gemini-3.1-flash-lite",
  "gemini/gemini-3.5-flash",
  "gemini/gemini-2.5-flash",
  "gemini/gemini-2.5-flash-lite",
  "gemini/gemma-4-26b-a4b-it",
  "mistral/mistral-small-latest",
  "mistral/open-mistral-7b",
  "mistral/open-mixtral-8x7b",
  "mistral/codestral-latest",
  "mistral/mistral-large-latest"
];

let activeSessionId = localStorage.getItem('cornerstone_active_session_id') || null;

function initModelDropdown() {
  const select = document.getElementById('modelSelect');
  if (!select) return;
  select.innerHTML = '';
  AVAILABLE_MODELS.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.innerText = m;
    if (m === 'gemini/gemini-2.5-flash') opt.selected = true;
    select.appendChild(opt);
  });
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function detectTextDirection(htmlOrText) {
  if (!htmlOrText) return '';
  const clean = htmlOrText.replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ');
  const latinMatches = clean.match(/[a-zA-Z]/g) || [];
  const arabicMatches = clean.match(/[\u0600-\u06FF]/g) || [];
  if (latinMatches.length > arabicMatches.length && latinMatches.length > 5) {
    return 'dir-ltr';
  }
  return '';
}

// --- CHAT SESSION MANAGEMENT ---

async function fetchChatSessions() {
  try {
    const res = await fetch('/api/chats');
    const sessions = await res.json();
    renderSessionListDOM(sessions);

    if (sessions.length > 0) {
      const existing = sessions.find(s => s.session_id === activeSessionId);
      await loadChatSession(existing ? existing.session_id : sessions[0].session_id);
    } else {
      await createNewChatSession();
    }
  } catch (err) {
    console.error("Failed to fetch chat sessions:", err);
  }
}

async function createNewChatSession() {
  const role = document.getElementById('roleSelect')?.value || 'property_manager';
  try {
    const res = await fetch('/api/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: "محادثة جديدة", role: role })
    });
    const session = await res.json();
    activeSessionId = session.session_id;
    localStorage.setItem('cornerstone_active_session_id', activeSessionId);

    const listRes = await fetch('/api/chats');
    const sessions = await listRes.json();
    renderSessionListDOM(sessions);
    await loadChatSession(activeSessionId);
  } catch (err) {
    console.error("Failed to create chat session:", err);
  }
}

async function loadChatSession(sessionId) {
  activeSessionId = sessionId;
  localStorage.setItem('cornerstone_active_session_id', sessionId);
  
  document.querySelectorAll('.chat-session-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === sessionId);
  });

  const historyContainer = document.getElementById('chatHistory');
  if (!historyContainer) return;
  historyContainer.innerHTML = '';

  try {
    const res = await fetch(`/api/chats/${sessionId}`);
    const data = await res.json();
    const messages = data.messages || [];

    if (messages.length === 0) {
      renderMessageDOM('assistant', '<h3>مرحباً بك في نظام Cornerstone Realty الذكي 🏢</h3><p>يمكنك الاستفسار عن الشقق المتاحة، فحص عقود الإيجار، تقديم طلبات الصيانة، أو تعديل قيمة الإيجار مع تفعيل نظام الموافقة البشرية Elicitation.</p>');
    } else {
      messages.forEach(msg => {
        if (msg.type === 'user') renderMessageDOM('user', msg.content);
        else if (msg.type === 'assistant') renderMessageDOM('assistant', msg.content);
        else if (msg.type === 'tool_trace') renderToolCardDOM(msg.tool, msg.args, msg.result);
        else if (msg.type === 'elicitation') renderElicitationDOM(msg.payload);
      });
    }
  } catch (err) {
    console.error("Failed to load chat session:", err);
  }
}

async function deleteChatSession(sessionId, event) {
  if (event) event.stopPropagation();
  try {
    await fetch(`/api/chats/${sessionId}`, { method: 'DELETE' });
    if (activeSessionId === sessionId) {
      activeSessionId = null;
      localStorage.removeItem('cornerstone_active_session_id');
    }
    await fetchChatSessions();
  } catch (err) {
    console.error("Failed to delete chat session:", err);
  }
}

function renderSessionListDOM(sessions) {
  const container = document.getElementById('chatSessionList');
  if (!container) return;
  container.innerHTML = '';

  sessions.forEach(s => {
    const div = document.createElement('div');
    div.className = `chat-session-item ${s.session_id === activeSessionId ? 'active' : ''}`;
    div.dataset.id = s.session_id;
    div.onclick = () => loadChatSession(s.session_id);
    div.innerHTML = `
      <div class="session-info">
        <span class="session-title">💬 ${s.title}</span>
        <span class="session-date">${s.created_at || ''}</span>
      </div>
      <button class="btn-del-session" onclick="deleteChatSession('${s.session_id}', event)" title="حذف المحادثة">🗑️</button>
    `;
    container.appendChild(div);
  });
}

// --- DOM RENDERERS ---

function renderMessageDOM(role, contentHtmlOrText) {
  const history = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = `chat-msg-bubble msg ${role}`;
  
  if (role === 'assistant') {
    div.classList.add('ai-response-content');
    const dirClass = detectTextDirection(contentHtmlOrText);
    if (dirClass) div.classList.add(dirClass);
    div.innerHTML = contentHtmlOrText;
  } else {
    const dirClass = detectTextDirection(contentHtmlOrText);
    if (dirClass) div.classList.add(dirClass);
    div.innerText = contentHtmlOrText;
  }
  
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;
  return div;
}

/**
 * Toggle tool card open/closed using data-open attribute.
 * Using data attribute avoids inline style vs CSS !important conflicts.
 */
function toggleToolCard(headerEl) {
  const card = headerEl.closest('.tool-card');
  if (!card) return;
  const isOpen = card.dataset.open === 'true';
  card.dataset.open = isOpen ? 'false' : 'true';
}

function renderToolCardDOM(tool, args, result) {
  const history = document.getElementById('chatHistory');
  if (!history) return null;

  const status = (result && result.status) ? result.status : 'success';
  const isElicitation = (status === 'elicitation_required');
  const badgeClass = isElicitation ? 'tool-badge elicitation' : 'tool-badge';
  const badgeText = isElicitation ? 'ELICITATION' : 'SUCCESS';

  const toolName = tool || 'unnamed_tool';
  const argsJson = args ? JSON.stringify(args) : '{}';
  const argsPreview = argsJson.length > 40 ? argsJson.substring(0, 40) + '…' : argsJson;

  // Safely encode JSON for display - escape HTML entities inside pre
  const escapeHtml = (str) => str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const argsFormatted = escapeHtml(JSON.stringify(args || {}, null, 2));
  const resultFormatted = escapeHtml(JSON.stringify(result || {}, null, 2));

  const container = document.createElement('div');
  container.className = 'tool-card';
  container.dataset.open = 'true'; // Open by default via data attribute

  container.innerHTML = `
    <div class="tool-card-header" onclick="toggleToolCard(this)">
      <div class="tool-info">
        <span class="tool-emoji">🛠️</span>
        <span class="tool-name-title">MCP Tool: <strong>${toolName}</strong></span>
        <span class="tool-args-preview">${argsPreview}</span>
        <span class="${badgeClass}">${badgeText}</span>
      </div>
      <span class="toggle-icon">▼</span>
    </div>
    <div class="tool-card-body">
      <div class="tool-section">
        <div class="tool-section-title">📥 Input Parameters</div>
        <pre class="json-block">${argsFormatted}</pre>
      </div>
      <div class="tool-section">
        <div class="tool-section-title">📤 Output Result</div>
        <pre class="json-block">${resultFormatted}</pre>
      </div>
    </div>
  `;

  history.appendChild(container);
  history.scrollTop = history.scrollHeight;
  return container;
}

function renderElicitationDOM(payload) {
  const history = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = 'elicitation-card';
  div.id = 'activeElicitation';
  div.innerHTML = `
    <div class="elicitation-title">⚠️ Elicitation Triggered (Human Approval Needed)</div>
    <p>${payload.prompt}</p>
    <div class="elicitation-btns">
      <button class="btn-approve" onclick="respondElicitation(${payload.lease_id}, ${payload.proposed_rent}, true)">موافقة (Approve)</button>
      <button class="btn-deny" onclick="respondElicitation(${payload.lease_id}, ${payload.proposed_rent}, false)">رفض (Deny)</button>
    </div>
  `;
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;
}

// --- SSE STREAM CHAT CONTROLLER ---

async function sendChatMessageStream() {
  if (!activeSessionId) await createNewChatSession();

  const inputEl = document.getElementById('userInput');
  const text = inputEl.value.trim();
  if (!text) return;

  renderMessageDOM('user', text);
  inputEl.value = '';
  inputEl.style.height = 'auto';

  const role = document.getElementById('roleSelect').value;
  const model = document.getElementById('modelSelect').value;

  let currentAssistantBubble = null;
  let fullAssistantText = '';

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: activeSessionId,
        user_message: text,
        role: role,
        model: model,
        conversation_history: []
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const dataStr = trimmed.slice(6).trim();
        if (!dataStr) continue;

        try {
          const event = JSON.parse(dataStr);

          if (event.type === 'tool_call') {
            // Finalize any in-progress assistant bubble before showing tool
            currentAssistantBubble = null;
            fullAssistantText = '';
            renderToolCardDOM(event.tool, event.args, event.result);

          } else if (event.type === 'token') {
            if (!currentAssistantBubble) {
              currentAssistantBubble = renderMessageDOM('assistant', '');
            }
            fullAssistantText += event.content;
            const dirClass = detectTextDirection(fullAssistantText);
            if (dirClass) currentAssistantBubble.classList.add(dirClass);
            else currentAssistantBubble.classList.remove('dir-ltr');
            currentAssistantBubble.innerHTML = fullAssistantText;
            document.getElementById('chatHistory').scrollTop = 999999;

          } else if (event.type === 'elicitation_required') {
            renderElicitationDOM(event.payload);

          } else if (event.type === 'fallback') {
            if (!currentAssistantBubble) currentAssistantBubble = renderMessageDOM('assistant', '');
            currentAssistantBubble.innerHTML = event.content;
          }
        } catch (e) {
          console.error("SSE Parse Error:", e, dataStr);
        }
      }
    }

    // Refresh sidebar titles without resetting DOM
    const sessions = await (await fetch('/api/chats')).json();
    renderSessionListDOM(sessions);

  } catch (err) {
    if (!currentAssistantBubble) currentAssistantBubble = renderMessageDOM('assistant', '');
    currentAssistantBubble.innerHTML = '<p>⚠️ خطأ في الاتصال: ' + err.message + '</p>';
  }
}

async function respondElicitation(leaseId, proposedRent, approved) {
  document.getElementById('activeElicitation')?.remove();
  try {
    const res = await fetch('/api/elicitation/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: activeSessionId,
        lease_id: leaseId,
        proposed_rent: proposedRent,
        approved: approved
      })
    });
    const data = await res.json();
    renderMessageDOM('assistant', data.final_answer);
  } catch (err) {
    renderMessageDOM('assistant', '<p>⚠️ Failed to record elicitation response: ' + err.message + '</p>');
  }
}

function onRoleChange() {
  const role = document.getElementById('roleSelect').value;
  document.getElementById('notifStatus').innerText = 'PUSH SENT (' + role.toUpperCase() + ')';
  renderMessageDOM('assistant', `<h3>ℹ️ تم تغيير صلاحيات المستخدم</h3><p>الدور الجديد: <strong>${role}</strong>. تم إرسال إشعار <code>notifications/tools/list_changed</code>.</p>`);
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessageStream();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initModelDropdown();
  fetchChatSessions();
});
