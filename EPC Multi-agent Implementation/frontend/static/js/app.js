/* ═══════════════════════════════════════════════════════════════════════════
   App.js — SPA router, state management, agent query handling
   ═══════════════════════════════════════════════════════════════════════════ */

const App = {
  currentView: 'dashboard',
  views: ['dashboard', 'graph', 'agents', 'workflows', 'hitl', 'simulations'],

  init() {
    this.bindNavigation();
    this.bindAgentQuery();
    this.bindModal();
    this.navigateFromHash();
    window.addEventListener('hashchange', () => this.navigateFromHash());

    // Load initial data
    Dashboard.load();
    AgentFeed.startSSE();
    HITLQueue.load();
  },

  bindNavigation() {
    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        this.switchView(el.dataset.view);
      });
    });
  },

  switchView(viewId) {
    if (!this.views.includes(viewId)) return;
    this.currentView = viewId;
    window.location.hash = viewId;

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-view="${viewId}"]`)?.classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${viewId}`)?.classList.add('active');

    // Update title
    const titles = {
      dashboard: 'Dashboard',
      graph: 'Knowledge Graph Explorer',
      agents: 'Agent Activity',
      workflows: 'Workflow Monitor',
      hitl: 'HITL Approval Queue',
      simulations: 'Executive View — What-If Simulations',
    };
    document.getElementById('page-title').textContent = titles[viewId] || '';

    // Lazy load views
    if (viewId === 'graph') GraphViz.load();
    if (viewId === 'workflows') WorkflowMonitor.load();
    if (viewId === 'hitl') HITLQueue.load();
    if (viewId === 'agents') AgentFeed.renderHistory();
    if (viewId === 'simulations') Simulations.load();
  },

  navigateFromHash() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    this.switchView(hash);
  },

  bindAgentQuery() {
    const input = document.getElementById('agent-query-input');
    const btn = document.getElementById('agent-query-btn');

    const send = async () => {
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      btn.disabled = true;
      btn.innerHTML = '<span style="animation:pulse 1s infinite">⏳</span>';

      try {
        const res = await fetch('/api/agents/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();
        this.showModal(data.response || JSON.stringify(data, null, 2));
      } catch (err) {
        this.showModal('Error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
      }
    };

    btn.addEventListener('click', send);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
  },

  bindModal() {
    document.getElementById('modal-close').addEventListener('click', () => {
      document.getElementById('agent-modal').classList.add('hidden');
    });
    document.getElementById('agent-modal').addEventListener('click', e => {
      if (e.target.id === 'agent-modal') {
        e.target.classList.add('hidden');
      }
    });
  },

  showModal(content) {
    document.getElementById('agent-modal-body').textContent = content;
    document.getElementById('agent-modal').classList.remove('hidden');
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
