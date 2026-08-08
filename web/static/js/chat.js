/**
 * Chat Page — SSE streaming, tool cards, elicitation, session management.
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

let currentPersonas = {};

function initModelDropdown() {
  const sel = document.getElementById('modelSelect');
  if (!sel) return;
  sel.innerHTML = '';
  AVAILABLE_MODELS.forEach(m => {
    const o = document.createElement('option');
    o.value = m; o.textContent = m;
    if (m === 'gemini/gemini-3.1-flash-lite') o.selected = true;
    sel.appendChild(o);
  });
}

// ── Text Direction Detection ──

function detectTextDirection(text) {
  if (!text) return '';
  const clean = text.replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ');
  const latin = (clean.match(/[a-zA-Z]/g) || []).length;
  const arabic = (clean.match(/[\u0600-\u06FF]/g) || []).length;
  return (latin > arabic && latin > 5) ? 'dir-ltr' : '';
}

// ── Session Management ──

async function fetchChatSessions() {
  try {
    const res = await fetch('/api/chats');
    const sessions = await res.json();
    renderSessionList(sessions);
    if (sessions.length > 0) {
      const existing = sessions.find(s => s.session_id === activeSessionId);
      const targetId = existing ? existing.session_id : sessions[0].session_id;
      if (activePage === 'chat') {
        await loadChatSession(targetId);
      } else {
        activeSessionId = targetId;
        localStorage.setItem('cornerstone_active_session_id', targetId);
      }
    } else {
      if (activePage === 'chat') {
        await createNewChatSession();
      }
    }
  } catch (e) { console.error('Failed to fetch sessions:', e); }
}

async function createNewChatSession() {
  if (activePage !== 'chat') {
    switchPage('chat');
  }
  const role = document.getElementById('roleSelect')?.value || 'property_manager';
  try {
    const res = await fetch('/api/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New conversation', role })
    });
    const session = await res.json();
    activeSessionId = session.session_id;
    localStorage.setItem('cornerstone_active_session_id', activeSessionId);
    const listRes = await fetch('/api/chats');
    renderSessionList(await listRes.json());
    await loadChatSession(activeSessionId);
  } catch (e) { console.error('Failed to create session:', e); }
}

async function loadChatSession(sessionId) {
  activeSessionId = sessionId;
  localStorage.setItem('cornerstone_active_session_id', sessionId);
  if (activePage === 'chat') {
    updateURL('chat', sessionId);
  }
  document.querySelectorAll('.session-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === sessionId);
  });
  const hist = document.getElementById('chatHistory');
  if (!hist) return;
  hist.innerHTML = '';
  try {
    const res = await fetch(`/api/chats/${sessionId}`);
    const data = await res.json();
    const msgs = data.messages || [];
    if (msgs.length === 0) {
      renderMessage('assistant', '<h3>Welcome to Cornerstone AI</h3><p>Ask about available units, lease terms, maintenance requests, or policy documents.</p>');
    } else {
      msgs.forEach(m => {
        if (m.type === 'user') renderMessage('user', m.content);
        else if (m.type === 'assistant') renderMessage('assistant', m.content);
        else if (m.type === 'tool_trace') renderToolCard(m.tool, m.args, m.result);
        else if (m.type === 'elicitation') renderElicitation(m.payload);
      });
    }
  } catch (e) { console.error('Failed to load session:', e); }
}

async function deleteChatSession(sessionId, ev) {
  if (ev) ev.stopPropagation();
  try {
    await fetch(`/api/chats/${sessionId}`, { method: 'DELETE' });
    if (activeSessionId === sessionId) {
      activeSessionId = null;
      localStorage.removeItem('cornerstone_active_session_id');
    }
    fetchChatSessions();
  } catch (e) { console.error('Failed to delete:', e); }
}

function renderSessionList(sessions) {
  const container = document.getElementById('chatSessionList');
  if (!container) return;
  container.innerHTML = '';
  sessions.forEach(s => {
    const div = document.createElement('div');
    div.className = `session-item ${s.session_id === activeSessionId ? 'active' : ''}`;
    div.dataset.id = s.session_id;
    div.setAttribute('data-id', s.session_id);
    div.onclick = () => {

      if (activePage !== 'chat') {
        switchPage('chat');
      }
      loadChatSession(s.session_id);
    };
    div.innerHTML = `
      <span class="session-title">${s.title || 'New conversation'}</span>
      <button class="session-delete" onclick="deleteChatSession('${s.session_id}', event)" title="Delete">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>`;
    container.appendChild(div);
  });
}


// ── DOM Renderers ──

function renderMessage(role, content) {
  const hist = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  if (role === 'assistant') {
    div.classList.add('ai-response-content');
    const dir = detectTextDirection(content);
    if (dir) div.classList.add(dir);
    div.innerHTML = content;
  } else {
    const dir = detectTextDirection(content);
    if (dir) div.classList.add(dir);
    div.textContent = content;
  }
  hist.appendChild(div);
  hist.scrollTop = hist.scrollHeight;
  return div;
}

function toggleToolCard(headerEl) {
  const card = headerEl.closest('.tool-card');
  if (!card) return;
  card.dataset.open = card.dataset.open === 'true' ? 'false' : 'true';
}

function renderToolCard(tool, args, result) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return null;
  const status = result?.status || 'success';
  const isElit = status === 'elicitation_required';
  const argsJson = args ? JSON.stringify(args) : '{}';
  const argsPreview = argsJson.length > 40 ? argsJson.substring(0, 40) + '...' : argsJson;
  const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const card = document.createElement('div');
  card.className = 'tool-card';
  card.dataset.open = 'true';
  card.innerHTML = `
    <div class="tool-card-header" onclick="toggleToolCard(this)">
      <div class="tool-info">
        <span class="tool-name-title">${tool || 'tool'}</span>
        <span class="tool-args-preview">${argsPreview}</span>
        <span class="tool-badge ${isElit ? 'elicitation' : 'success'}">${isElit ? 'ELICITATION' : 'SUCCESS'}</span>
      </div>
      <span class="toggle-icon">&#9660;</span>
    </div>
    <div class="tool-card-body">
      <div class="tool-section">
        <div class="tool-section-title">Input</div>
        <pre class="json-block">${esc(JSON.stringify(args || {}, null, 2))}</pre>
      </div>
      <div class="tool-section">
        <div class="tool-section-title">Output</div>
        <pre class="json-block">${esc(JSON.stringify(result || {}, null, 2))}</pre>
      </div>
    </div>`;
  hist.appendChild(card);
  hist.scrollTop = hist.scrollHeight;
  return card;
}

function renderElicitation(payload) {
  const hist = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = 'elicitation-card';
  div.id = 'activeElicitation';
  div.innerHTML = `
    <div class="elicitation-title">Elicitation — Human Approval Required</div>
    <p>${payload.prompt || 'High-value operation requires approval.'}</p>
    <div class="elicitation-btns">
      <button class="btn-approve" onclick="respondElicitation(${payload.lease_id}, ${payload.proposed_rent}, true)">Approve</button>
      <button class="btn-deny" onclick="respondElicitation(${payload.lease_id}, ${payload.proposed_rent}, false)">Deny</button>
    </div>`;
  hist.appendChild(div);
  hist.scrollTop = hist.scrollHeight;
}

async function respondElicitation(leaseId, proposedRent, approved) {
  document.getElementById('activeElicitation')?.remove();
  try {
    const res = await fetch('/api/elicitation/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: activeSessionId, lease_id: leaseId, proposed_rent: proposedRent, approved })
    });
    const data = await res.json();
    renderMessage('assistant', data.final_answer);
  } catch (e) {
    renderMessage('assistant', `<p>Elicitation error: ${e.message}</p>`);
  }
}

// ── Persona ──

async function fetchPersonas() {
  try {
    const res = await fetch('/api/personas');
    currentPersonas = await res.json();
    updatePersonaBanner();
  } catch (e) { console.error('Failed to fetch personas:', e); }
}

function updatePersonaBanner() {
  const role = document.getElementById('roleSelect')?.value || 'property_manager';
  const p = currentPersonas[role];
  const info = document.getElementById('personaInfo');
  const badge = document.getElementById('personaRoleBadge');
  if (p && info && badge) {
    let detail = `${p.name} — ${p.email}`;
    if (p.unit_number) detail += ` — ${p.unit_number}`;
    info.textContent = detail;
    badge.textContent = role.toUpperCase().replace('_', ' ');
  }
}

function onRoleChange() {
  updatePersonaBanner();
  fetchTenantMemories();
}

// ── Active Memory Context Card ──

function renderMemoryCard(event) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return null;
  const facts = event.active_facts || [];
  const episodes = event.recent_episodes || [];
  if (facts.length === 0 && episodes.length === 0) return null;

  const card = document.createElement('div');
  card.className = 'memory-context-card';
  card.dataset.open = 'true';
  card.innerHTML = `
    <div class="memory-card-header" onclick="toggleMemoryCard(this)">
      <div class="memory-card-info">
        <div class="memory-card-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a5 5 0 0 1 5 5v1a5 5 0 0 1-10 0V7a5 5 0 0 1 5-5z"/><path d="M4 14a8 8 0 0 0 16 0"/><line x1="12" y1="18" x2="12" y2="22"/></svg>
        </div>
        <span class="memory-card-title">Active Memory Context — ${event.persona_name || 'Tenant'}</span>
        <span class="memory-card-badge">${facts.length} Active Facts</span>
      </div>
      <span class="toggle-icon">&#9660;</span>
    </div>
    <div class="memory-card-body">
      ${facts.length > 0 ? `
        <div class="memory-section-title">Consolidated Semantic Facts (v1/v2 Active)</div>
        <div class="fact-list">
          ${facts.map(f => `
            <div class="fact-item">
              <span class="fact-badge">[${f.category.toUpperCase()}]</span>
              <span class="fact-val">${f.value}</span>
              <span class="fact-ver">v${f.version}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}
      ${episodes.length > 0 ? `
        <div class="memory-section-title" style="margin-top:10px;">Recent Episodic Store Events</div>
        <div class="episode-list">
          ${episodes.map(e => `
            <div class="episode-item">
              <span class="episode-date">${e.timestamp || '2026-02-15'}</span>
              <span class="episode-text">${e.summary}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>`;
  hist.appendChild(card);
  hist.scrollTop = hist.scrollHeight;
  return card;
}

function toggleMemoryCard(header) {
  const card = header.closest('.memory-context-card');
  const isOpen = card.dataset.open === 'true';
  card.dataset.open = isOpen ? 'false' : 'true';
  const body = card.querySelector('.memory-card-body');
  const icon = card.querySelector('.toggle-icon');
  if (isOpen) {
    body.style.display = 'none';
    icon.innerHTML = '&#9654;';
  } else {
    body.style.display = 'block';
    icon.innerHTML = '&#9660;';
  }
}

// ── Self-RAG Verification Badge ──

function renderSelfRagBadge(event) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return;
  const isSupported = event.is_supported === 'fully_supported';
  const badge = document.createElement('div');
  badge.className = `self-rag-badge ${isSupported ? 'supported' : 'warning'}`;
  
  if (isSupported) {
    badge.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
      <span>Self-RAG Verified: Grounded in Retrieved Policy</span>
      <span class="badge-tag">[IsRel: ${event.is_relevant}]</span>
      <span class="badge-tag">[IsSup: ${event.is_supported}]</span>
    `;
  } else {
    badge.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span>Self-RAG Advisory: Unverified Statute Claims</span>
      <span class="badge-tag">[IsRel: ${event.is_relevant}]</span>
      <span class="badge-tag">[IsSup: ${event.is_supported}]</span>
    `;
  }
  hist.appendChild(badge);
  hist.scrollTop = hist.scrollHeight;
}

// ── Memories ──

async function fetchTenantMemories() {
  const role = document.getElementById('roleSelect')?.value || 'tenant';
  const p = currentPersonas[role] || { tenant_id: 1, name: 'Amr Hassan' };
  const container = document.getElementById('memoryList');
  if (!container) return;
  try {
    const res = await fetch(`/api/memory/${p.tenant_id}`);
    const data = await res.json();
    if (data.memories && data.memories.length > 0) {
      container.innerHTML = data.memories.map(m => `
        <div style="margin-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;">
          <span style="color:var(--green); font-weight:600;">[${(m.category || 'fact').toUpperCase()}]</span> ${m.event_summary}
        </div>
      `).join('');
    } else {
      container.innerHTML = `<i>No recorded memories for ${p.name}.</i>`;
    }
  } catch (e) {
    container.innerHTML = '<span style="color:var(--red);">Failed to load memory context.</span>';
  }
}



// ── SSE Stream Chat ──

async function sendChatMessageStream() {
  if (!activeSessionId) await createNewChatSession();
  const inputEl = document.getElementById('userInput');
  const text = inputEl.value.trim();
  if (!text) return;

  renderMessage('user', text);
  inputEl.value = '';
  inputEl.style.height = 'auto';

  // Optimistically update session title in sidebar immediately on first message
  const activeItemTitle = document.querySelector('.session-item.active .session-title') || document.querySelector(`.session-item[data-id="${activeSessionId}"] .session-title`);
  if (activeItemTitle) {
    const currentTitle = activeItemTitle.textContent.trim().toLowerCase();
    const isDefault = ['new conversation', 'new chat', 'محادثة جديدة'].some(k => currentTitle.includes(k));
    if (isDefault) {
      activeItemTitle.textContent = text.slice(0, 35) + (text.length > 35 ? '...' : '');
    }
  }



  const role = document.getElementById('roleSelect').value;

  const model = document.getElementById('modelSelect').value;
  const ragStrategy = document.getElementById('ragSelect').value;

  let bubble = null;
  let fullText = '';
  const thinkingEl = document.getElementById('thinkingIndicator');
  if (thinkingEl) thinkingEl.style.display = 'flex';

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: activeSessionId,
        user_message: text,
        role, model,
        rag_strategy: ragStrategy,
        conversation_history: []
      })
    });

    // Refresh chat list so sidebar updates title immediately on first message
    fetch('/api/chats').then(res => res.json()).then(sessions => renderSessionList(sessions));

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

          if (event.type === 'memory_context') {
            renderMemoryCard(event);
          } else if (event.type === 'tool_call') {
            if (thinkingEl) thinkingEl.style.display = 'none';
            bubble = null; fullText = '';
            renderToolCard(event.tool, event.args, event.result);
          } else if (event.type === 'token') {
            if (thinkingEl) thinkingEl.style.display = 'none';
            if (!bubble) bubble = renderMessage('assistant', '');
            fullText += event.content;
            const dir = detectTextDirection(fullText);
            if (dir) bubble.classList.add(dir);
            else bubble.classList.remove('dir-ltr');
            bubble.innerHTML = fullText;
            document.getElementById('chatHistory').scrollTop = 999999;
          } else if (event.type === 'self_rag_verification') {
            renderSelfRagBadge(event);
          } else if (event.type === 'elicitation_required') {
            renderElicitation(event.payload);
          } else if (event.type === 'fallback') {
            if (!bubble) bubble = renderMessage('assistant', '');
            bubble.innerHTML = event.content;
          }

        } catch (e) { console.error('SSE parse error:', e); }
      }
    }

    const sessions = await (await fetch('/api/chats')).json();

    renderSessionList(sessions);
  } catch (e) {
    if (thinkingEl) thinkingEl.style.display = 'none';
    if (!bubble) bubble = renderMessage('assistant', '');
    bubble.innerHTML = `<p>Connection error: ${e.message}</p>`;
  }
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessageStream();
  }
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}
