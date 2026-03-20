/* ═══════════════════════════════════════════════════════════════════════════
   Agent Feed — Real-time SSE activity stream
   ═══════════════════════════════════════════════════════════════════════════ */

const AgentFeed = {
  events: [],
  evtSource: null,

  startSSE() {
    if (this.evtSource) return;
    this.evtSource = new EventSource('/api/agents/activity');
    this.evtSource.addEventListener('activity', e => {
      try {
        const data = JSON.parse(e.data);
        this.events.push(data);
        if (App.currentView === 'agents') this.appendEntry(data);
        this.updateDashboardFeed(data);
      } catch (err) { /* ignore parse errors */ }
    });
    this.evtSource.onerror = () => {
      // Will auto-reconnect
    };
  },

  async renderHistory() {
    const view = document.getElementById('view-agents');
    try {
      const res = await fetch('/api/agents/activity/history');
      const data = await res.json();
      this.events = data;

      view.innerHTML = `
        <div class="agents-layout">
          <div class="section-header">
            <h3 class="section-title">Agent Activity Stream</h3>
            <div class="section-actions">
              <span class="kpi-sub">${data.length} events</span>
            </div>
          </div>
          <div class="card" style="padding:16px">
            <div id="agent-feed-list" class="feed-container" style="max-height:calc(100vh - 200px)"></div>
          </div>
        </div>
      `;

      const container = document.getElementById('agent-feed-list');
      if (!data.length) {
        container.innerHTML = '<div class="empty-state">No agent activity yet. Run a workflow or ask a question to see agents in action.</div>';
        return;
      }
      const reversed = [...data].reverse();
      container.innerHTML = reversed.map(e => this.renderEntry(e)).join('');
    } catch (err) {
      view.innerHTML = `<div class="empty-state">Failed to load activity: ${err.message}</div>`;
    }
  },

  renderEntry(e, isNew = false) {
    const time = new Date(e.timestamp).toLocaleTimeString();
    const detailHtml = e.detail ? `<div class="feed-detail">${this.escapeHtml(e.detail)}</div>` : '';
    const toolHtml = e.tool_calls?.length
      ? `<div class="feed-detail" style="color:var(--accent)">🔧 ${e.tool_calls.join(', ')}</div>`
      : '';
    return `
      <div class="feed-item ${isNew ? 'new' : ''}">
        <div class="feed-icon">${e.agent_icon || '🤖'}</div>
        <div class="feed-body">
          <div class="feed-agent">${e.agent_name || 'System'}</div>
          <div class="feed-action">${this.escapeHtml(e.action || '')}</div>
          ${detailHtml}
          ${toolHtml}
        </div>
        <div class="feed-time">${time}</div>
      </div>
    `;
  },

  appendEntry(e) {
    const container = document.getElementById('agent-feed-list');
    if (!container) return;
    // Remove empty state
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
    container.insertAdjacentHTML('afterbegin', this.renderEntry(e, true));
  },

  updateDashboardFeed(e) {
    const container = document.getElementById('dashboard-feed');
    if (!container) return;
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
    // Keep max 8 items
    while (container.children.length >= 8 && container.lastChild) {
      container.removeChild(container.lastChild);
    }
    container.insertAdjacentHTML('afterbegin', `
      <div class="feed-item new">
        <div class="feed-icon">${e.agent_icon || '🤖'}</div>
        <div class="feed-body">
          <div class="feed-agent">${e.agent_name}</div>
          <div class="feed-action">${this.escapeHtml(e.action || '')}</div>
        </div>
        <div class="feed-time">${new Date(e.timestamp).toLocaleTimeString()}</div>
      </div>
    `);
  },

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },
};
