/**
 * App Shell — Page switching, URL routing, sidebar, initialization.
 */

let activePage = 'chat';
let activeSessionId = localStorage.getItem('cornerstone_active_session_id') || null;
let sidebarCollapsed = localStorage.getItem('cornerstone_sidebar_collapsed') === 'true';
let isSwitchingPage = false;

// ── URL Routing ──

function parseHash() {
  const hash = window.location.hash;
  if (!hash || hash === '#' || hash === '#/') {
    const savedPage = localStorage.getItem('cornerstone_page') || 'chat';
    const savedSessionId = localStorage.getItem('cornerstone_active_session_id');
    return {
      page: savedPage,
      params: new URLSearchParams(savedSessionId && savedPage === 'chat' ? `session=${savedSessionId}` : '')
    };
  }
  const [path, queryStr] = hash.slice(1).split('?');
  const pathParts = path.split('/').filter(Boolean);
  const page = pathParts[0] || localStorage.getItem('cornerstone_page') || 'chat';
  const params = new URLSearchParams(queryStr || '');
  return { page, params };
}

function updateURL(page, sessionId) {
  let hash = '#/' + page;
  if (page === 'chat' && sessionId) {
    hash += '?session=' + sessionId;
  }
  if (window.location.hash !== hash) {
    window.location.hash = hash;
  }
}

function onHashChange() {
  if (isSwitchingPage) return;
  const { page, params } = parseHash();
  const sessionId = params.get('session');
  if (page === 'chat' && sessionId && sessionId !== activeSessionId) {
    activeSessionId = sessionId;
    localStorage.setItem('cornerstone_active_session_id', sessionId);
  }
  switchPage(page, false);
}

// ── Page Switching ──

function switchPage(page, updateHash = true) {
  isSwitchingPage = true;
  activePage = page;
  localStorage.setItem('cornerstone_page', page);

  if (updateHash) {
    if (page === 'chat') {
      updateURL(page, activeSessionId);
    } else {
      updateURL(page, null);
    }
  }

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  const target = document.getElementById('page-' + page);
  const btn = document.querySelector(`.nav-btn[data-page="${page}"]`);
  if (target) target.classList.add('active');
  if (btn) btn.classList.add('active');

  const chatSection = document.getElementById('chatHistorySection');
  if (chatSection) {
    chatSection.classList.toggle('hidden', page !== 'chat');
  }

  if (page === 'status') loadStatusPage();
  if (page === 'showcase') loadShowcasePage();
  if (page === 'chat') fetchChatSessions();

  requestAnimationFrame(() => { isSwitchingPage = false; });
}

// ── Sidebar Toggle ──

function positionToggle() {
  const toggle = document.getElementById('sidebarToggle');
  const newChat = document.querySelector('.sidebar-new-chat');
  if (!toggle || !newChat) return;
  const rect = newChat.getBoundingClientRect();
  toggle.style.top = (rect.bottom) + 'px';
}

function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
  localStorage.setItem('cornerstone_sidebar_collapsed', sidebarCollapsed);
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.toggle('collapsed', sidebarCollapsed);
  requestAnimationFrame(positionToggle);
}

// ── Init ──

document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  if (sidebar && sidebarCollapsed) sidebar.classList.add('collapsed');

  const { page, params } = parseHash();
  const sessionId = params.get('session') || localStorage.getItem('cornerstone_active_session_id');
  if (sessionId) {
    activeSessionId = sessionId;
    localStorage.setItem('cornerstone_active_session_id', sessionId);
  }

  switchPage(page, true);

  // Remove initial load animation block after first frame paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.body.classList.remove('no-animation');
    });
  });

  initModelDropdown();
  fetchPersonas().then(() => fetchTenantMemories());
  if (page !== 'chat') {
    fetchChatSessions();
  }

  positionToggle();
  window.addEventListener('resize', positionToggle);

  window.addEventListener('hashchange', onHashChange);
});


