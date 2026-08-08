/**
 * Showcase Page — Premium System Presentation, Visual Enhancements, Benchmarks & Animations.
 */

let showcaseLoaded = false;

// ── Vector SVG Icon Dictionary (Pure Vector — Zero Emojis) ──

const SVG_ICONS = {
  shield: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  bell: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
  hand: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v9"/><path d="M18 11a2 2 0 0 1 4 0v3a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>`,
  book: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
  chart: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  lock: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
  cpu: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>`,
  layout: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>`,
  git: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg>`,
  database: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  sliders: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>`,
  users: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  check: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  zap: `<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`
};

function getSvgIcon(name, size = 20, strokeWidth = 2) {
  const tpl = SVG_ICONS[name] || SVG_ICONS.zap;
  return tpl.replace(/{s}/g, size).replace(/{w}/g, strokeWidth);
}

// ── Interactive Toast Feedback ──

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${type === 'success' ? getSvgIcon('check', 14, 2.5) : getSvgIcon('zap', 14, 2.5)}</div>
    <div class="toast-message">${message}</div>
  `;
  toastContainer.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

// ── Smooth Counter Animation Engine ──

function animateCounter(el, targetStr, duration = 1200) {
  const hasPercent = targetStr.includes('%');
  const cleanTarget = parseFloat(targetStr.replace('%', ''));
  const isFloat = String(cleanTarget).includes('.');
  let startTimestamp = null;

  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    // Cubic ease-out curve
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const currentVal = easeProgress * cleanTarget;

    if (isFloat) {
      el.textContent = currentVal.toFixed(1) + (hasPercent ? '%' : '');
    } else {
      el.textContent = Math.floor(currentVal) + (hasPercent ? '%' : '');
    }

    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      el.textContent = targetStr;
    }
  };

  requestAnimationFrame(step);
}

// ── Scroll Reveal Observer ──

function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        
        // Trigger counter animation if element has [data-counter]
        const counters = entry.target.querySelectorAll('[data-counter]');
        counters.forEach(c => {
          if (!c.dataset.animated) {
            c.dataset.animated = 'true';
            animateCounter(c, c.dataset.counter);
          }
        });

        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.showcase-section, .hero-stat, .feature-card, .arch-card, .timeline-item, .team-card').forEach(el => {
    el.classList.add('reveal-on-scroll');
    observer.observe(el);
  });
}

// ── Core Showcase Loader ──

async function loadShowcasePage() {
  if (showcaseLoaded) return;
  showcaseLoaded = true;

  const benchmarks = await fetchShowcaseBenchmarks();
  renderHeroStats();
  renderShowcaseContent(benchmarks);

  requestAnimationFrame(() => {
    initScrollReveal();
  });
}

async function fetchShowcaseBenchmarks() {
  try {
    const res = await fetch('/api/benchmarks');
    return await res.json();
  } catch { return {}; }
}

// ── Hero Stats Render ──

function renderHeroStats() {
  const container = document.getElementById('heroStats');
  if (!container) return;

  const stats = [
    { value: '79', label: 'Tests Passing' },
    { value: '5', label: 'RAG Architectures' },
    { value: '8', label: 'MCP Protocol Concerns' },
    { value: '16', label: 'Subsystems Built' },
    { value: '3', label: 'Contributors' },
  ];

  container.innerHTML = stats.map(s => `
    <div class="hero-stat reveal-on-scroll">
      <div class="hero-stat-value" data-counter="${s.value}">0</div>
      <div class="hero-stat-label">${s.label}</div>
    </div>`).join('');
}

// ── Main Section Renders ──

function renderShowcaseContent(benchmarks) {
  const container = document.getElementById('showcaseContent');
  if (!container) return;
  container.innerHTML = '';

  container.appendChild(buildEvolutionSection());
  container.appendChild(buildRagSection(benchmarks));
  container.appendChild(buildContextSection(benchmarks));
  container.appendChild(buildFeaturesSection());
  container.appendChild(buildTeamSection());
}

// 1. Evolution Section
function buildEvolutionSection() {
  const section = document.createElement('div');
  section.className = 'showcase-section';
  section.innerHTML = `
    <div class="showcase-section-header">
      <div class="showcase-section-icon week2">
        ${getSvgIcon('git', 20, 2)}
      </div>
      <div>
        <div class="showcase-section-title">System Evolution</div>
        <div class="showcase-section-subtitle">From Week 2 MCP foundations to Week 3 autonomous RAG</div>
      </div>
    </div>
    <div class="evolution-timeline">
      <div class="timeline-item completed">
        <div class="watermark-icon">${getSvgIcon('shield', 96, 1.5)}</div>
        <div class="timeline-week">Week 2 — Foundation</div>
        <div class="timeline-title">MCP Server with 8 Protocol Concerns</div>
        <div class="timeline-desc">Built the core FastMCP server with capability negotiation, notifications, human elicitation, resources, prompts, progress tracking, defensive Pydantic schemas, and dual transport (stdio + HTTP). SQLite-backed chat persistence, provider-agnostic LLM engine (10+ models via LiteLLM), and interactive web portal.</div>
      </div>
      <div class="timeline-item completed">
        <div class="watermark-icon">${getSvgIcon('database', 96, 1.5)}</div>
        <div class="timeline-week">Week 3 — Memory & RAG</div>
        <div class="timeline-title">5 RAG Architectures + Memory Subsystems</div>
        <div class="timeline-desc">Implemented Naive, Hybrid (BM25+RRF), Agentic (multi-hop), and Graph RAG with vector store. Added short-term memory buffer, scratchpad, episodic store, semantic consolidation with contradiction resolution. 4 context pruning strategies benchmarked across 40-turn test suite. Self-RAG verification with [IsRel] and [IsSup] critique tokens.</div>
      </div>
      <div class="timeline-item completed">
        <div class="watermark-icon">${getSvgIcon('check', 96, 1.5)}</div>
        <div class="timeline-week">Integration</div>
        <div class="timeline-title">Unified Web Portal with All Subsystems</div>
        <div class="timeline-desc">Merged all subsystems into a single interactive web application. RAG strategy selector in chat, live benchmark display, system status dashboard. 79/79 tests passing across all modules.</div>
      </div>
    </div>`;
  return section;
}


// 2. RAG Section
function buildRagSection(benchmarks) {
  const section = document.createElement('div');
  section.className = 'showcase-section';

  const archCards = [
    { key: 'naive', name: 'Naive RAG', accuracy: '66.7%', val: 'mid', iconKey: 'database', tradeoff: 'Simplest — dense vector baseline, no keyword matching', color: 'blue' },
    { key: 'hybrid', name: 'Hybrid Search', accuracy: '75.0%', val: 'mid', iconKey: 'sliders', tradeoff: 'BM25 statute bonus lifts citation-heavy queries', color: 'indigo' },
    { key: 'agentic', name: 'Agentic RAG', accuracy: '91.7%', val: 'best', iconKey: 'cpu', tradeoff: 'Multi-hop decomposition wins on complex questions', color: 'green', best: true },
    { key: 'graph', name: 'Graph RAG', accuracy: '16.7%', val: 'low', iconKey: 'git', tradeoff: 'Bonus: entity traversal, needs richer knowledge graph', color: 'purple' },
  ];

  section.innerHTML = `
    <div class="showcase-section-header">
      <div class="showcase-section-icon week3">
        ${getSvgIcon('database', 20, 2)}
      </div>
      <div>
        <div class="showcase-section-title">RAG Architectures</div>
        <div class="showcase-section-subtitle">5 retrieval strategies benchmarked across 12 domain questions</div>
      </div>
    </div>
    <div class="arch-comparison">
      ${archCards.map(a => `
        <div class="arch-card ${a.best ? 'best' : ''}" onclick="showToast('Selected Architecture: ${a.name} (${a.accuracy} accuracy)', 'success')">
          <div class="watermark-icon">${getSvgIcon(a.iconKey, 88, 1.5)}</div>
          <div class="arch-card-name">${a.name}</div>
          <div class="arch-card-accuracy ${a.val === 'best' ? 'best-val' : a.val === 'mid' ? 'mid-val' : 'low-val'}" data-counter="${a.accuracy}">0.0%</div>
          <div class="arch-card-label">Accuracy</div>
          <div class="arch-card-tradeoff">${a.tradeoff}</div>
        </div>`).join('')}
    </div>

    <div style="margin-top:24px;">
      <div class="benchmark-table-wrapper">
        <table class="benchmark-table">
          <thead>
            <tr>
              <th>Architecture</th>
              <th>Accuracy</th>
              <th>Avg Tokens</th>
              <th>Avg Latency</th>
              <th>Key Tradeoff</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Naive RAG</td><td>8/12 (66.7%)</td><td>175</td><td class="dim">&lt;0.001s</td><td class="dim">Simplest, no keyword matching</td></tr>
            <tr><td>Hybrid Search</td><td>9/12 (75.0%)</td><td>210</td><td>0.001s</td><td>Adds BM25 statute bonus</td></tr>
            <tr><td class="highlight">Agentic RAG</td><td class="highlight">11/12 (91.7%)</td><td>391</td><td>0.001s</td><td>Query decomposition wins on complex questions</td></tr>
            <tr><td>Graph RAG</td><td>2/12 (16.7%)</td><td>17</td><td class="dim">&lt;0.001s</td><td class="dim">Bonus: structured traversal, needs richer KG</td></tr>
          </tbody>
        </table>
      </div>
    </div>`;
  return section;
}

// 3. Context Management Section
function buildContextSection(benchmarks) {
  const section = document.createElement('div');
  section.className = 'showcase-section';

  section.innerHTML = `
    <div class="showcase-section-header">
      <div class="showcase-section-icon week3">
        ${getSvgIcon('sliders', 20, 2)}
      </div>
      <div>
        <div class="showcase-section-title">Context Window Management</div>
        <div class="showcase-section-subtitle">4 pruning strategies across 40-turn test suite (10 variations)</div>
      </div>
    </div>
    <div class="benchmark-table-wrapper">
      <table class="benchmark-table">
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Recall Accuracy</th>
            <th>Avg Input Tokens</th>
            <th>Avg Output Tokens</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Sliding Window (Last 10)</td><td>0/10 (0%)</td><td>2365</td><td>120</td></tr>
          <tr><td class="highlight">Observation Masking (Keep 3 Tools)</td><td class="highlight">10/10 (100%)</td><td class="highlight">1984</td><td>200</td></tr>
          <tr><td>Recursive Summarization</td><td>4/10 (40%)</td><td>2281</td><td>152</td></tr>
          <tr><td>Zone-Based Pruning</td><td>0/10 (0%)</td><td>2623</td><td>120</td></tr>
        </tbody>
      </table>
    </div>
    <p style="margin-top:12px; font-size:12.5px; color:var(--text-secondary); line-height:1.6;">
      <strong style="color:var(--green)">Key Insight:</strong> Observation Masking achieves 100% recall at the lowest token cost because tool JSON output is the primary context bloat — not dialogue. Masking older tool responses preserves the critical early constraint while removing 80%+ of token volume.
    </p>`;
  return section;
}

// 4. Features Section (With Interactive Category Filtering)
function buildFeaturesSection() {
  const section = document.createElement('div');
  section.className = 'showcase-section';

  const features = [
    { cat: 'protocol', iconKey: 'shield', title: 'Capability Negotiation', desc: 'Server declares elicitation, tools/listChanged, sampling, resources, and progress support during initialize handshake.', color: 'indigo', file: 'server.py' },
    { cat: 'protocol', iconKey: 'bell', title: 'Live Notifications', desc: 'Server pushes notifications/tools/list_changed when user role changes, updating client toolset dynamically.', color: 'blue', file: 'notifications.py' },
    { cat: 'protocol', iconKey: 'hand', title: 'Human Elicitation', desc: 'High-risk lease modifications trigger elicitation/create mid-call, pausing for executive approval.', color: 'red', file: 'server.py' },
    { cat: 'protocol', iconKey: 'book', title: 'Resources & Prompts', desc: 'Static policy documents as resources, parameterized templates for notice drafting.', color: 'green', file: 'resources/' },
    { cat: 'protocol', iconKey: 'chart', title: 'Progress Tracking', desc: 'Batch property compliance audits report step-by-step percentage progress via progressToken.', color: 'amber', file: 'progress.py' },
    { cat: 'protocol', iconKey: 'lock', title: 'Defensive Schemas', desc: 'Strict Pydantic with extra="forbid", parameter bounds, and server-side authorization.', color: 'purple', file: 'server.py' },
    { cat: 'llm', iconKey: 'cpu', title: 'Provider-Agnostic LLM', desc: '10+ models via LiteLLM — Gemini, Mistral, CodeStral, Gemma. Streaming and non-streaming modes.', color: 'blue', file: 'llm_engine.py' },
    { cat: 'llm', iconKey: 'layout', title: 'Interactive Web Portal', desc: 'Dark-mode glassmorphism UI with SSE streaming, tool tracing, elicitation cards, and SQLite persistence.', color: 'indigo', file: 'web/' },
  ];

  section.innerHTML = `
    <div class="showcase-section-header" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="showcase-section-icon team">
          ${getSvgIcon('layout', 20, 2)}
        </div>
        <div>
          <div class="showcase-section-title">MCP Server Features</div>
          <div class="showcase-section-subtitle">Production-grade protocol implementation with 8 concerns</div>
        </div>
      </div>
      <div class="feature-filter-pills">
        <button class="filter-pill active" onclick="filterFeatures('all', this)">All</button>
        <button class="filter-pill" onclick="filterFeatures('protocol', this)">Protocol</button>
        <button class="filter-pill" onclick="filterFeatures('llm', this)">LLM & UI</button>
      </div>
    </div>
    <div class="feature-grid" id="featureGrid">
      ${features.map(f => `
        <div class="feature-card" data-category="${f.cat}" onclick="showToast('Inspecting: ${f.title} (${f.file})', 'info')">
          <div class="watermark-icon">${getSvgIcon(f.iconKey, 92, 1.5)}</div>
          <div class="feature-card-icon ${f.color}">${getSvgIcon(f.iconKey, 20, 2)}</div>
          <h3>${f.title}</h3>
          <p>${f.desc}</p>
          <span class="file-tag">${f.file}</span>
        </div>`).join('')}
    </div>`;
  return section;
}

function filterFeatures(cat, btnEl) {
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const cards = document.querySelectorAll('.feature-card');
  cards.forEach(card => {
    if (cat === 'all' || card.dataset.category === cat) {
      card.style.display = 'block';
      requestAnimationFrame(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0) scale(1)';
      });
    } else {
      card.style.opacity = '0';
      card.style.transform = 'scale(0.95)';
      setTimeout(() => { card.style.display = 'none'; }, 200);
    }
  });
}

// 5. Team Section
function buildTeamSection() {
  const section = document.createElement('div');
  section.className = 'showcase-section';

  const members = [
    {
      name: 'Abdallah Saber', role: 'Team Lead & RAG Architect', avatar: 'AS', cls: 'a1', iconKey: 'cpu',
      contributions: [
        'FastMCP Server Core & 8 Protocol Concerns',
        'LLM Engine (10+ models via LiteLLM)',
        'Web App & Interactive Chat Portal',
        'Vector DB, Naive/Hybrid/Agentic/Graph RAG',
        'Master Benchmarks & README',
      ]
    },
    {
      name: 'Nour Salem', role: 'Memory Systems Lead', avatar: 'NS', cls: 'a2', iconKey: 'database',
      contributions: [
        'Short-Term Memory Buffer & Scratchpad',
        'Promote-or-Drop Router',
        'Episodic Memory Store',
        'Semantic Consolidation Engine',
        'Contradiction Resolution',
      ]
    },
    {
      name: 'Ahmed Wael', role: 'Protocol & Eval Lead', avatar: 'AW', cls: 'a3', iconKey: 'shield',
      contributions: [
        'MCP Client Agent & Notifications',
        'Progress Tracking Implementation',
        '4 Context Pruning Strategies',
        '40-Turn Long-Context Test Suite',
        'Self-RAG Verification & Retrieval Eval',
      ]
    },
  ];

  section.innerHTML = `
    <div class="showcase-section-header">
      <div class="showcase-section-icon team">
        ${getSvgIcon('users', 20, 2)}
      </div>
      <div>
        <div class="showcase-section-title">Team</div>
        <div class="showcase-section-subtitle">Cornerstone Realty Group B — 3 contributors, 16 subsystems</div>
      </div>
    </div>
    <div class="team-grid">
      ${members.map(m => `
        <div class="team-card" onclick="showToast('Contributor: ${m.name} (${m.role})', 'info')">
          <div class="watermark-icon">${getSvgIcon(m.iconKey, 96, 1.5)}</div>
          <div class="team-avatar ${m.cls}">${m.avatar}</div>
          <div class="team-name">${m.name}</div>
          <div class="team-role">${m.role}</div>
          <ul class="team-contributions">
            ${m.contributions.map(c => `<li>${c}</li>`).join('')}
          </ul>
        </div>`).join('')}
    </div>`;
  return section;
}
