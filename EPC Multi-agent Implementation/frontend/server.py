"""
FastAPI server — REST API + SSE for the EPC (Engineering, Procurement, Construction)
Multi-Agent Dashboard.

This server provides:
  1. A static HTML/JS frontend (single-page app)
  2. REST endpoints for project dashboard data, knowledge graph queries,
     workflow orchestration, HITL (Human-in-the-Loop) approvals, and simulations
  3. A Server-Sent Events (SSE) stream for real-time agent activity updates

Architecture:
  - The knowledge graph (in-memory) stores project entities (activities, work packages,
    materials, resources) and their relationships as nodes + edges
  - Multiple specialized agents (procurement, scheduling, project delivery) operate
    on the graph and produce activity logs
  - An orchestrator agent routes natural-language queries to the appropriate specialist
  - Autonomous workflows run without human intervention; HITL workflows require
    explicit approve/reject decisions from users before changes are committed

Graph Concepts:
  - Nodes represent domain objects: Project, Activity, WorkPackage, Material, etc.
  - Edges represent typed relationships: DEPENDS_ON, BELONGS_TO, REQUIRES, etc.
  - D3 JSON format = {nodes: [...], links: [...]} for frontend visualization
  - Critical path = longest dependency chain determining minimum project duration
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse  # Third-party SSE support for FastAPI

# Ensure the top-level 'src' package is importable regardless of how the server is launched.
# This inserts the project root (one level above frontend/) onto sys.path so that
# "from src.xxx import yyy" works even when running directly via `python frontend/server.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Domain Imports ──────────────────────────────────────────────────────────
# seed() populates the in-memory knowledge graph with realistic EPC project data.
# PROJECT_ID is the default project identifier used when none is specified.
from src.data.seed import seed, PROJECT_ID

# Pydantic response/request models — enforce schema validation on all API I/O.
from src.api_models import (
    AgentActivityResponse,
    AgentQueryRequest,
    AgentQueryResponse,
    DashboardResponse,
    GraphResponse,
    HITLItemResponse,
    HITLItemsCreatedResponse,
    HITLQueueResponse,
    RejectRequest,
    SimulationRequest,
    SimulationResponse,
    WorkflowDefinitionResponse,
    WorkflowListResponse,
    WorkflowRunResponse,
)

# get_graph() returns the singleton in-memory graph instance.
# All agents and queries operate against this shared graph.
from src.graph.client import get_graph

# queries module contains graph traversal functions (critical path, dashboard KPIs, etc.)
from src.graph import queries

# Agent system: get_activity_log() returns the global list of agent actions taken so far.
from src.agents import get_activity_log

# The orchestrator is the "router" agent — it interprets user questions and delegates
# to specialist agents (procurement, scheduling, project delivery).
from src.agents.orchestrator import OrchestratorAgent

# Autonomous workflows run end-to-end without human approval (e.g., schedule optimization).
from src.workflows.autonomous import AUTONOMOUS_WORKFLOWS

# HITL workflows generate proposed changes that require human approve/reject decisions.
from src.workflows.hitl import (
    HITL_WORKFLOWS, get_pending_items, get_resolved_items,
    approve_item, reject_item,
)

# Simulations allow "what-if" scenario analysis on the project graph.
from src.workflows.simulations import SIMULATIONS


# ── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(title="EPC Multi-Agent Dashboard", version="0.1.0")

# Serve the static SPA (HTML, CSS, JS) from frontend/static/
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Module-level orchestrator instance — initialized once at startup and reused
# across all /api/agents/query requests to maintain conversation context.
_orchestrator = None


@app.on_event("startup")
async def startup():
    """Application startup hook — runs once when uvicorn starts the server.

    Steps:
      1. seed() — Populates the in-memory knowledge graph with sample EPC project
         data (activities, dependencies, materials, work packages). This simulates
         data that would normally come from external systems (Primavera P6, SAP, etc.).
      2. OrchestratorAgent() — Instantiates the top-level agent that will route
         natural-language queries to specialist sub-agents.
      3. Pre-trigger HITL workflows — Generates initial pending approval items so
         the dashboard has content to display immediately on first load.
    """
    global _orchestrator
    seed()
    _orchestrator = OrchestratorAgent()
    # Pre-trigger all HITL workflows so the approval queue is non-empty at startup.
    # Each trigger() call analyzes the current graph state and produces items
    # that require human review (e.g., "approve budget reallocation for WP-003").
    for wf in HITL_WORKFLOWS.values():
        wf["trigger"]()


# ── Pages ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the single-page app. All client-side routing is handled by JS."""
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


# ── Dashboard API ───────────────────────────────────────────────────────────

@app.get("/api/dashboard/{project_id}", response_model=DashboardResponse)
async def dashboard(project_id: str = PROJECT_ID):
    """Return aggregated project KPIs (schedule health, cost, progress %).

    Traverses the knowledge graph to compute metrics by walking nodes connected
    to the given project: counts activities by status, sums budgets, calculates
    percent-complete from completed vs. total activities, etc.
    """
    return queries.get_project_dashboard(get_graph(), project_id)


# ── Graph API ───────────────────────────────────────────────────────────────
# These endpoints expose the knowledge graph in D3-compatible JSON format
# for the frontend force-directed graph visualization.
#
# D3 JSON structure:
#   { "nodes": [{"id": ..., "type": ..., "label": ..., ...}],
#     "links": [{"source": ..., "target": ..., "type": ..., ...}] }
#
# The frontend renders this with d3-force: nodes become circles, links become
# connecting lines, colored/sized by type and status.

@app.get("/api/graph/{project_id}", response_model=GraphResponse)
async def graph_data(project_id: str = PROJECT_ID):
    """Return the full knowledge graph for a project as D3 JSON.

    Includes ALL nodes and edges belonging to the project — activities,
    work packages, materials, resources, and their inter-relationships.
    The frontend can filter/highlight subsets client-side.
    """
    return get_graph().to_d3_json(project_id)


@app.get("/api/graph/{project_id}/critical-path", response_model=GraphResponse)
async def graph_critical_path(project_id: str = PROJECT_ID):
    """Return the full graph with critical-path nodes flagged.

    Critical Path Algorithm:
      1. get_critical_path() performs a topological traversal of the activity
         dependency graph (DEPENDS_ON edges) to find the longest path from
         project start to project end — this is the sequence of activities
         that determines the minimum project duration.
      2. Any delay on a critical-path activity delays the entire project.
      3. We collect the IDs of critical-path activities into a set (cp_ids).
      4. We then fetch the full D3 graph and annotate each node with an
         "is_critical" boolean flag so the frontend can highlight them
         (typically in red) on the force-directed visualization.

    This is a read-only operation — it does not modify the graph.
    """
    g = get_graph()
    # Step 1: Compute the critical path — returns list of activity dicts on the longest path
    cp = queries.get_critical_path(g, project_id)
    # Step 2: Build a set of critical-path node IDs for O(1) membership testing
    cp_ids = {a["id"] for a in cp}
    # Step 3: Get the full graph in D3 format
    full = g.to_d3_json(project_id)
    # Step 4: Annotate every node — frontend uses this flag for visual highlighting
    for node in full["nodes"]:
        node["is_critical"] = node["id"] in cp_ids
    return full


# ── Agent API ───────────────────────────────────────────────────────────────
# Agents are autonomous reasoning components that analyze the graph, detect issues,
# and take actions. Each agent logs its activity to a shared in-memory list.
# The frontend consumes these logs via SSE for real-time updates and via REST
# for historical replay.

@app.get("/api/agents/activity")
async def agent_activity_sse(request: Request):
    """Server-Sent Events (SSE) stream of real-time agent activity.

    How SSE works here:
      - The client opens a persistent HTTP connection (EventSource in JS).
      - The server sends events as they occur — no polling from the client side.
      - Each event is a JSON-serialized agent activity entry (agent name, action,
        timestamp, affected entities, etc.).

    Implementation:
      - `seen` tracks how many log entries we've already sent to THIS client.
      - Every 0.5s we check the global activity log for new entries beyond `seen`.
      - When new entries exist, we yield them as SSE events and advance `seen`.
      - If the client disconnects, we break out of the loop to free resources.

    This pattern avoids database polling — the activity log is an in-memory list
    that agents append to, and we simply tail it.
    """
    seen = 0

    async def event_generator():
        nonlocal seen
        while True:
            # Check if the client closed the connection (browser tab closed, etc.)
            if await request.is_disconnected():
                break
            log = get_activity_log()
            # Only send entries the client hasn't seen yet
            if len(log) > seen:
                for entry in log[seen:]:
                    yield {
                        "event": "activity",
                        "data": json.dumps(entry.to_dict()),
                    }
                seen = len(log)
            # Sleep to avoid busy-looping; 0.5s gives near-real-time feel
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/agents/activity/history", response_model=list[AgentActivityResponse])
async def agent_activity_history():
    """Return the full agent activity log (all entries since server start).

    Used by the frontend on initial page load to backfill the activity feed
    with events that occurred before the SSE connection was established.
    """
    return [e.to_dict() for e in get_activity_log()]


@app.post("/api/agents/query", response_model=AgentQueryResponse)
async def agent_query(body: AgentQueryRequest):
    """Natural-language query interface to the multi-agent system.

    The orchestrator agent:
      1. Parses the user's question (e.g., "What materials are delayed?").
      2. Determines which specialist agent should handle it (procurement,
         scheduling, or project delivery).
      3. The specialist queries the knowledge graph and formulates a response.
      4. The orchestrator returns the structured answer + any graph citations.

    This is the primary conversational AI endpoint for the dashboard.
    """
    result = _orchestrator.respond(body.message)
    return result


# ── Workflow API ────────────────────────────────────────────────────────────
# Workflows are pre-defined multi-step agent operations. Two categories:
#   - Autonomous: Run to completion without human input (e.g., "optimize schedule").
#     These directly mutate the graph and return a summary of changes.
#   - HITL (Human-in-the-Loop): Generate proposed changes that go into a review queue.
#     A human must approve or reject each item before the graph is updated.

@app.get("/api/workflows/list", response_model=WorkflowListResponse)
async def list_workflows():
    """List all available workflows, categorized by type (autonomous vs. HITL).

    The frontend uses this to populate the workflow launcher panel.
    """
    auto = [
        WorkflowDefinitionResponse(id=k, name=v["name"], description=v["description"], type="autonomous")
        for k, v in AUTONOMOUS_WORKFLOWS.items()
    ]
    hitl = [
        WorkflowDefinitionResponse(id=k, name=v["name"], description=v["description"], type="hitl")
        for k, v in HITL_WORKFLOWS.items()
    ]
    return {"autonomous": auto, "hitl": hitl}


@app.post("/api/workflows/{workflow_id}/run", response_model=WorkflowRunResponse | HITLItemsCreatedResponse)
async def run_workflow(workflow_id: str):
    """Execute a workflow by ID.

    Behavior depends on workflow type:
      - Autonomous: Calls run() which modifies the graph immediately and returns
        a WorkflowRunResponse with a summary of what changed.
      - HITL: Calls trigger() which analyzes the graph, creates pending approval
        items, and returns an HITLItemsCreatedResponse listing what needs review.
        The graph is NOT modified until items are individually approved.

    Returns 404 if the workflow_id doesn't match any registered workflow.
    """
    if workflow_id in AUTONOMOUS_WORKFLOWS:
        result = AUTONOMOUS_WORKFLOWS[workflow_id]["run"]()
        return result
    elif workflow_id in HITL_WORKFLOWS:
        # trigger() returns a list of HITLItem objects (pending approval)
        items = HITL_WORKFLOWS[workflow_id]["trigger"]()
        return HITLItemsCreatedResponse(items_created=len(items), items=[HITLItemResponse(**i.to_dict()) for i in items])
    raise HTTPException(404, f"Workflow '{workflow_id}' not found")


# ── Simulations API ─────────────────────────────────────────────────────────
# Simulations are "what-if" scenarios that run against a copy or snapshot of
# the graph. They answer questions like "What happens to the schedule if
# material delivery is delayed by 2 weeks?" without modifying the real graph.

@app.post("/api/simulations/run", response_model=SimulationResponse)
async def run_simulation(body: SimulationRequest):
    """Run a what-if simulation scenario.

    Takes a scenario_id (predefined scenario type) and project_id, then:
      1. Applies hypothetical changes to a graph copy (e.g., delay a delivery)
      2. Re-computes metrics (schedule impact, cost impact, critical path changes)
      3. Returns a SimulationResponse with before/after comparison

    This is non-destructive — the actual project graph is not modified.
    """
    if body.scenario_id not in SIMULATIONS:
        raise HTTPException(404, f"Scenario '{body.scenario_id}' not found")
    result = SIMULATIONS[body.scenario_id]["run"](body.project_id)
    return result


# ── HITL (Human-in-the-Loop) API ────────────────────────────────────────────
# HITL items represent proposed graph mutations that require human judgment.
# Example: "Agent recommends reallocating $50K from WP-002 to WP-005."
# The human reviews the proposal's rationale and either approves (applying
# the change to the graph) or rejects (discarding it with a reason).
#
# Lifecycle: pending → approved/rejected
# Only pending items can be acted upon. Resolved items are kept for audit trail.

@app.get("/api/hitl/queue", response_model=HITLQueueResponse)
async def hitl_queue():
    """Return all HITL items split into pending (awaiting decision) and resolved.

    The frontend displays pending items as actionable cards with approve/reject
    buttons, and resolved items in a historical log.
    """
    pending = [i.to_dict() for i in get_pending_items()]
    resolved = [i.to_dict() for i in get_resolved_items()]
    return {"pending": pending, "resolved": resolved}


@app.post("/api/hitl/{item_id}/approve", response_model=HITLItemResponse)
async def hitl_approve(item_id: str):
    """Approve a pending HITL item — applies its proposed change to the graph.

    Once approved, the item's associated graph mutation is executed (e.g.,
    updating a budget field, reassigning a resource, changing a schedule date).
    The item transitions to 'approved' status and cannot be acted upon again.
    """
    item = approve_item(item_id)
    if not item:
        raise HTTPException(404, f"HITL item '{item_id}' not found or not pending")
    return item.to_dict()


@app.post("/api/hitl/{item_id}/reject", response_model=HITLItemResponse)
async def hitl_reject(item_id: str, body: RejectRequest):
    """Reject a pending HITL item — discards the proposed change with a reason.

    The graph is NOT modified. The rejection reason is stored for auditability
    so the agent system can learn from human feedback patterns.
    """
    item = reject_item(item_id, reason=body.reason)
    if not item:
        raise HTTPException(404, f"HITL item '{item_id}' not found or not pending")
    return item.to_dict()


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Start the ASGI server with hot-reload enabled for development.
    # "frontend.server:app" is the import path to the FastAPI instance.
    # host="0.0.0.0" binds to all interfaces (accessible from other machines).
    # reload=True watches for file changes and restarts automatically.
    uvicorn.run("frontend.server:app", host="0.0.0.0", port=8000, reload=True)
