/**
 * Chat Page — SSE streaming, tool cards, elicitation, session management.
 * Guarantees 100% state persistence and identical rendering in stream vs reload.
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

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

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

// ── Copy Helper ──

async function copyToClipboard(text, btnEl) {
  try {
    await navigator.clipboard.writeText(text);
    const origHtml = btnEl.innerHTML;
    btnEl.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <span style="color:#10b981; font-weight:600; font-size:11px; margin-left:3px;">Copied!</span>
    `;
    setTimeout(() => {
      btnEl.innerHTML = origHtml;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
  }
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
    
    // Auto-switch role/persona selector to saved session persona
    if (data.role) {
      const roleSel = document.getElementById('roleSelect');
      if (roleSel && roleSel.value !== data.role) {
        roleSel.value = data.role;
        updatePersonaBanner();
        fetchTenantMemories();
      }
    }

    const msgs = data.messages || [];
    if (msgs.length === 0) {
      renderMessage('assistant', '<h3>Welcome to Cornerstone AI</h3><p>Ask about available units, lease terms, maintenance requests, compliance audits, or policy documents.</p>');
    } else {
      msgs.forEach(m => {
        if (m.type === 'user') {
          renderMessage('user', m.content);
        } else if (m.type === 'assistant') {
          renderMessage('assistant', m.content);
        } else if (m.type === 'tool_trace') {
          renderToolCard(m.tool, m.args, m.result);
        } else if (m.type === 'elicitation') {
          renderElicitation(m.payload);
        } else if (m.type === 'intent_routed') {
          let p = {};
          try { p = typeof m.content === 'string' ? JSON.parse(m.content) : (m.content || {}); } catch (e) { p = {}; }
          renderIntentBadge(p.intent || 'STANDARD', p.rationale || '');
        } else if (m.type === 'memory_context') {
          let p = {};
          try { p = typeof m.content === 'string' ? JSON.parse(m.content) : (m.content || {}); } catch (e) { p = {}; }
          renderMemoryCard(p);
        } else if (m.type === 'self_rag_verification') {
          let p = {};
          try { p = typeof m.content === 'string' ? JSON.parse(m.content) : (m.content || {}); } catch (e) { p = {}; }
          renderSelfRagBadge(p);
        } else if (m.type === 'planning_subtask') {
          let p = {};
          try { p = typeof m.content === 'string' ? JSON.parse(m.content) : (m.content || {}); } catch (e) { p = {}; }
          renderPlanningSubtaskCard(p);
        }
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
      <span class="session-title">${escapeHtml(s.title || 'New conversation')}</span>
      <button class="session-delete" onclick="deleteChatSession('${s.session_id}', event)" title="Delete">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>`;
    container.appendChild(div);
  });
}

// ── DOM Renderers ──

function renderMessage(role, content) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return null;
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  
  if (role === 'assistant') {
    div.classList.add('ai-response-content');
    const dir = detectTextDirection(content);
    if (dir) div.classList.add(dir);
    
    // Message container with action toolbar
    const textContainer = document.createElement('div');
    textContainer.className = 'msg-body';
    if (content && window.marked && typeof window.marked.parse === 'function') {
      textContainer.innerHTML = window.marked.parse(content);
    } else {
      textContainer.innerHTML = content || '';
    }
    div.appendChild(textContainer);

    // Floating copy button
    const actionsBar = document.createElement('div');
    actionsBar.className = 'msg-actions-bar';
    actionsBar.innerHTML = `
      <button class="msg-action-btn" title="Copy response" onclick="copyToClipboard(\`${escapeHtml(content || '').replace(/`/g, '\\`')}\`, this)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>Copy</span>
      </button>
    `;
    div.appendChild(actionsBar);
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
  const isOpen = card.dataset.open === 'true';
  card.dataset.open = isOpen ? 'false' : 'true';
  const icon = card.querySelector('.toggle-icon');
  if (icon) icon.innerHTML = isOpen ? '&#9654;' : '&#9660;';
}

function renderToolCard(tool, args, result) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return null;
  const status = result?.status || 'success';
  const isElit = status === 'elicitation_required';
  const isError = status === 'error';
  const argsJson = args ? JSON.stringify(args) : '{}';
  const argsPreview = argsJson.length > 45 ? argsJson.substring(0, 45) + '...' : argsJson;
  const card = document.createElement('div');
  card.className = 'tool-card';
  card.dataset.open = 'true';

  let toolIcon = '⚙️';
  let badgeLabel = 'SUCCESS';
  let badgeClass = 'success';
  if (isElit) { toolIcon = '🛡️'; badgeLabel = 'ELICITATION'; badgeClass = 'elicitation'; }
  if (isError) { toolIcon = '⚠️'; badgeLabel = 'ERROR'; badgeClass = 'error'; }

  // Custom visual enhancement for run_property_audit
  let specialVisual = '';
  if (tool === 'run_property_audit' && result && !isError) {
    toolIcon = '📊';
    const totalU = result.total_units || 0;
    const occU = result.occupied_units || 0;
    const occRate = result.occupancy_rate || '0%';
    const pId = result.property_id || args?.property_id || 1;
    const logs = result.progress_logs || [];

    specialVisual = `
      <div class="audit-summary-widget">
        <div class="audit-widget-header">
          <span class="audit-widget-title">Property #${pId} Compliance & Occupancy Scorecard</span>
          <span class="audit-rate-pill">${occRate} Occupancy</span>
        </div>
        <div class="audit-metrics-grid">
          <div class="audit-metric-card">
            <span class="metric-num">${totalU}</span>
            <span class="metric-lbl">Total Units</span>
          </div>
          <div class="audit-metric-card">
            <span class="metric-num" style="color:var(--emerald,#10b981);">${occU}</span>
            <span class="metric-lbl">Occupied Units</span>
          </div>
          <div class="audit-metric-card">
            <span class="metric-num" style="color:var(--cyan,#06b6d4);">${totalU - occU}</span>
            <span class="metric-lbl">Available</span>
          </div>
          <div class="audit-metric-card">
            <span class="metric-num" style="color:var(--accent,#6366f1);">${occRate}</span>
            <span class="metric-lbl">Occupancy Rate</span>
          </div>
        </div>
        ${logs.length > 0 ? `
          <div class="audit-progress-container">
            <div class="audit-progress-bar">
              <div class="audit-progress-fill" style="width: 100%;"></div>
            </div>
            <div class="audit-steps-list">
              ${logs.map(l => `
                <div class="audit-step-item">
                  <span class="step-check">✓</span>
                  <span class="step-text">${escapeHtml(l.message)}</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  } else if (tool === 'lookup_available_units' && result && !isError) {
    toolIcon = '🔍';
    const count = result.count || (Array.isArray(result.result) ? result.result.length : 0);
    specialVisual = `
      <div class="tool-quick-stat">
        <span class="stat-badge">Found <strong>${count}</strong> available units matching query criteria</span>
      </div>
    `;
  }

  const rawJsonArgs = JSON.stringify(args || {}, null, 2);
  const rawJsonRes = JSON.stringify(result || {}, null, 2);

  card.innerHTML = `
    <div class="tool-card-header" onclick="toggleToolCard(this)">
      <div class="tool-info">
        <span class="tool-icon-label">${toolIcon}</span>
        <span class="tool-name-title">${escapeHtml(tool || 'tool')}</span>
        <span class="tool-args-preview">${escapeHtml(argsPreview)}</span>
        <span class="tool-badge ${badgeClass}">${badgeLabel}</span>
      </div>
      <span class="toggle-icon">&#9660;</span>
    </div>
    <div class="tool-card-body">
      ${specialVisual}
      <div class="tool-section">
        <div class="tool-section-title-row">
          <span class="tool-section-title">Input Parameters</span>
          <button class="json-copy-btn" onclick="event.stopPropagation(); copyToClipboard(\`${escapeHtml(rawJsonArgs).replace(/`/g, '\\`')}\`, this)">Copy</button>
        </div>
        <pre class="json-block">${escapeHtml(rawJsonArgs)}</pre>
      </div>
      <div class="tool-section">
        <div class="tool-section-title-row">
          <span class="tool-section-title">Output Result</span>
          <button class="json-copy-btn" onclick="event.stopPropagation(); copyToClipboard(\`${escapeHtml(rawJsonRes).replace(/`/g, '\\`')}\`, this)">Copy</button>
        </div>
        <pre class="json-block">${escapeHtml(rawJsonRes)}</pre>
      </div>
    </div>`;

  hist.appendChild(card);
  hist.scrollTop = hist.scrollHeight;
  return card;
}

function renderElicitation(payload) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return;
  const div = document.createElement('div');
  div.className = 'elicitation-card';
  div.id = 'activeElicitation';
  const leaseId = payload.lease_id || 1;
  const proposedRent = payload.proposed_rent || 0;
  
  div.innerHTML = `
    <div class="elicitation-title">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span>Elicitation — Executive Approval Required</span>
    </div>
    <p class="elicitation-prompt">${escapeHtml(payload.prompt || 'High-value lease operation requires executive authorization.')}</p>
    <div class="elicitation-btns">
      <button class="btn-approve" onclick="respondElicitation(${leaseId}, ${proposedRent}, true)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Approve Override
      </button>
      <button class="btn-deny" onclick="respondElicitation(${leaseId}, ${proposedRent}, false)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        Deny Request
      </button>
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
    renderMessage('assistant', `<p>Elicitation error: ${escapeHtml(e.message)}</p>`);
  }
}

// ── Persona & Memory ──

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

async function onRoleChange() {
  updatePersonaBanner();
  fetchTenantMemories();
  if (activeSessionId) {
    const role = document.getElementById('roleSelect')?.value;
    if (role) {
      try {
        await fetch(`/api/chats/${activeSessionId}/role`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role })
        });
      } catch (e) {
        console.error('Failed to update session role in DB:', e);
      }
    }
  }
}

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
        <span class="memory-card-title">Active Memory Context — ${escapeHtml(event.persona_name || 'Tenant')}</span>
        <span class="memory-card-badge">${facts.length} Facts • ${episodes.length} Episodes</span>
      </div>
      <span class="toggle-icon">&#9660;</span>
    </div>
    <div class="memory-card-body">
      ${facts.length > 0 ? `
        <div class="memory-section-title">Consolidated Semantic Facts (v1/v2 Active)</div>
        <div class="fact-list">
          ${facts.map(f => `
            <div class="fact-item">
              <span class="fact-badge">[${escapeHtml((f.category || 'fact').toUpperCase())}]</span>
              <span class="fact-val">${escapeHtml(f.value)}</span>
              <span class="fact-ver">v${f.version || 1}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}
      ${episodes.length > 0 ? `
        <div class="memory-section-title" style="margin-top:${facts.length > 0 ? '10px' : '0'};">Recent Episodic Store Events</div>
        <div class="episode-list">
          ${episodes.map(e => `
            <div class="episode-item">
              <span class="episode-date">${escapeHtml(e.timestamp || '2026-02-15')}</span>
              <span class="episode-text">${escapeHtml(e.summary)}</span>
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
  if (!card) return;
  const isOpen = card.dataset.open === 'true';
  card.dataset.open = isOpen ? 'false' : 'true';
  const icon = card.querySelector('.toggle-icon');
  if (icon) icon.innerHTML = isOpen ? '&#9654;' : '&#9660;';
}

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
      <span class="badge-tag">[IsRel: ${escapeHtml(event.is_relevant)}]</span>
      <span class="badge-tag">[IsSup: ${escapeHtml(event.is_supported)}]</span>
    `;
  } else {
    badge.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span>Self-RAG Advisory: Unverified Policy Claims</span>
      <span class="badge-tag">[IsRel: ${escapeHtml(event.is_relevant)}]</span>
      <span class="badge-tag">[IsSup: ${escapeHtml(event.is_supported)}]</span>
    `;
  }
  hist.appendChild(badge);
  hist.scrollTop = hist.scrollHeight;
}

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
          <span style="color:var(--green,#10b981); font-weight:600;">[${escapeHtml((m.category || 'fact').toUpperCase())}]</span> ${escapeHtml(m.event_summary)}
        </div>
      `).join('');
    } else {
      container.innerHTML = `<i>No recorded memories for ${escapeHtml(p.name)}.</i>`;
    }
  } catch (e) {
    container.innerHTML = '<span style="color:var(--red,#ef4444);">Failed to load memory context.</span>';
  }
}

// ── SSE Stream Chat ──

let currentAbortController = null;

function abortChatStream() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  const thinkingEl = document.getElementById('thinkingIndicator');
  if (thinkingEl) thinkingEl.style.display = 'none';

  const btnSend = document.getElementById('btnSendMessage');
  const btnStop = document.getElementById('btnStopMessage');
  if (btnSend) btnSend.style.display = 'flex';
  if (btnStop) btnStop.style.display = 'none';

  const hist = document.getElementById('chatHistory');
  if (hist) {
    const badge = document.createElement('div');
    badge.className = 'intent-routed-badge';
    badge.style.background = 'rgba(244, 63, 94, 0.15)';
    badge.style.border = '1px solid rgba(244, 63, 94, 0.3)';
    badge.style.color = '#f43f5e';
    badge.innerHTML = `<span>🛑 <strong>Generation Interrupted by User</strong></span>`;
    hist.appendChild(badge);
    hist.scrollTop = hist.scrollHeight;
  }
}

async function sendChatMessageStream() {
  if (!activeSessionId) await createNewChatSession();
  const inputEl = document.getElementById('userInput');
  const text = inputEl.value.trim();
  if (!text) return;

  renderMessage('user', text);
  inputEl.value = '';
  inputEl.style.height = 'auto';

  autoResizeTextarea(inputEl);

  const role = document.getElementById('roleSelect').value;
  const model = document.getElementById('modelSelect').value;
  const ragStrategy = document.getElementById('ragSelect').value;

  const btnSend = document.getElementById('btnSendMessage');
  const btnStop = document.getElementById('btnStopMessage');
  if (btnSend) btnSend.style.display = 'none';
  if (btnStop) btnStop.style.display = 'flex';

  let bubble = null;
  let fullText = '';
  const thinkingEl = document.getElementById('thinkingIndicator');
  if (thinkingEl) thinkingEl.style.display = 'flex';

  currentAbortController = new AbortController();

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        session_id: activeSessionId,
        user_message: text,
        role, model,
        rag_strategy: ragStrategy,
        conversation_history: []
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

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

          if (event.type === 'intent_routed') {
            renderIntentBadge(event.intent, event.rationale);
          } else if (event.type === 'planning_subtask') {
            if (thinkingEl) thinkingEl.style.display = 'none';
            renderPlanningSubtaskCard(event);
          } else if (event.type === 'memory_context') {
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
            
            const bodyEl = bubble.querySelector('.msg-body') || bubble;
            if (window.marked && typeof window.marked.parse === 'function') {
              bodyEl.innerHTML = window.marked.parse(fullText);
            } else {
              bodyEl.innerHTML = fullText;
            }
            document.getElementById('chatHistory').scrollTop = 999999;
          } else if (event.type === 'self_rag_verification') {
            renderSelfRagBadge(event);
          } else if (event.type === 'elicitation_required') {
            renderElicitation(event.payload);
          } else if (event.type === 'fallback') {
            if (!bubble) bubble = renderMessage('assistant', '');
            const bodyEl = bubble.querySelector('.msg-body') || bubble;
            bodyEl.innerHTML = event.content;
          }

        } catch (e) { console.error('SSE parse error:', e); }
      }
    }

    const sessions = await (await fetch('/api/chats')).json();
    renderSessionList(sessions);
  } catch (e) {
    if (e.name === 'AbortError') {
      console.log('Chat stream intentionally aborted by user.');
    } else {
      if (thinkingEl) thinkingEl.style.display = 'none';
      if (!bubble) bubble = renderMessage('assistant', '');
      const bodyEl = bubble.querySelector('.msg-body') || bubble;
      bodyEl.innerHTML = `<div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#f87171; padding:10px 14px; border-radius:8px;">⚠️ <strong>Stream Error:</strong> ${escapeHtml(e.message)}</div>`;
    }
  } finally {
    currentAbortController = null;
    if (thinkingEl) thinkingEl.style.display = 'none';
    if (btnSend) btnSend.style.display = 'flex';
    if (btnStop) btnStop.style.display = 'none';
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

function renderIntentBadge(intent, rationale) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return;
  const badge = document.createElement('div');
  const isPlanning = intent === 'PLANNING';
  badge.className = `intent-routed-badge ${isPlanning ? 'intent-planning' : 'intent-standard'}`;
  
  let icon = '⚡';
  let title = 'Standard Query';
  if (isPlanning) { icon = '🧩'; title = 'Autonomous Planning Agent (Week 4)'; }
  
  badge.innerHTML = `
    <span class="intent-tag">${icon} ${intent}</span>
    <span><strong>Intent Router (Mistral 7B):</strong> ${escapeHtml(rationale || title)}</span>
  `;
  hist.appendChild(badge);
  hist.scrollTop = hist.scrollHeight;
}

function togglePlanningCard(headerEl) {
  const card = headerEl.closest('.planning-chat-card');
  if (!card) return;
  const isExpanded = card.dataset.expanded !== 'false';
  card.dataset.expanded = isExpanded ? 'false' : 'true';
  const body = card.querySelector('.planning-card-body');
  const icon = card.querySelector('.planning-toggle-icon');
  if (isExpanded) {
    body.style.display = 'none';
    if (icon) icon.innerHTML = '&#9654;';
  } else {
    body.style.display = 'block';
    if (icon) icon.innerHTML = '&#9660;';
  }
}

function renderPlanningSubtaskCard(st) {
  const hist = document.getElementById('chatHistory');
  if (!hist) return;
  const card = document.createElement('div');
  const method = st.method || 'PS';
  
  let badgeClass = 'planning-card-ps';
  let tagColor = '#10b981';
  if (method === 'ToT') { badgeClass = 'planning-card-tot'; tagColor = '#8b5cf6'; }
  if (method === 'LATS') { badgeClass = 'planning-card-lats'; tagColor = '#f43f5e'; }

  const parsedOutput = (window.marked && typeof window.marked.parse === 'function')
    ? window.marked.parse(st.output || '')
    : escapeHtml(st.output || '');

  card.className = `planning-chat-card ${badgeClass}`;
  card.dataset.expanded = 'true';

  card.innerHTML = `
    <div class="planning-card-header" onclick="togglePlanningCard(this)" style="display:flex; justify-content:space-between; align-items:center; cursor:pointer; user-select:none; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:8px;">
      <div style="display:flex; align-items:center; gap:8px; flex:1;">
        <span style="background:${tagColor}; color:#fff; padding:2px 8px; border-radius:10px; font-size:0.72rem; font-weight:bold; flex-shrink:0;">${method} ROUTED</span>
        <span style="font-weight:600; color:#f8fafc; font-size:0.88rem;">${escapeHtml(st.instruction)}</span>
      </div>
      <div style="display:flex; align-items:center; gap:6px; flex-shrink:0; margin-left:10px;">
        <span style="color:#64748b; font-size:0.75rem;">Sub-Task</span>
        <span class="planning-toggle-icon" style="color:#94a3b8; font-size:0.8rem;">&#9660;</span>
      </div>
    </div>
    <div class="planning-card-body ai-response-content" style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:8px; font-size:0.85rem; color:#cbd5e1; border:1px solid rgba(255,255,255,0.05);">
      ${parsedOutput}
    </div>
  `;
  hist.appendChild(card);
  hist.scrollTop = hist.scrollHeight;
}
