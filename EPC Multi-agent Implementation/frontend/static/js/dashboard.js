/* ═══════════════════════════════════════════════════════════════════════════
   Dashboard — KPI cards, quick actions, activity preview
   ═══════════════════════════════════════════════════════════════════════════ */

const Dashboard = {
  async load() {
    const view = document.getElementById('view-dashboard');
    try {
      const res = await fetch('/api/dashboard/PRJ-001');
      const data = await res.json();
      view.innerHTML = this.render(data);
      this.bindActions();
    } catch (err) {
      view.innerHTML = `<div class="empty-state">Failed to load dashboard: ${err.message}</div>`;
    }
  },

  render(data) {
    const s = data.schedule || {};
    const p = data.procurement || {};
    const w = data.work_packages || {};
    const m = data.milestones || {};

    return `
      <div class="kpi-grid">
        <div class="card kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Schedule Progress</span>
            <div class="kpi-icon schedule">📅</div>
          </div>
          <div class="kpi-value" style="color: var(--accent)">${s.avg_pct_complete || 0}%</div>
          <div class="kpi-sub">${s.completed || 0}/${s.total_activities || 0} activities complete</div>
          <div class="kpi-change down">${s.critical_path_count || 0} critical path activities</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Procurement Status</span>
            <div class="kpi-icon procure">📦</div>
          </div>
          <div class="kpi-value" style="color: var(--purple)">${p.open_pos || 0}</div>
          <div class="kpi-sub">Open Purchase Orders</div>
          <div class="kpi-change ${p.material_slips > 0 ? 'down' : 'up'}">
            ${p.material_slips || 0} material slip${p.material_slips !== 1 ? 's' : ''} detected
          </div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">IWP Readiness</span>
            <div class="kpi-icon iwp">🔧</div>
          </div>
          <div class="kpi-value" style="color: var(--success)">${w.iwp_ready || 0}<span style="font-size:1.2rem;color:var(--text-muted)">/${w.total_iwps || 0}</span></div>
          <div class="kpi-sub">Work Packages Ready</div>
          <div class="kpi-change ${w.iwp_blocked > 0 ? 'down' : 'up'}">${w.iwp_blocked || 0} blocked</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Milestone Health</span>
            <div class="kpi-icon risk">${m.at_risk > 0 ? '⚠️' : '✅'}</div>
          </div>
          <div class="kpi-value" style="color: ${m.at_risk > 0 ? 'var(--warning)' : 'var(--success)'}">${m.at_risk || 0}</div>
          <div class="kpi-sub">Milestones At Risk</div>
          <div class="kpi-change up">${m.achieved || 0} of ${m.total || 0} achieved</div>
        </div>
      </div>

      <div class="quick-actions">
        <button class="btn btn-primary" data-action="delay-scan">⚡ Run Delay Scan</button>
        <button class="btn" data-action="iwp-check">🔍 Check IWP Readiness</button>
        <button class="btn" data-action="variance-check">📊 Schedule Variance</button>
        <button class="btn" data-action="supplier-scan">🔒 Supplier Risk Scan</button>
      </div>

      <div class="dashboard-grid">
        <div class="card" style="padding:20px">
          <div class="section-header">
            <h3 class="section-title">Recent Agent Activity</h3>
            <a href="#agents" class="btn btn-sm">View All →</a>
          </div>
          <div id="dashboard-feed" class="feed-container"></div>
        </div>

        <div class="card" style="padding:20px">
          <div class="section-header">
            <h3 class="section-title">Top Material Slips</h3>
          </div>
          ${this.renderSlips(p.top_slips || [])}
        </div>
      </div>
    `;
  },

  renderSlips(slips) {
    if (!slips.length) return '<div class="empty-state">No material slips detected ✅</div>';
    return slips.map(s => `
      <div class="feed-item">
        <div class="feed-icon" style="background:rgba(239,68,68,0.12);color:var(--danger)">⚠️</div>
        <div class="feed-body">
          <div class="feed-agent">${s.material_tag || s.material_id}</div>
          <div class="feed-action">${s.description || ''}</div>
          <div class="feed-detail">PO ${s.po_number} — ${s.slip_days} days late (need: ${s.need_date}, delivery: ${s.delivery_date})</div>
        </div>
      </div>
    `).join('');
  },

  formatQuickActionResult(action, data, queueData = null) {
    if (action === 'iwp-check') {
      const ready = data.ready_for_release || [];
      const blockers = data.blockers || [];
      const blockerLines = blockers.slice(0, 5).map(b => {
        const blockedBy = (b.blocked_by || []).join(', ') || 'Unknown';
        return `• ${b.iwp} (${b.discipline}) — blocked by ${blockedBy}`;
      });

      return [
        'IWP Readiness Summary',
        `Status: ${data.status || 'completed'}`,
        `Ready for release: ${data.iwps_ready || 0}`,
        `Blocked: ${data.iwps_blocked || 0}`,
        '',
        'Ready packages:',
        ...(ready.length ? ready.slice(0, 5).map(name => `• ${name}`) : ['• None']),
        '',
        'Top blockers:',
        ...(blockerLines.length ? blockerLines : ['• None']),
      ].join('\n');
    }

    if (action === 'variance-check') {
      const behind = data.variance_details || [];
      const topBehind = behind.slice(0, 5).map(item => {
        const variance = Math.abs(item.variance || 0).toFixed(1);
        const expected = item.expected_pct ?? 0;
        const actual = item.pct_complete ?? 0;
        return `• ${item.name}: ${actual}% actual vs ${expected}% expected (${variance}% behind)`;
      });

      return [
        'Schedule Variance Summary',
        `Status: ${data.status || 'completed'}`,
        `Activities behind plan: ${data.activities_behind || 0}`,
        `Low-float activities: ${data.low_float_activities || 0}`,
        '',
        'Most delayed activities:',
        ...(topBehind.length ? topBehind : ['• None']),
        '',
        'Recommended focus:',
        ...((data.recommendations || []).length ? data.recommendations.map(r => `• ${r}`) : ['• All activities are on track']),
      ].join('\n');
    }

    if (action === 'supplier-scan') {
      const pendingItems = (queueData?.pending || []).filter(
        item => item.workflow_name === 'Supplier Qualification Review'
      );
      const created = data.items_created || 0;
      const supplierLines = pendingItems.slice(0, 5).map(item => {
        const details = item.details || {};
        const linkedPos = (details.linked_pos || []).join(', ') || 'No linked POs';
        return `• ${details.supplier_name}: ${details.compliance_score}% compliance, ${details.qualification_status}, linked POs: ${linkedPos}`;
      });

      return [
        'Supplier Risk Scan',
        `New reviews created: ${created}`,
        `Suppliers currently flagged: ${pendingItems.length}`,
        '',
        ...(supplierLines.length
          ? ['Flagged suppliers:', ...supplierLines]
          : ['No suppliers are currently below the configured review threshold.']),
        '',
        created === 0 && pendingItems.length > 0
          ? 'No new items were created because these suppliers are already in the review queue.'
          : 'Review the pending supplier items in the HITL queue for approval decisions.',
      ].join('\n');
    }

    if (data.workflow) {
      return [
        `Workflow: ${data.workflow}`,
        `Status: ${data.status || 'completed'}`,
        JSON.stringify(data, null, 2),
      ].join('\n\n');
    }

    return JSON.stringify(data, null, 2);
  },

  bindActions() {
    document.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const action = btn.dataset.action;
        btn.disabled = true;
        const original = btn.innerHTML;
        btn.innerHTML = '⏳ Running...';

        const queries = {
          'delay-scan': 'procurement_delay_cascade',
          'iwp-check': 'document_readiness_check',
          'variance-check': 'schedule_variance_detection',
          'supplier-scan': 'supplier_qualification_review',
        };

        try {
          const wfId = queries[action];
          const res = await fetch(`/api/workflows/${wfId}/run`, { method: 'POST' });
          const data = await res.json();

          let queueData = null;
          if (action === 'supplier-scan') {
            const queueRes = await fetch('/api/hitl/queue');
            queueData = await queueRes.json();
          }

          App.showModal(this.formatQuickActionResult(action, data, queueData));

          // Refresh dashboard
          this.load();
          HITLQueue.load();
        } catch (err) {
          App.showModal('Error: ' + err.message);
        } finally {
          btn.disabled = false;
          btn.innerHTML = original;
        }
      });
    });

    // Load activity preview
    this.loadActivityPreview();
  },

  async loadActivityPreview() {
    try {
      const res = await fetch('/api/agents/activity/history');
      const data = await res.json();
      const container = document.getElementById('dashboard-feed');
      if (!container) return;
      const recent = data.slice(-8).reverse();
      if (!recent.length) {
        container.innerHTML = '<div class="empty-state">No agent activity yet</div>';
        return;
      }
      container.innerHTML = recent.map(e => `
        <div class="feed-item">
          <div class="feed-icon">${e.agent_icon || '🤖'}</div>
          <div class="feed-body">
            <div class="feed-agent">${e.agent_name}</div>
            <div class="feed-action">${e.action}</div>
          </div>
          <div class="feed-time">${new Date(e.timestamp).toLocaleTimeString()}</div>
        </div>
      `).join('');
    } catch (err) { /* ignore */ }
  },
};
