/* ═══════════════════════════════════════════════════════════════════════════
   What-If Simulations — Run Executive Scenarios
   ═══════════════════════════════════════════════════════════════════════════ */

const Simulations = {
  async load() {
    const view = document.getElementById('view-simulations');
    view.innerHTML = this.render();
    this.bindActions();
  },

  render() {
    return `
      <div class="section-header">
        <h3 class="section-title">What-If Scenarios</h3>
        <p style="color:var(--text-muted);font-size:0.875rem">Run executive-level simulations to forecast impact across the Golden Triangle.</p>
      </div>
      
      <div class="workflow-grid">
        <!-- Supply Chain Shock -->
        <div class="card workflow-card" style="border-top: 4px solid var(--danger)">
          <div class="workflow-card-header">
            <div>
              <div class="workflow-name" style="color:var(--danger)">🚢 The Supply Chain Shock</div>
              <div class="workflow-desc">Simulate a 4-week delay on major shipping routes (e.g., Red Sea blockage) and trace the Schedule & Cost impact.</div>
            </div>
            <span class="workflow-type-badge hitl">SCENARIO</span>
          </div>
          <button class="btn btn-primary btn-sm" data-sim="supply_chain_shock">
            ▶ Run Simulation
          </button>
          <div id="sim-result-supply_chain_shock" class="workflow-result" style="display:none;background:rgba(239, 68, 68, 0.05);border-color:rgba(239, 68, 68, 0.2)"></div>
        </div>
        
        <!-- Weather Event -->
        <div class="card workflow-card" style="border-top: 4px solid var(--accent)">
          <div class="workflow-card-header">
            <div>
              <div class="workflow-name" style="color:var(--accent)">🌪️ The Extreme Weather Event</div>
              <div class="workflow-desc">Simulate a Category 4 cyclone hitting the primary modular fabrication yard.</div>
            </div>
            <span class="workflow-type-badge hitl">SCENARIO</span>
          </div>
          <button class="btn btn-primary btn-sm" data-sim="extreme_weather">
            ▶ Run Simulation
          </button>
          <div id="sim-result-extreme_weather" class="workflow-result" style="display:none;background:rgba(6, 182, 212, 0.05);border-color:rgba(6, 182, 212, 0.2)"></div>
        </div>

        <!-- Labor Shortage -->
        <div class="card workflow-card" style="border-top: 4px solid var(--warning)">
          <div class="workflow-card-header">
            <div>
              <div class="workflow-name" style="color:var(--warning)">👷 The Labor Shortage</div>
              <div class="workflow-desc">Simulate only 60% mobilization of critical exotic-metal welders for the next quarter.</div>
            </div>
            <span class="workflow-type-badge hitl">SCENARIO</span>
          </div>
          <button class="btn btn-primary btn-sm" data-sim="labor_shortage">
            ▶ Run Simulation
          </button>
          <div id="sim-result-labor_shortage" class="workflow-result" style="display:none;background:rgba(234, 179, 8, 0.05);border-color:rgba(234, 179, 8, 0.2)"></div>
        </div>
      </div>
    `;
  },

  bindActions() {
    document.querySelectorAll('[data-sim]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const simId = btn.dataset.sim;
        btn.disabled = true;
        btn.textContent = '⏳ Simulating Cascade Impact...';
        
        const resultDiv = document.getElementById(`sim-result-${simId}`);
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<div class="loader">Querying 12 Agents... Generating Blast Radius...</div>';
        
        try {
          const res = await fetch('/api/simulations/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario_id: simId })
          });
          
          if (!res.ok) throw new Error(await res.text());
          const data = await res.json();
          
          resultDiv.innerHTML = `
            <div style="margin-bottom: 12px">
              <strong>Scenario:</strong> ${data.scenario}
            </div>
            <div style="display:flex;gap:12px;margin-bottom:12px">
              <div style="flex:1;background:rgba(255,255,255,0.05);padding:12px;border-radius:6px">
                <div style="color:var(--danger);font-size:1.5rem;font-weight:700">+${data.schedule_impact.critical_path_extended_days} Days</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">Critical Path Delay</div>
              </div>
              <div style="flex:1;background:rgba(255,255,255,0.05);padding:12px;border-radius:6px">
                <div style="color:var(--warning);font-size:1.5rem;font-weight:700">$${(data.cost_impact.total_exposure / 1000).toLocaleString()}k</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">Commercial Exposure</div>
              </div>
            </div>
            ${data.narrative ? `
            <div style="font-size:0.875rem;margin-bottom:12px;color:var(--text-main);line-height:1.5">
              <strong>Analysis:</strong> ${data.narrative}
            </div>` : ''}
            <div style="font-size:0.875rem;margin-bottom:12px">
              <strong>Blast Radius:</strong> ${data.affected_pos && data.affected_pos.length > 0 ? data.affected_pos.length + ' shipments delayed, ' : ''}pushing ${data.schedule_impact.new_critical_activities} activities onto the critical path. Threatens <strong>${data.schedule_impact.key_milestone_impacted}</strong>.
            </div>
            <div style="font-size:0.875rem;padding:8px;border-left:3px solid var(--accent);background:rgba(6, 182, 212, 0.1)">
              <strong>AI Recommendation:</strong> ${data.recommendation}
            </div>
          `;
          
        } catch (err) {
          resultDiv.textContent = 'Error: ' + err.message;
        } finally {
          btn.disabled = false;
          btn.textContent = '▶ Run Simulation Again';
        }
      });
    });
  }
};
