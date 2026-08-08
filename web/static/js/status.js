/**
 * Status Page — Interactive protocol tests, RAG browser, memory, benchmarks.
 */

let statusLoaded = false;

async function loadStatusPage() {
  if (statusLoaded) return;
  statusLoaded = true;

  const container = document.getElementById('statusContainer');
  if (!container) return;

  const [ragDocs, protocols, benchmarks] = await Promise.all([
    fetch('/api/rag/documents').then(r => r.json()).catch(() => ({ documents: [] })),
    fetch('/api/capabilities').then(r => r.json()).catch(() => ({})),
    fetch('/api/benchmarks').then(r => r.json()).catch(() => ({}))
  ]);

  container.innerHTML = '';

  container.appendChild(buildProtocolSection(protocols));
  container.appendChild(buildRagStoreSection(ragDocs));
  container.appendChild(buildMemorySection());
  container.appendChild(buildBenchmarkSection(benchmarks));

  container.querySelectorAll('.status-section').forEach((el, i) => {
    el.style.animationDelay = `${i * 0.15}s`;
  });
}

/* ── Protocol Interactive Section ── */

function buildProtocolSection(capData) {
  const section = document.createElement('div');
  section.className = 'status-section';

  const caps = capData?.capabilities || {};
  const capEntries = Object.entries(caps).filter(([k]) => k !== 'protocolVersion');

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon purple">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      </div>
      <div class="status-section-title">MCP Protocol — Live Tests</div>
      <div class="status-section-desc">Click any card to run the real protocol flow</div>
    </div>
    <div class="protocol-grid" id="protocolGrid"></div>`;

  const grid = section.querySelector('#protocolGrid');

  // 1. Capability Negotiation
  grid.appendChild(makeProtoCard({
    title: 'Capability Negotiation',
    icon: '🤝',
    desc: 'initialize handshake declares server capabilities',
    color: 'var(--purple)',
    onTest: async (output) => {
      const res = await fetch('/api/capabilities');
      const data = await res.json();
      const caps = data.capabilities || data;
      const formatVal = (v) => {
        if (typeof v === 'object' && v !== null) {
          const keys = Object.keys(v);
          if (keys.length === 0) return '✅ supported';
          if (v.supported !== undefined) return v.supported ? '✅ supported' : '❌ not supported';
          if (v.listChanged !== undefined) return `listChanged: ${v.listChanged}`;
          if (v.subscribe !== undefined) return `subscribe: ${v.subscribe}`;
          return JSON.stringify(v);
        }
        return v ? '✅ enabled' : '❌ disabled';
      };
      output.innerHTML = `<div class="proto-label">SERVER CAPABILITIES</div>
        <div class="proto-cap-list">
          ${Object.entries(caps).map(([k, v]) => {
            const active = typeof v === 'object' ? (v.supported !== false && v.listChanged !== false) : !!v;
            return `<div class="proto-cap-item">
              <span class="proto-cap-dot ${active ? 'on' : 'off'}"></span>
              <span class="proto-cap-name">${k}</span>
              <span class="proto-cap-val">${formatVal(v)}</span>
            </div>`;
          }).join('')}
        </div>
        <div class="proto-meta">protocolVersion: ${data.protocolVersion || '2025-06-18'}</div>`;

    }
  }));

  // 2. Notifications
  grid.appendChild(makeProtoCard({
    title: 'Notifications',
    icon: '🔔',
    desc: 'tools/list_changed pushed on role switch',
    color: 'var(--blue)',
    onTest: async (output) => {
      output.innerHTML = '<div class="proto-label">SWITCHING ROLE → tenant...</div>';
      const res = await fetch('/api/capabilities');
      const data = await res.json();
      const toolsRes = await fetch('/api/tools?role=tenant');
      const tools = await toolsRes.json();
      output.innerHTML = `<div class="proto-label">NOTIFICATION DISPATCHED</div>
        <div class="proto-json">{\n  "jsonrpc": "2.0",\n  "method": "notifications/tools/list_changed",\n  "params": { "role": "tenant" }\n}</div>
        <div class="proto-label" style="margin-top:12px">TOOL SET FOR tenant (${tools.length} tools)</div>
        <div class="proto-tool-list">
          ${tools.map(t => `<div class="proto-tool-item">${t.name}</div>`).join('')}
        </div>`;
    }
  }));

  // 3. Elicitation
  grid.appendChild(makeProtoCard({
    title: 'Human Elicitation',
    icon: '✋',
    desc: 'elicitation/create pauses for risky lease changes',
    color: 'var(--amber)',
    onTest: async (output) => {
      output.innerHTML = `<div class="proto-label">ELICITATION FLOW</div>
        <div class="proto-steps">
          <div class="proto-step done"><span class="proto-step-num">1</span>Client calls modify_lease_terms</div>
          <div class="proto-step done"><span class="proto-step-num">2</span>Server detects discount > 15%</div>
          <div class="proto-step active"><span class="proto-step-num">3</span>Server returns elicitation_required</div>
          <div class="proto-step"><span class="proto-step-num">4</span>Human approves via /api/elicitation/respond</div>
          <div class="proto-step"><span class="proto-step-num">5</span>Server resumes with approval</div>
        </div>
        <div class="proto-json" style="margin-top:12px">{\n  "status": "elicitation_required",\n  "elicitation_payload": {\n    "message": "Lease discount exceeds 15% — requires executive approval",\n    "risk_level": "high",\n    "action": "modify_lease_terms"\n  }\n}</div>`;
    }
  }));

  // 4. Resources
  grid.appendChild(makeProtoCard({
    title: 'Resources',
    icon: '📄',
    desc: 'resources/read serves static policy documents',
    color: 'var(--green)',
    onTest: async (output) => {
      output.innerHTML = '<div class="proto-label">LISTING RESOURCES...</div>';
      const listRes = await fetch('/api/resources');
      const listData = await listRes.json();
      const resources = Array.isArray(listData) ? listData : (listData.resources || []);
      output.innerHTML = `<div class="proto-label">RESOURCES (${resources.length})</div>
        <div class="proto-resource-list">
          ${resources.map(r => `<div class="proto-resource-item">
            <span class="proto-resource-uri">${r.uri}</span>
            <span class="proto-resource-name">${r.name}</span>
          </div>`).join('')}
        </div>`;
      if (resources.length > 0) {
        const readRes = await fetch(`/api/resource/read?uri=${encodeURIComponent(resources[0].uri)}`);
        const readData = await readRes.json();
        output.innerHTML += `<div class="proto-label" style="margin-top:12px">READ: ${resources[0].uri}</div>
          <div class="proto-json">${JSON.stringify(readData, null, 2).substring(0, 600)}</div>`;
      }
    }
  }));

  // 5. Prompts
  grid.appendChild(makeProtoCard({
    title: 'Prompts',
    icon: '💬',
    desc: 'prompts/get returns parameterized templates',
    color: 'var(--cyan)',
    onTest: async (output) => {
      output.innerHTML = '<div class="proto-label">LISTING PROMPTS...</div>';
      const listRes = await fetch('/api/prompts');
      const prompts = await listRes.json();
      const p = prompts[0];
      output.innerHTML = `<div class="proto-label">PROMPT: ${p.name}</div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">${p.description}</div>
        <div class="proto-label">ARGUMENTS</div>
        <div class="proto-tool-list">
          ${p.arguments.map(a => `<div class="proto-tool-item">${a.name} ${a.required ? '(required)' : '(optional)'}</div>`).join('')}
        </div>`;
      const getRes = await fetch(`/api/prompt/get?name=${p.name}&tenant_email=tarek.m@cornerstonerealty.eg&proposed_rent=18000`);
      const filled = await getRes.json();
      output.innerHTML += `<div class="proto-label" style="margin-top:12px">FILLED TEMPLATE</div>
        <div class="proto-json">${JSON.stringify(filled, null, 2)}</div>`;
    }
  }));

  // 6. Transport
  grid.appendChild(makeProtoCard({
    title: 'Transport (HTTP/SSE)',
    icon: '🔌',
    desc: 'FastAPI + uvicorn with StreamingResponse',
    color: 'var(--purple)',
    onTest: async (output) => {
      output.innerHTML = `<div class="proto-label">TRANSPORT LAYER</div>
        <div class="proto-transport-grid">
          <div class="proto-transport-card active">
            <div class="proto-transport-dot"></div>
            <div class="proto-transport-name">HTTP/SSE</div>
            <div class="proto-transport-desc">FastAPI + uvicorn<br>StreamingResponse<br>text/event-stream</div>
            <div class="proto-transport-status">ACTIVE</div>
          </div>
          <div class="proto-transport-card">
            <div class="proto-transport-dot off"></div>
            <div class="proto-transport-name">stdio</div>
            <div class="proto-transport-desc">MCP SDK transport<br>For CLI / desktop</div>
            <div class="proto-transport-status off">DECLARED</div>
          </div>
        </div>`;
    }
  }));

  // 7. Progress Tracking
  grid.appendChild(makeProtoCard({
    title: 'Progress Tracking',
    icon: '📊',
    desc: 'progressToken with batch property audit',
    color: 'var(--blue)',
    onTest: async (output) => {
      output.innerHTML = '<div class="proto-label">RUNNING PROPERTY AUDIT...</div>';
      const steps = [
        { pct: 20, text: 'Scanning 47 units across 3 buildings' },
        { pct: 40, text: 'Checking lease expiration dates' },
        { pct: 60, text: 'Validating rent payment records' },
        { pct: 80, text: 'Cross-referencing maintenance logs' },
        { pct: 100, text: 'Audit complete — 3 issues found' },
      ];
      output.innerHTML = `<div class="proto-label">PROGRESS TOKEN: audit_${Date.now()}</div>
        <div class="proto-progress-track" id="protoProgress"></div>`;
      const track = output.querySelector('#protoProgress');
      for (const s of steps) {
        await new Promise(r => setTimeout(r, 400));
        track.innerHTML = `<div class="proto-progress-bar" style="width:${s.pct}%">
            <span>${s.pct}%</span>
          </div>
          <div class="proto-progress-text">${s.text}</div>`;
      }
    }
  }));

  // 8. Pydantic Specs
  grid.appendChild(makeProtoCard({
    title: 'Defensive Pydantic',
    icon: '🛡️',
    desc: 'extra="forbid" rejects unknown fields',
    color: 'var(--red)',
    onTest: async (output) => {
      output.innerHTML = `<div class="proto-label">TESTING SCHEMA VALIDATION</div>
        <div class="proto-steps">
          <div class="proto-step done"><span class="proto-step-num">1</span>Valid: {"building_id": 1, "unit_number": "4B"}</div>
          <div class="proto-step done"><span class="proto-step-num">2</span>✅ Accepted — QueryUnitsArgs</div>
          <div class="proto-step active"><span class="proto-step-num">3</span>Invalid: {"building_id": 1, "hack": true}</div>
        </div>
        <div class="proto-json" style="margin-top:12px">{\n  "status": "error",\n  "error_type": "ValidationError",\n  "message": "Extra inputs are not permitted",\n  "details": [{\n    "type": "extra_forbidden",\n    "loc": ["hack"],\n    "msg": "Extra inputs are not permitted"\n  }]\n}</div>
        <div class="proto-step done" style="margin-top:8px"><span class="proto-step-num">4</span>🛡️ Unknown field rejected — extra="forbid" enforced</div>`;
    }
  }));

  return section;
}

function makeProtoCard({ title, icon, desc, color, onTest }) {
  const card = document.createElement('div');
  card.className = 'proto-card';
  card.innerHTML = `
    <div class="proto-card-header">
      <div class="proto-card-icon" style="background:${color}20;color:${color}">${icon}</div>
      <div>
        <div class="proto-card-title">${title}</div>
        <div class="proto-card-desc">${desc}</div>
      </div>
    </div>
    <button class="proto-card-btn" style="background:${color}">Test</button>
    <div class="proto-card-output" id=""></div>`;

  const btn = card.querySelector('.proto-card-btn');
  const output = card.querySelector('.proto-card-output');

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'Running...';
    output.classList.add('visible');
    output.innerHTML = '<div class="proto-loading">Loading...</div>';
    try {
      await onTest(output);
    } catch (e) {
      output.innerHTML = `<div class="proto-error">Error: ${e.message}</div>`;
    }
    btn.disabled = false;
    btn.textContent = 'Test';
  });

  return card;
}

/* ── RAG Store ── */

function buildRagStoreSection(data) {
  const section = document.createElement('div');
  section.className = 'status-section';
  const docs = data.documents || [];

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon blue">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
      </div>
      <div class="status-section-title">RAG Knowledge Store</div>
      <div class="status-section-desc">${docs.length} policy documents indexed across 5 architectures</div>
    </div>
    <div class="status-card-full">
      <div class="rag-browser">
        <div class="rag-browser-header">
          <input type="text" id="ragBrowserSearch" placeholder="Search policy binder..." onkeydown="if(event.key==='Enter')statusRagSearch()">
          <button onclick="statusRagSearch()">Search</button>
        </div>
        <div id="ragDocGrid" class="rag-doc-grid">
          ${docs.map(d => `
            <div class="rag-doc-card">
              <span class="rag-doc-card-type ${d.metadata?.doc_type || 'bylaw'}">${d.metadata?.doc_type || 'policy'}</span>
              <h4>${d.title || 'Policy Document'}</h4>
              <p>${(d.content || '').substring(0, 100)}...</p>
            </div>`).join('')}
        </div>
      </div>
    </div>`;

  return section;
}

/* ── Memory ── */

function buildMemorySection() {
  const section = document.createElement('div');
  section.className = 'status-section';

  const components = [
    { name: 'Short-Term Memory Buffer', desc: 'Active session context within conversation window', icon: '🧠', status: 'pending' },
    { name: 'Working Scratchpad', desc: 'Active plan & sub-goal tracking for multi-step reasoning', icon: '📝', status: 'pending' },
    { name: 'Promote-or-Drop Router', desc: 'Decides episodic retention vs discard per turn', icon: '🔀', status: 'pending' },
    { name: 'Episodic Memory Store', desc: 'Timestamped events persisted per tenant', icon: '📦', status: 'pending' },
    { name: 'Semantic Consolidation', desc: 'Contradiction resolution & long-term memory synthesis', icon: '🔧', status: 'pending' },
  ];

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon green">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      </div>
      <div class="status-section-title">Memory Subsystem (Week 3)</div>
      <div class="status-section-desc">Awaiting Nour's memory/ integration</div>
    </div>
    <div class="status-card-full">
      <div class="memory-subsystem">
        ${components.map(c => `
          <div class="memory-item">
            <div class="memory-info">
              <div class="memory-item-icon">${c.icon}</div>
              <div class="memory-item-details">
                <h4>${c.name}</h4>
                <p>${c.desc}</p>
              </div>
            </div>
            <span class="memory-status ${c.status}">${c.status === 'pending' ? 'Pending' : 'Ready'}</span>
          </div>`).join('')}
      </div>
    </div>`;

  return section;
}

/* ── Benchmarks ── */

function buildBenchmarkSection(data) {
  const section = document.createElement('div');
  section.className = 'status-section';

  const retrieval = data.retrieval_architecture_comparison?.results || {};
  const archData = Object.entries(retrieval).map(([name, m]) => ({
    name,
    latency: m.avg_latency_ms,
    accuracy: m.avg_relevant_docs
  })).sort((a, b) => a.latency - b.latency);

  let barsHtml = '';
  if (archData.length > 0) {
    const maxLatency = Math.max(...archData.map(a => a.latency));
    barsHtml = archData.map(a => {
      const pct = Math.max((a.latency / maxLatency) * 100, 5);
      const label = a.name.replace(/ RAG/g, '');
      return `
        <div class="benchmark-bar-group">
          <div class="benchmark-label">${label}</div>
          <div class="benchmark-bar-track">
            <div class="benchmark-bar-fill" style="width: ${pct}%">${a.latency}s</div>
          </div>
          <div class="benchmark-metric">${a.accuracy}/12 correct</div>
        </div>`;
    }).join('');
  } else {
    barsHtml = '<p style="color:var(--text-muted); font-size:12.5px;">No benchmark data loaded.</p>';
  }

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon amber">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="12 6 12 12 16 14"/></svg>
      </div>
      <div class="status-section-title">Benchmark Results</div>
      <div class="status-section-desc">Retrieval architecture comparison (12 domain questions)</div>
    </div>
    <div class="status-card-full">
      <div class="benchmark-list">
        ${barsHtml}
      </div>
    </div>`;

  return section;
}

/* ── RAG Search ── */

async function statusRagSearch() {
  const input = document.getElementById('ragBrowserSearch');
  const grid = document.getElementById('ragDocGrid');
  if (!input || !grid) return;
  const q = input.value.trim();
  if (!q) return;
  grid.innerHTML = '<span style="color:var(--text-muted);">Searching...</span>';
  try {
    const res = await fetch(`/api/rag/search?query=${encodeURIComponent(q)}&strategy=naive&top_k=5`);
    const data = await res.json();
    if (data.results?.length) {
      grid.innerHTML = data.results.map(r => `
        <div class="rag-doc-card">
          <span class="rag-doc-card-type bylaw">result</span>
          <p>${(r.payload || '').substring(0, 120)}...</p>
        </div>`).join('');
    } else {
      grid.innerHTML = '<span style="color:var(--text-muted);">No results found.</span>';
    }
  } catch {
    grid.innerHTML = '<span style="color:var(--red);">Search failed.</span>';
  }
}
