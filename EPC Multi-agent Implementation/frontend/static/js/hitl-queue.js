/* ═══════════════════════════════════════════════════════════════════════════
   HITL Queue — approve / reject pending items
   ═══════════════════════════════════════════════════════════════════════════ */

const HITLQueue = {
  async load() {
    const view = document.getElementById('view-hitl');
    try {
      const res = await fetch('/api/hitl/queue');
      const data = await res.json();
      const pending = data.pending || [];
      const resolved = data.resolved || [];

      // Update badge
      const badge = document.getElementById('hitl-badge');
      badge.textContent = pending.length;
      badge.style.display = pending.length > 0 ? 'inline' : 'none';

      view.innerHTML = this.render(pending, resolved);
      this.bindActions();
    } catch (err) {
      view.innerHTML = `<div class="empty-state">Failed to load HITL queue: ${err.message}</div>`;
    }
  },

  render(pending, resolved) {
    const pendingHtml = pending.length
      ? `<div class="hitl-grid">${pending.map(i => this.renderCard(i)).join('')}</div>`
      : '<div class="empty-state"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>No pending approvals — all clear!</div>';

    const resolvedHtml = resolved.length
      ? `<div class="resolved-section">
          <div class="section-header"><h3 class="section-title">Resolved (${resolved.length})</h3></div>
          <div class="hitl-grid">${resolved.map(i => this.renderCard(i, true)).join('')}</div>
        </div>`
      : '';

    return `
      <div class="section-header">
        <h3 class="section-title">Pending Approvals (${pending.length})</h3>
        <div class="section-actions">
          <button class="btn btn-sm" onclick="HITLQueue.load()">🔄 Refresh</button>
        </div>
      </div>
      ${pendingHtml}
      ${resolvedHtml}
    `;
  },

  renderCard(item, isResolved = false) {
    const details = item.details || {};
    const detailRows = Object.entries(details)
      .filter(([k]) => k !== 'recommendation' && k !== 'options' && k !== 'constraints')
      .map(([k, v]) => {
        const displayVal = typeof v === 'number' && k.includes('value')
          ? `$${v.toLocaleString()}`
          : v;
        return `<div class="hitl-detail-row"><span class="hitl-detail-key">${k.replace(/_/g, ' ')}</span><span class="hitl-detail-val">${displayVal}</span></div>`;
      }).join('');

    const actionsHtml = item.status === 'pending' ? `
      <div class="hitl-actions">
        <button class="btn btn-success btn-sm" data-approve="${item.id}">✅ Approve</button>
        <button class="btn btn-danger btn-sm" data-reject-show="${item.id}">❌ Reject</button>
      </div>
      <div class="hitl-reject-reason" id="reject-${item.id}">
        <textarea placeholder="Reason for rejection..."></textarea>
        <div style="display:flex;gap:8px;margin-top:6px">
          <button class="btn btn-danger btn-sm" data-reject-confirm="${item.id}">Confirm Reject</button>
          <button class="btn btn-sm" data-reject-cancel="${item.id}">Cancel</button>
        </div>
      </div>
    ` : `
      <div style="font-size:0.72rem;color:var(--text-muted);margin-top:8px">
        ${item.status === 'approved' ? '✅' : '❌'} ${item.status} by ${item.resolved_by || 'System'}
        ${item.rejection_reason ? `<br>Reason: ${item.rejection_reason}` : ''}
        ${item.resolved_at ? `<br>${new Date(item.resolved_at).toLocaleString()}` : ''}
      </div>
    `;

    return `
      <div class="card hitl-card ${isResolved ? 'resolved' : ''}">
        <div class="hitl-card-header">
          <div>
            <div class="hitl-title">${item.title}</div>
            <div class="hitl-agent">Requested by: ${item.requesting_agent}</div>
          </div>
          <span class="hitl-status-badge ${item.status}">${item.status}</span>
        </div>
        <div class="hitl-summary">${item.summary}</div>
        ${item.impact ? `<div class="hitl-impact">⚡ ${item.impact}</div>` : ''}
        <div class="hitl-details-toggle" data-toggle="${item.id}">▶ View Details</div>
        <div class="hitl-details" id="details-${item.id}">${detailRows}</div>
        ${actionsHtml}
      </div>
    `;
  },

  bindActions() {
    // Detail toggles
    document.querySelectorAll('.hitl-details-toggle').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.dataset.toggle;
        const details = document.getElementById(`details-${id}`);
        details.classList.toggle('open');
        el.textContent = details.classList.contains('open') ? '▼ Hide Details' : '▶ View Details';
      });
    });

    // Approve
    document.querySelectorAll('[data-approve]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.approve;
        btn.disabled = true;
        btn.textContent = '⏳...';
        try {
          await fetch(`/api/hitl/${id}/approve`, { method: 'POST' });
          this.load();
          Dashboard.load();
        } catch (err) {
          alert('Error: ' + err.message);
        }
      });
    });

    // Show reject form
    document.querySelectorAll('[data-reject-show]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.rejectShow;
        document.getElementById(`reject-${id}`).style.display = 'block';
      });
    });

    // Cancel reject
    document.querySelectorAll('[data-reject-cancel]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.rejectCancel;
        document.getElementById(`reject-${id}`).style.display = 'none';
      });
    });

    // Confirm reject
    document.querySelectorAll('[data-reject-confirm]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.rejectConfirm;
        const reason = document.querySelector(`#reject-${id} textarea`).value;
        btn.disabled = true;
        btn.textContent = '⏳...';
        try {
          await fetch(`/api/hitl/${id}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason }),
          });
          this.load();
          Dashboard.load();
        } catch (err) {
          alert('Error: ' + err.message);
        }
      });
    });
  },
};
