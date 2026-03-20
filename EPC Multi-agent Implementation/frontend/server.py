"""FastAPI server — REST API + SSE for the EPC dashboard."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.seed import seed, PROJECT_ID
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
from src.graph.client import get_graph
from src.graph import queries
from src.agents import get_activity_log
from src.agents.orchestrator import OrchestratorAgent
from src.workflows.autonomous import AUTONOMOUS_WORKFLOWS
from src.workflows.hitl import (
    HITL_WORKFLOWS, get_pending_items, get_resolved_items,
    approve_item, reject_item,
)
from src.workflows.simulations import SIMULATIONS


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="EPC Multi-Agent Dashboard", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Seed on startup
_orchestrator = None


@app.on_event("startup")
async def startup():
    global _orchestrator
    seed()
    _orchestrator = OrchestratorAgent()
    # Pre-trigger HITL workflows to populate queue
    for wf in HITL_WORKFLOWS.values():
        wf["trigger"]()


# ── Pages ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


# ── Dashboard API ───────────────────────────────────────────────────────────

@app.get("/api/dashboard/{project_id}", response_model=DashboardResponse)
async def dashboard(project_id: str = PROJECT_ID):
    return queries.get_project_dashboard(get_graph(), project_id)


# ── Graph API ───────────────────────────────────────────────────────────────

@app.get("/api/graph/{project_id}", response_model=GraphResponse)
async def graph_data(project_id: str = PROJECT_ID):
    return get_graph().to_d3_json(project_id)


@app.get("/api/graph/{project_id}/critical-path", response_model=GraphResponse)
async def graph_critical_path(project_id: str = PROJECT_ID):
    g = get_graph()
    cp = queries.get_critical_path(g, project_id)
    cp_ids = {a["id"] for a in cp}
    full = g.to_d3_json(project_id)
    for node in full["nodes"]:
        node["is_critical"] = node["id"] in cp_ids
    return full


# ── Agent API ───────────────────────────────────────────────────────────────

@app.get("/api/agents/activity")
async def agent_activity_sse(request: Request):
    """Server-Sent Events stream of agent activity."""
    seen = 0

    async def event_generator():
        nonlocal seen
        while True:
            if await request.is_disconnected():
                break
            log = get_activity_log()
            if len(log) > seen:
                for entry in log[seen:]:
                    yield {
                        "event": "activity",
                        "data": json.dumps(entry.to_dict()),
                    }
                seen = len(log)
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/agents/activity/history", response_model=list[AgentActivityResponse])
async def agent_activity_history():
    return [e.to_dict() for e in get_activity_log()]


@app.post("/api/agents/query", response_model=AgentQueryResponse)
async def agent_query(body: AgentQueryRequest):
    result = _orchestrator.respond(body.message)
    return result


# ── Workflow API ────────────────────────────────────────────────────────────

@app.get("/api/workflows/list", response_model=WorkflowListResponse)
async def list_workflows():
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
    if workflow_id in AUTONOMOUS_WORKFLOWS:
        result = AUTONOMOUS_WORKFLOWS[workflow_id]["run"]()
        return result
    elif workflow_id in HITL_WORKFLOWS:
        items = HITL_WORKFLOWS[workflow_id]["trigger"]()
        return HITLItemsCreatedResponse(items_created=len(items), items=[HITLItemResponse(**i.to_dict()) for i in items])
    raise HTTPException(404, f"Workflow '{workflow_id}' not found")


# ── Simulations API ─────────────────────────────────────────────────────────

@app.post("/api/simulations/run", response_model=SimulationResponse)
async def run_simulation(body: SimulationRequest):
    if body.scenario_id not in SIMULATIONS:
        raise HTTPException(404, f"Scenario '{body.scenario_id}' not found")
    result = SIMULATIONS[body.scenario_id]["run"](body.project_id)
    return result


# ── HITL API ────────────────────────────────────────────────────────────────

@app.get("/api/hitl/queue", response_model=HITLQueueResponse)
async def hitl_queue():
    pending = [i.to_dict() for i in get_pending_items()]
    resolved = [i.to_dict() for i in get_resolved_items()]
    return {"pending": pending, "resolved": resolved}


@app.post("/api/hitl/{item_id}/approve", response_model=HITLItemResponse)
async def hitl_approve(item_id: str):
    item = approve_item(item_id)
    if not item:
        raise HTTPException(404, f"HITL item '{item_id}' not found or not pending")
    return item.to_dict()


@app.post("/api/hitl/{item_id}/reject", response_model=HITLItemResponse)
async def hitl_reject(item_id: str, body: RejectRequest):
    item = reject_item(item_id, reason=body.reason)
    if not item:
        raise HTTPException(404, f"HITL item '{item_id}' not found or not pending")
    return item.to_dict()


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend.server:app", host="0.0.0.0", port=8000, reload=True)
