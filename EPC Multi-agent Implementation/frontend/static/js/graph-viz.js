/* ═══════════════════════════════════════════════════════════════════════════
   Graph Visualization — D3.js force-directed knowledge graph
   ═══════════════════════════════════════════════════════════════════════════ */

const GraphViz = {
  loaded: false,
  simulation: null,
  showCriticalPath: true,
  activeFilters: new Set(['Project','Phase','Activity','Milestone','Supplier','PurchaseOrder','Material','Document','WorkPackage','Equipment','WBS']),

  NODE_COLORS: {
    Project:       '#06b6d4',
    Phase:         '#3b82f6',
    Activity:      '#10b981',
    Milestone:     '#f59e0b',
    Supplier:      '#f97316',
    PurchaseOrder: '#ef4444',
    Material:      '#8b5cf6',
    Document:      '#ec4899',
    WorkPackage:   '#14b8a6',
    Equipment:     '#a855f7',
    WBS:           '#6366f1',
  },

  async load() {
    if (this.loaded) return;
    const view = document.getElementById('view-graph');
    try {
      const res = await fetch('/api/graph/PRJ-001/critical-path');
      const data = await res.json();
      view.innerHTML = this.renderShell();
      this.renderGraph(data);
      this.bindFilters(data);
      this.loaded = true;
    } catch (err) {
      view.innerHTML = `<div class="empty-state">Failed to load graph: ${err.message}</div>`;
    }
  },

  renderShell() {
    const legends = Object.entries(this.NODE_COLORS).map(([label, color]) =>
      `<div class="legend-item"><div class="legend-dot" style="background:${color}"></div>${label}</div>`
    ).join('');

    const chips = Object.keys(this.NODE_COLORS).map(label =>
      `<div class="filter-chip active" data-filter="${label}"><div class="chip-dot" style="background:${this.NODE_COLORS[label]}"></div>${label}</div>`
    ).join('');

    return `
      <div class="filter-bar">${chips}
        <div class="filter-chip active" data-filter="critical-path" style="border-color:var(--danger);color:var(--danger)">🔴 Critical Path</div>
      </div>
      <div id="graph-container">
        <svg id="graph-svg"></svg>
        <div class="graph-legend">${legends}</div>
        <div id="graph-tooltip" class="node-tooltip" style="display:none"></div>
      </div>
    `;
  },

  renderGraph(data) {
    const container = document.getElementById('graph-container');
    const svg = d3.select('#graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.attr('viewBox', [0, 0, width, height]);
    svg.selectAll('*').remove();

    // Defs for glow
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const g = svg.append('g');

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', e => g.attr('transform', e.transform));
    svg.call(zoom);

    const graphData = this.getVisibleGraph(data);
    const nodes = graphData.nodes;
    const links = graphData.links;

    // Simulation
    this.simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(60).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20));

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => d.isCriticalPath ? 'rgba(239,68,68,0.85)' : 'rgba(255,255,255,0.08)')
      .attr('stroke-width', d => d.isCriticalPath ? 2.5 : 1)
      .attr('stroke-linecap', 'round');

    // Nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => {
        const sizes = { Project: 16, Phase: 10, Activity: 7, Milestone: 9, Supplier: 9, PurchaseOrder: 8, Material: 7, Document: 6, WorkPackage: 8, Equipment: 7, WBS: 6 };
        return sizes[d.label] || 7;
      })
      .attr('fill', d => this.NODE_COLORS[d.label] || '#666')
      .attr('stroke', d => d.is_critical ? '#ef4444' : 'rgba(255,255,255,0.1)')
      .attr('stroke-width', d => d.is_critical ? 2 : 1)
      .style('filter', d => d.is_critical ? 'url(#glow)' : 'none')
      .style('cursor', 'pointer')
      .call(this.drag(this.simulation));

    // Labels for larger nodes
    const labels = g.append('g')
      .selectAll('text')
      .data(nodes.filter(n => ['Project', 'Phase', 'Milestone'].includes(n.label) || n.is_critical))
      .join('text')
      .text(d => d.name?.substring(0, 20) || d.id)
      .attr('font-size', d => d.is_critical ? '9px' : '8px')
      .attr('font-weight', d => d.is_critical ? 700 : 400)
      .attr('fill', d => d.is_critical ? 'rgba(254,202,202,0.95)' : 'rgba(255,255,255,0.6)')
      .attr('stroke', d => d.is_critical ? 'rgba(10,15,30,0.85)' : 'none')
      .attr('stroke-width', d => d.is_critical ? 3 : 0)
      .attr('paint-order', 'stroke')
      .attr('dx', d => d.is_critical ? 12 : 14)
      .attr('dy', 4);

    // Tooltip
    const tooltip = document.getElementById('graph-tooltip');
    node.on('mouseover', (event, d) => {
      const props = d.properties || {};
      const entries = Object.entries(props)
        .filter(([k]) => !k.startsWith('_') && k !== 'id')
        .slice(0, 8)
        .map(([k, v]) => `<div class="prop"><span class="prop-key">${k}</span><span class="prop-val">${v}</span></div>`)
        .join('');
      tooltip.innerHTML = `<h4>${d.label}: ${d.name || d.id}</h4>${entries}`;
      tooltip.style.display = 'block';
      tooltip.style.left = (event.offsetX + 20) + 'px';
      tooltip.style.top = (event.offsetY - 10) + 'px';
    })
    .on('mousemove', (event) => {
      tooltip.style.left = (event.offsetX + 20) + 'px';
      tooltip.style.top = (event.offsetY - 10) + 'px';
    })
    .on('mouseout', () => { tooltip.style.display = 'none'; });

    // Tick
    this.simulation.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('cx', d => d.x).attr('cy', d => d.y);
      labels.attr('x', d => d.x).attr('y', d => d.y);
    });
  },

  getVisibleGraph(data) {
    const filteredNodes = data.nodes.filter(n => this.activeFilters.has(n.label));
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredLinks = data.links.filter(l => {
      const sourceId = l.source?.id || l.source;
      const targetId = l.target?.id || l.target;
      return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId);
    });

    if (!this.showCriticalPath) {
      return {
        nodes: filteredNodes,
        links: filteredLinks.map(link => ({ ...link, isCriticalPath: false })),
      };
    }

    const criticalIds = new Set(
      filteredNodes.filter(node => node.is_critical).map(node => node.id)
    );
    const visibleIds = new Set(criticalIds);

    filteredLinks.forEach(link => {
      const sourceId = link.source?.id || link.source;
      const targetId = link.target?.id || link.target;
      if (criticalIds.has(sourceId) || criticalIds.has(targetId)) {
        visibleIds.add(sourceId);
        visibleIds.add(targetId);
      }
    });

    const nodes = filteredNodes.filter(node => visibleIds.has(node.id));
    const nodeIds = new Set(nodes.map(node => node.id));
    const links = filteredLinks
      .filter(link => {
        const sourceId = link.source?.id || link.source;
        const targetId = link.target?.id || link.target;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
      })
      .map(link => {
        const sourceId = link.source?.id || link.source;
        const targetId = link.target?.id || link.target;
        return {
          ...link,
          isCriticalPath: criticalIds.has(sourceId) && criticalIds.has(targetId),
        };
      });

    return { nodes, links };
  },

  drag(simulation) {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      });
  },

  bindFilters(data) {
    document.querySelectorAll('.filter-chip[data-filter]').forEach(chip => {
      chip.addEventListener('click', () => {
        const filter = chip.dataset.filter;
        if (filter === 'critical-path') {
          chip.classList.toggle('active');
          this.showCriticalPath = chip.classList.contains('active');
        } else {
          chip.classList.toggle('active');
          if (this.activeFilters.has(filter)) {
            this.activeFilters.delete(filter);
          } else {
            this.activeFilters.add(filter);
          }
        }
        this.renderGraph(data);
      });
    });
  },
};
