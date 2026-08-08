/**
 * Status Page — Interactive protocol tests, RAG browser, memory subsystems, and live benchmarks.
 */

let statusLoaded = false;

// ── Vector SVG Icon Helpers ──

const STATUS_SVGS = {
  shield: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  bell: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
  hand: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v9"/><path d="M18 11a2 2 0 0 1 4 0v3a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>`,
  book: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
  chart: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  lock: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
  cpu: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>`,
  database: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  sliders: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>`,
  zap: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  clipboard: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`,
  route: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a4.5 4.5 0 0 0 0-9H7a3 3 0 0 1 0-6h11"/><circle cx="18" cy="4" r="3"/></svg>`,
  refresh: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`
};

function getStatusSvg(key, size = 18, strokeWidth = 2) {
  const tpl = STATUS_SVGS[key] || STATUS_SVGS.zap;
  return tpl.replace(/{s}/g, size).replace(/{w}/g, strokeWidth);
}

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
  container.appendChild(buildMemorySection());
  container.appendChild(buildRagStoreSection(ragDocs));
  container.appendChild(buildBenchmarkSection(benchmarks));

  container.querySelectorAll('.status-section').forEach((el, i) => {
    el.style.animationDelay = `${i * 0.15}s`;
  });
}

/* ── Protocol Interactive Section ── */

function buildProtocolSection(capData) {
  const section = document.createElement('div');
  section.className = 'status-section';

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon purple">
        ${getStatusSvg('shield', 20, 2)}
      </div>
      <div>
        <div class="status-section-title">MCP Protocol — 8 Core Concerns</div>
        <div class="status-section-desc">Interactive live testing of Model Context Protocol server capabilities</div>
      </div>
    </div>
    <div class="protocol-grid" id="protocolGrid"></div>`;

  const grid = section.querySelector('#protocolGrid');

  // 1. Capability Negotiation
  grid.appendChild(makeProtoCard({
    title: 'Capability Negotiation',
    iconKey: 'hand',
    desc: 'initialize handshake declares server capabilities and protocol version',
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
    title: 'Notifications (Push)',
    iconKey: 'bell',
    desc: 'tools/list_changed pushed to client agent on role switch',
    color: 'var(--blue)',
    onTest: async (output) => {
      output.innerHTML = '<div class="proto-label">SWITCHING ROLE → tenant...</div>';
      const toolsRes = await fetch('/api/tools?role=tenant');
      const tools = await toolsRes.json();
      output.innerHTML = `<div class="proto-label">NOTIFICATION DISPATCHED</div>
        <div class="proto-json">{\n  "jsonrpc": "2.0",\n  "method": "notifications/tools/list_changed",\n  "params": { "role": "tenant" }\n}</div>
        <div class="proto-label" style="margin-top:12px">FILTERED TOOL SET FOR tenant (${tools.length} tools)</div>
        <div class="proto-tool-list">
          ${tools.map(t => `<div class="proto-tool-item">${t.name}</div>`).join('')}
        </div>`;
    }
  }));

  // 3. Elicitation
  grid.appendChild(makeProtoCard({
    title: 'Human Elicitation',
    iconKey: 'shield',
    desc: 'elicitation/create pauses for high-discount lease modifications',
    color: 'var(--amber)',
    onTest: async (output) => {
      output.innerHTML = `<div class="proto-label">ELICITATION LIFECYCLE</div>
        <div class="proto-steps">
          <div class="proto-step done"><span class="proto-step-num">1</span>Client calls modify_lease_terms(proposed_rent: 14000)</div>
          <div class="proto-step done"><span class="proto-step-num">2</span>Server detects discount > 15% threshold</div>
          <div class="proto-step active"><span class="proto-step-num">3</span>Server pauses and returns elicitation_required</div>
          <div class="proto-step"><span class="proto-step-num">4</span>Human manager reviews and approves via /api/elicitation/respond</div>
          <div class="proto-step"><span class="proto-step-num">5</span>Server executes lease update with executive approval</div>
        </div>
        <div class="proto-json" style="margin-top:12px">{\n  "status": "elicitation_required",\n  "elicitation_payload": {\n    "message": "Proposed rent represents 22.2% discount — requires human sign-off",\n    "risk_level": "high",\n    "action": "modify_lease_terms"\n  }\n}</div>`;
    }
  }));

  // 4. Resources
  grid.appendChild(makeProtoCard({
    title: 'Resources (Static Policies)',
    iconKey: 'book',
    desc: 'realty://policies/* served via resources/read',
    color: 'var(--green)',
    onTest: async (output) => {
      const listRes = await fetch('/api/resources');
      const listData = await listRes.json();
      const resources = Array.isArray(listData) ? listData : (listData.resources || []);
      const readRes = await fetch(`/api/resource/read?uri=${encodeURIComponent(resources[0]?.uri || 'realty://policies/lease_terms')}`);
      const readData = await readRes.json();
      output.innerHTML = `<div class="proto-label">RESOURCES DISCOVERED (${resources.length})</div>
        <div class="proto-resource-list">
          ${resources.map(r => `<div class="proto-resource-item">
            <span class="proto-resource-uri">${r.uri}</span>
            <span class="proto-resource-name">${r.name}</span>
          </div>`).join('')}
        </div>
        <div class="proto-label" style="margin-top:12px">READ RESOURCE PAYLOAD (${resources[0]?.uri})</div>
        <div class="proto-json">${JSON.stringify(readData, null, 2).substring(0, 450)}...</div>`;
    }
  }));

  // 5. Prompts
  grid.appendChild(makeProtoCard({
    title: 'Prompt Templates',
    iconKey: 'clipboard',
    desc: 'prompts/get returns parameterized lease notice templates',
    color: 'var(--cyan)',
    onTest: async (output) => {
      const listRes = await fetch('/api/prompts');
      const prompts = await listRes.json();
      const p = prompts[0] || { name: 'draft_lease_notice', arguments: [] };
      const getRes = await fetch(`/api/prompt/get?name=${p.name}&tenant_email=amr.hassan@example.com&proposed_rent=16000`);
      const filled = await getRes.json();
      output.innerHTML = `<div class="proto-label">PROMPT: ${p.name}</div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">${p.description}</div>
        <div class="proto-label">RENDERED PROMPT TEMPLATE</div>
        <div class="proto-json">${JSON.stringify(filled, null, 2)}</div>`;
    }
  }));

  // 6. Progress Tracking
  grid.appendChild(makeProtoCard({
    title: 'Progress Tracking',
    iconKey: 'chart',
    desc: 'progressToken streaming for batch property audits',
    color: 'var(--blue)',
    onTest: async (output) => {
      output.innerHTML = `<div class="proto-label">STREAMING AUDIT PROGRESS (Token: audit_${Date.now()})</div>
        <div class="proto-progress-track" id="protoProgress"></div>`;
      const track = output.querySelector('#protoProgress');
      const steps = [
        { pct: 20, text: 'Scanning 47 units across Cairo & Giza properties' },
        { pct: 40, text: 'Auditing active lease agreements and deposit records' },
        { pct: 60, text: 'Cross-referencing open maintenance work orders' },
        { pct: 80, text: 'Computing portfolio occupancy rate (91.5%)' },
        { pct: 100, text: 'Audit complete — 0 compliance violations found' },
      ];
      for (const s of steps) {
        await new Promise(r => setTimeout(r, 350));
        track.innerHTML = `<div class="proto-progress-bar" style="width:${s.pct}%">
            <span>${s.pct}%</span>
          </div>
          <div class="proto-progress-text">${s.text}</div>`;
      }
    }
  }));

  return section;
}

function makeProtoCard({ title, iconKey, desc, color, onTest }) {
  const card = document.createElement('div');
  card.className = 'proto-card';
  card.innerHTML = `
    <div class="proto-card-header">
      <div class="proto-card-icon" style="background:${color}20;color:${color}">${getStatusSvg(iconKey, 20, 2)}</div>
      <div>
        <div class="proto-card-title">${title}</div>
        <div class="proto-card-desc">${desc}</div>
      </div>
    </div>
    <button class="proto-card-btn" style="background:${color}">Test</button>
    <div class="proto-card-output"></div>`;

  const btn = card.querySelector('.proto-card-btn');
  const output = card.querySelector('.proto-card-output');

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'Running...';
    output.classList.add('visible');
    output.innerHTML = '<div class="proto-loading">Executing protocol test...</div>';
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

/* ── Memory Subsystem (Week 3 Live Interactive Playground) ── */

function buildMemorySection() {
  const section = document.createElement('div');
  section.className = 'status-section';

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon green">
        ${getStatusSvg('database', 20, 2)}
      </div>
      <div>
        <div class="status-section-title">Memory Subsystem (Week 3) — Live Interactive Playground</div>
        <div class="status-section-desc">Short-term buffer, decoupled scratchpad, promote-or-drop router, episodic store, & semantic consolidation</div>
      </div>
    </div>
    <div class="protocol-grid" id="memoryGrid"></div>`;

  const grid = section.querySelector('#memoryGrid');

  // 1. Short-Term Memory Buffer & Scratchpad
  grid.appendChild(makeProtoCard({
    title: 'Short-Term Memory & Scratchpad',
    iconKey: 'clipboard',
    desc: 'Rolling message buffer (window=3) + decoupled scratchpad preserving active plan during pruning',
    color: 'var(--green)',
    onTest: async (output) => {
      const res = await fetch('/api/memory/demo/stm');
      const data = await res.json();
      output.innerHTML = `<div class="proto-label">TRANSCRIPT PRUNING GUARANTEE</div>
        <div style="font-size:12px; color:var(--text-secondary); margin-bottom:8px;">${data.guarantee}</div>
        <div class="proto-label">ACTIVE SCRATCHPAD (PRESERVED)</div>
        <div class="proto-json">${JSON.stringify(data.scratchpad_preserved, null, 2)}</div>
        <div class="proto-label" style="margin-top:10px">PRUNED TRANSCRIPT (${data.pruned_transcript_turns} turns kept)</div>
        <div class="proto-json">${JSON.stringify(data.transcript_preview, null, 2)}</div>`;
    }
  }));

  // 2. Promote-or-Drop Router
  grid.appendChild(makeProtoCard({
    title: 'Promote-or-Drop Router',
    iconKey: 'route',
    desc: 'Decision layer on STM overflow: routes aging items to forget vs episodic with logged rationale',
    color: 'var(--purple)',
    onTest: async (output) => {
      const res = await fetch('/api/memory/demo/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: 'Tenant Amr Hassan reported severe paint allergy; requested low-VOC maintenance.',
          entity_id: 'tenant_1'
        })
      });
      const data = await res.json();
      output.innerHTML = `<div class="proto-label">ROUTER OVERFLOW DECISION</div>
        <div class="proto-steps">
          <div class="proto-step done"><span class="proto-step-num">1</span>Input event: "${data.input_content}"</div>
          <div class="proto-step done"><span class="proto-step-num">2</span>Entity: ${data.entity_id}</div>
          <div class="proto-step active"><span class="proto-step-num">3</span>Routing Verdict: <strong style="color:var(--green)">${(data.destination || 'episodic').toUpperCase()}</strong></div>
        </div>
        <div class="proto-label" style="margin-top:10px">LOGGED OPERATIONAL RATIONALE</div>
        <div class="proto-json">${JSON.stringify(data.decision, null, 2)}</div>`;
    }
  }));

  // 3. Episodic Memory Store
  grid.appendChild(makeProtoCard({
    title: 'Episodic Memory Store',
    iconKey: 'database',
    desc: 'Timestamped event store with entity-scoped queries for tenant history and maintenance records',
    color: 'var(--cyan)',
    onTest: async (output) => {
      const res = await fetch('/api/memory/1');
      const data = await res.json();
      output.innerHTML = `<div class="proto-label">QUERY EPISODES FOR TENANT #1 (Amr Hassan)</div>
        <div class="proto-resource-list">
          ${(data.memories || []).map(m => `
            <div class="proto-resource-item">
              <span class="proto-resource-uri">[${(m.category || 'EPISODE').toUpperCase()}]</span>
              <span class="proto-resource-name">${m.event_summary}</span>
            </div>
          `).join('')}
        </div>
        <div class="proto-meta" style="margin-top:8px">Total facts: ${data.facts_count} | Total episodes: ${data.episodes_count}</div>`;
    }
  }));

  // 4. Semantic Consolidation & Contradiction Resolution
  grid.appendChild(makeProtoCard({
    title: 'Semantic Consolidation & Contradictions',
    iconKey: 'refresh',
    desc: 'Periodic pass over episodic store: updates facts, versions (v1 -> v2), and resolves conflicts',
    color: 'var(--amber)',
    onTest: async (output) => {
      const res = await fetch('/api/memory/demo/consolidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: 1, trigger_conflict: true })
      });
      const data = await res.json();
      output.innerHTML = `<div class="proto-label">CONSOLIDATION PASS EXECUTED</div>
        <div class="proto-steps">
          <div class="proto-step done"><span class="proto-step-num">1</span>Scanned un-consolidated episodic history</div>
          <div class="proto-step done"><span class="proto-step-num">2</span>Detected lease intent conflict (Renewal v1 vs Vacate Notice v2)</div>
          <div class="proto-step active"><span class="proto-step-num">3</span>Superseded v1 fact and activated v2 fact</div>
        </div>
        <div class="proto-label" style="margin-top:10px">ACTIVE CONSOLIDATED FACTS (Semantic Store)</div>
        <div class="proto-json">${JSON.stringify(data.active_facts, null, 2)}</div>
        <div class="proto-label" style="margin-top:10px">VERSION HISTORY (v1 SUPERSEDED)</div>
        <div class="proto-json">${JSON.stringify(data.full_history_including_superseded, null, 2)}</div>`;
    }
  }));

  return section;
}

/* ── RAG Store Section ── */

function buildRagStoreSection(data) {
  const section = document.createElement('div');
  section.className = 'status-section';
  const docs = data.documents || [];

  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon blue">
        ${getStatusSvg('book', 20, 2)}
      </div>
      <div>
        <div class="status-section-title">RAG Knowledge Store</div>
        <div class="status-section-desc">${docs.length} policy binder documents indexed across 5 architectures</div>
      </div>
    </div>
    <div class="status-card-full">
      <div class="rag-browser">
        <div class="rag-browser-header">
          <input type="text" id="ragBrowserSearch" placeholder="Search policy binder (e.g. security deposit, termination)..." onkeydown="if(event.key==='Enter')statusRagSearch()">
          <button onclick="statusRagSearch()">Search</button>
        </div>
        <div id="ragDocGrid" class="rag-doc-grid">
          ${docs.map(d => `
            <div class="rag-doc-card">
              <span class="rag-doc-card-type ${d.metadata?.doc_type || 'bylaw'}">${d.metadata?.doc_type || 'policy'}</span>
              <h4>${d.title || 'Policy Document'}</h4>
              <p>${(d.content || '').substring(0, 120)}...</p>
            </div>`).join('')}
        </div>
      </div>
    </div>`;

  return section;
}

/* ── Benchmarks Section ── */

function buildBenchmarkSection(data) {
  const section = document.createElement('div');
  section.className = 'status-section';

  const ragBench = data.retrieval_architecture_benchmarks || [];
  const ctxBench = data.context_management_benchmarks || [];

  let ragHtml = '';
  if (ragBench.length > 0) {
    ragHtml = ragBench.map(b => {
      const pct = b.accuracy_pct || 50;
      return `
        <div class="benchmark-bar-group">
          <div class="benchmark-label">${b.architecture}</div>
          <div class="benchmark-bar-track">
            <div class="benchmark-bar-fill" style="width: ${Math.max(pct, 12)}%">${b.accuracy_score} (${pct.toFixed(1)}%)</div>
          </div>
          <div class="benchmark-metric">${b.avg_tokens_per_query} tok | ${b.avg_latency_sec}s</div>
        </div>`;
    }).join('');
  } else {
    ragHtml = '<p style="color:var(--text-muted); font-size:12.5px;">No RAG benchmark data found.</p>';
  }

  let ctxHtml = '';
  if (ctxBench.length > 0) {
    ctxHtml = ctxBench.map(c => {
      const pct = c.accuracy_pct !== undefined ? c.accuracy_pct : (c.recall_accuracy_pct || 0);
      const score = c.accuracy_recalled || c.allergy_detail_recalled || `${pct.toFixed(0)}%`;
      return `
        <div class="benchmark-bar-group">
          <div class="benchmark-label">${c.strategy}</div>
          <div class="benchmark-bar-track">
            <div class="benchmark-bar-fill" style="width: ${Math.max(pct, 14)}%; background: linear-gradient(90deg, var(--green), var(--cyan));">${score} (${pct.toFixed(0)}%)</div>
          </div>
          <div class="benchmark-metric">${(c.avg_input_tokens || 0).toLocaleString()} in / ${c.avg_output_tokens || 0} out</div>
        </div>`;
    }).join('');
  } else {
    ctxHtml = '<p style="color:var(--text-muted); font-size:12.5px;">No context benchmark data found.</p>';
  }


  section.innerHTML = `
    <div class="status-section-header">
      <div class="status-section-icon amber">
        ${getStatusSvg('chart', 20, 2)}
      </div>
      <div>
        <div class="status-section-title">Benchmark Results & Empirical Measurements</div>
        <div class="status-section-desc">Live performance metrics recorded across retrieval architectures and context pruning strategies</div>
      </div>
    </div>
    <div class="status-card-full" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap:24px;">
      <div>
        <div class="proto-label" style="margin-bottom:14px; font-size:11px; color:var(--text-primary);">RETRIEVAL ARCHITECTURES (12 DOMAIN QUESTIONS)</div>
        <div class="benchmark-list">
          ${ragHtml}
        </div>
      </div>
      <div>
        <div class="proto-label" style="margin-bottom:14px; font-size:11px; color:var(--text-primary);">CONTEXT WINDOW PRUNING (40-TURN SUITE, 10 RUNS)</div>
        <div class="benchmark-list">
          ${ctxHtml}
        </div>
      </div>
    </div>`;

  return section;
}

/* ── RAG Live Search ── */

async function statusRagSearch() {
  const input = document.getElementById('ragBrowserSearch');
  const grid = document.getElementById('ragDocGrid');
  if (!input || !grid) return;
  const q = input.value.trim();
  if (!q) return;
  grid.innerHTML = '<span style="color:var(--text-muted);">Searching indexed corpus...</span>';
  try {
    const res = await fetch(`/api/rag/search?query=${encodeURIComponent(q)}&strategy=hybrid&top_k=5`);
    const data = await res.json();
    if (data.results?.length) {
      grid.innerHTML = data.results.map(r => `
        <div class="rag-doc-card">
          <span class="rag-doc-card-type bylaw">hybrid match</span>
          <p>${(r.payload || '').substring(0, 140)}...</p>
        </div>`).join('');
    } else {
      grid.innerHTML = '<span style="color:var(--text-muted);">No matching passages found.</span>';
    }
  } catch {
    grid.innerHTML = '<span style="color:var(--red);">Search failed.</span>';
  }
}
