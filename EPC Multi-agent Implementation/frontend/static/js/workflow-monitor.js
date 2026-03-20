/* ═══════════════════════════════════════════════════════════════════════════
   Workflow Monitor — run and view workflow results
   ═══════════════════════════════════════════════════════════════════════════ */

const WorkflowMonitor = {
  async load() {
    const view = document.getElementById('view-workflows');
    try {
      const res = await fetch('/api/workflows/list');
      const data = await res.json();
      view.innerHTML = this.render(data);
      this.bindButtons();
    } catch (err) {
      view.innerHTML = `<div class="empty-state">Failed to load workflows: ${err.message}</div>`;
    }
  },

  render(data) {
    const autoCards = (data.autonomous || []).map(w => this.renderCard(w)).join('');
    const hitlCards = (data.hitl || []).map(w => this.renderCard(w)).join('');

    return `
      <div class="section-header">
        <h3 class="section-title">Autonomous Workflows</h3>
      </div>
      <div class="workflow-grid" style="margin-bottom:32px">${autoCards}</div>

      <div class="section-header">
        <h3 class="section-title">Human-in-the-Loop Workflows</h3>
      </div>
      <div class="workflow-grid">${hitlCards}</div>
    `;
  },

  renderCard(w) {
    return `
      <div class="card workflow-card">
        <div class="workflow-card-header">
          <div>
            <div class="workflow-name">${w.name}</div>
            <div class="workflow-desc">${w.description}</div>
          </div>
          <span class="workflow-type-badge ${w.type}">${w.type}</span>
        </div>
        <button class="btn btn-primary btn-sm" data-workflow="${w.id}" data-type="${w.type}">
          ${w.type === 'autonomous' ? '⚡ Run Now' : '🔔 Trigger Scan'}
        </button>
        <div id="result-${w.id}" class="workflow-result" style="display:none"></div>
      </div>
    `;
  },

  bindButtons() {
    document.querySelectorAll('[data-workflow]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const wfId = btn.dataset.workflow;
        btn.disabled = true;
        btn.textContent = '⏳ Running...';

        try {
          const res = await fetch(`/api/workflows/${wfId}/run`, { method: 'POST' });
          const data = await res.json();
          const resultDiv = document.getElementById(`result-${wfId}`);
          resultDiv.style.display = 'block';

          if (data.workflow) {
            resultDiv.textContent =
              `Status: ${data.status}\n` +
              `Steps: ${data.steps_completed || 'N/A'}\n\n` +
              (data.recommendations ? 'Recommendations:\n' + data.recommendations.join('\n') : '') +
              (data.blockers ? '\nBlockers:\n' + data.blockers.map(b => `• ${b.iwp}: ${b.blocked_by.join(', ')}`).join('\n') : '') +
              (data.ready_for_release ? '\nReady for Release:\n' + data.ready_for_release.map(r => `✅ ${r}`).join('\n') : '');
          } else if (data.items_created !== undefined) {
            resultDiv.textContent = `Created ${data.items_created} HITL item(s) for review.`;
            HITLQueue.load();
          } else {
            resultDiv.textContent = JSON.stringify(data, null, 2);
          }
        } catch (err) {
          document.getElementById(`result-${wfId}`).textContent = 'Error: ' + err.message;
        } finally {
          btn.disabled = false;
          btn.textContent = btn.dataset.type === 'autonomous' ? '⚡ Run Again' : '🔔 Trigger Scan';
        }
      });
    });
  },
};
