# EPC Multi-Agent Implementation

## What This Project Does

This project is an EPC knowledge graph and multi-agent decision-support application focused on engineering, procurement, construction, and delivery workflows.

The application brings together:

- a browser-based dashboard for project visibility
- a FastAPI backend that serves the UI and API
- a LangGraph-based orchestrator that routes requests to specialist agents
- graph-centric project intelligence for schedules, materials, milestones, suppliers, and work packages
- a mock mode for local demos and development
- an Azure deployment scaffold for a production-grade, identity-based implementation

At a high level, the system is designed to answer questions like:

- which activities are on the critical path
- which purchase orders are slipping past need dates
- which work packages are ready for release
- which milestones are at risk
- what the downstream impact of a procurement or logistics issue might be
- what-if simulation outcomes for supply chain, weather, or labor disruptions

The target production architecture uses Azure Database for PostgreSQL Flexible Server with Apache AGE as the graph backbone, Azure AI services for document extraction and understanding, Azure AI Search for retrieval, Azure Service Bus for event-driven pipelines, and Azure Container Apps for runtime hosting.

## Core Concept

The system models EPC delivery as a connected graph instead of isolated tables and dashboards.

That graph connects:

- activities and milestones
- materials and purchase orders
- suppliers and compliance risk
- documents and work packages
- engineering, procurement, logistics, construction, cost, and HSE perspectives

The agent layer sits on top of that graph. Instead of a user manually traversing multiple systems, the orchestrator routes a question to the right specialist agent, which then calls graph tools and returns a structured answer.

## Current Runtime Modes

This repo currently supports two runtime modes.

### Mock Mode

`APP_MODE=mock`

Mock mode is the current fully working local path.

In mock mode:

- the app seeds an in-memory graph on startup
- the frontend and API run inside a single FastAPI process
- the agents use seeded demo data rather than live Azure services
- simulations, workflows, dashboard views, and graph queries run against local memory

This mode is intended for:

- local development
- UI and API iteration
- demos
- orchestration and validation work before live Azure integration is finished

### Azure Mode

`APP_MODE=azure`

Azure mode is scaffolded, not yet fully wired end to end.

In Azure mode the intended runtime contract is:

- `DefaultAzureCredential` for service authentication
- Azure OpenAI via Entra token auth
- PostgreSQL Flexible Server plus Apache AGE for graph storage
- Azure Storage for raw, curated, and enriched document content
- Azure Service Bus for ingestion and enrichment events
- Azure AI Search for retrieval and indexing
- Azure AI multi-service account for Document Intelligence and Content Understanding pipelines
- Container Apps for hosting the FastAPI runtime

At this point, the configuration, dependencies, Bicep, and environment contract are in place, but the application logic is still primarily executing through the mock graph path.

## End-to-End Flow

The intended flow is:

1. documents and structured EPC source-system data arrive from external systems
2. ingestion and enrichment pipelines normalize and extract entities, relationships, and metadata
3. the extracted data is loaded into PostgreSQL plus Apache AGE and indexed for retrieval
4. the user asks a question through the dashboard or API
5. the LangGraph orchestrator routes the request to the right specialist agent
6. the selected agent calls graph queries, workflow logic, or simulation logic
7. the API returns a validated response payload to the dashboard

## Project Structure

This is the current structure and the role of each major area.

```text
EPC Multi-agent Implementation/
├── frontend/
│   ├── server.py                # FastAPI entrypoint serving UI and API
│   └── static/                  # HTML, CSS, and JS for the dashboard
├── infra/
│   └── bicep/
│       ├── main.bicep           # Main Azure deployment template
│       ├── main.dev.bicepparam  # DEV parameters for Central US
│       └── modules/             # Resource-specific Bicep modules
├── src/
│   ├── agents/                  # Specialist agents and compatibility wrapper
│   ├── orchestration/           # LangGraph-based orchestrator
│   ├── graph/                   # In-memory graph client, models, and queries
│   ├── tools/                   # Agent-callable graph tools
│   ├── workflows/               # Autonomous, HITL, and simulation workflows
│   ├── data/                    # Seed data and mock source-system adapters
│   ├── api_models.py            # Pydantic request and response models
│   ├── auth.py                  # Azure identity and Azure OpenAI helpers
│   └── config.py                # Mock and Azure runtime configuration
├── .env.example                 # Example runtime contract
├── EPC.drawio                   # Architecture diagrams
├── pyproject.toml               # Python dependencies and package config
└── README.md                    # This document
```

## Detailed Component Breakdown

### frontend/

The frontend is a lightweight dashboard application served directly by FastAPI.

Key responsibilities:

- render project dashboard views
- show graph visualizations
- trigger agent queries
- consume REST responses and SSE activity feeds

Key file:

- [frontend/server.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/frontend/server.py)

### src/agents/

This folder contains the specialist agents.

Examples:

- scheduling
- procurement
- project delivery
- construction
- engineering
- logistics
- cost
- HSE
- QA/QC
- contracts
- commissioning

The file [src/agents/orchestrator.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/agents/orchestrator.py) is now a compatibility entry point that delegates to the LangGraph implementation.

### src/orchestration/

This is the new orchestration layer.

Key file:

- [src/orchestration/langgraph_orchestrator.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/orchestration/langgraph_orchestrator.py)

Responsibilities:

- accept the incoming user request
- determine routing target based on request semantics
- dispatch to the appropriate specialist agent
- preserve a stable response contract for the rest of the app

### src/graph/

This folder contains the graph data layer.

Current state:

- [src/graph/client.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/graph/client.py) is an in-memory property graph client used by mock mode
- [src/graph/models.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/graph/models.py) contains Pydantic graph entity models
- [src/graph/queries.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/graph/queries.py) contains reusable query functions for schedules, milestones, procurement, readiness, and cascade impact

Future Azure mode direction:

- replace or extend the in-memory graph client with PostgreSQL plus Apache AGE access
- retain the same query-level API where practical

### src/tools/

This layer wraps graph queries into simple tool calls that agents can invoke.

Key file:

- [src/tools/graph_tools.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/tools/graph_tools.py)

### src/workflows/

This folder contains execution patterns above direct question answering.

Files:

- [src/workflows/autonomous.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/workflows/autonomous.py)
- [src/workflows/hitl.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/workflows/hitl.py)
- [src/workflows/simulations.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/workflows/simulations.py)

These support:

- autonomous exception scanning
- human-in-the-loop approval queues
- scenario simulations

### src/api_models.py

This file centralizes Pydantic request and response models for the FastAPI layer and internal serialized payloads.

This matters because it gives the project:

- better validation
- better API documentation
- more stable UI contracts
- a cleaner transition from mock to Azure-backed services

### infra/bicep/

This folder contains the Azure deployment scaffold.

Main files:

- [infra/bicep/main.bicep](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/infra/bicep/main.bicep)
- [infra/bicep/main.dev.bicepparam](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/infra/bicep/main.dev.bicepparam)

Modules include:

- identity
- monitoring
- storage
- service bus
- search
- AI services
- PostgreSQL
- Container Apps

## API Surface

The application exposes these main API areas through FastAPI.

- `/api/dashboard/{project_id}`
- `/api/graph/{project_id}`
- `/api/graph/{project_id}/critical-path`
- `/api/agents/activity`
- `/api/agents/activity/history`
- `/api/agents/query`
- `/api/workflows/list`
- `/api/workflows/{workflow_id}/run`
- `/api/simulations/run`
- `/api/hitl/queue`
- `/api/hitl/{item_id}/approve`
- `/api/hitl/{item_id}/reject`

All major request and response payloads now use Pydantic models.

## How To Run In Mock Mode

### Prerequisites

- Windows PowerShell
- the workspace virtual environment at `.venv`
- local `.env` configured with `APP_MODE=mock`

### Preferred Startup

```powershell
Set-Location 'C:\Projects\GithubLocal\EPC Knowledge Graph\EPC Multi-agent Implementation'
.\run-mock.ps1
```

If local script execution is blocked:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-mock.ps1
```

Equivalent direct command:

```powershell
Set-Location 'C:\Projects\GithubLocal\EPC Knowledge Graph\EPC Multi-agent Implementation'
& "C:\Projects\GithubLocal\EPC Knowledge Graph\.venv\Scripts\python.exe" -m uvicorn frontend.server:app --host 127.0.0.1 --port 8000
```

Alternative activation flow:

```powershell
Set-Location 'C:\Projects\GithubLocal\EPC Knowledge Graph'
& ".\.venv\Scripts\Activate.ps1"
Set-Location '.\EPC Multi-agent Implementation'
.\run-mock.ps1
```

### Open The UI

```text
http://127.0.0.1:8000/
```

Do not open the HTML file directly from disk.

### Verify The App Is Running

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/' | Select-Object StatusCode
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/dashboard/PRJ-001' | Select-Object StatusCode
```

Expected result:

```text
StatusCode
----------
200
```

### What Happens In Mock Mode

On startup, the app:

- seeds the in-memory graph
- initializes the LangGraph orchestrator
- preloads HITL workflow queue entries as needed
- serves the frontend and API from one process

## How To Run In Azure Mode

Azure mode should be treated as scaffolded integration mode, not fully operational production runtime yet.

### What Azure Mode Is For Right Now

- validating deployment structure
- validating environment contract
- preparing identity-based runtime dependencies
- transitioning from mock graph access to live services

### Azure Configuration Contract

See [src/config.py](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/src/config.py) and [.env.example](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/.env.example).

Important runtime settings include:

- `APP_MODE=azure`
- `APP_ENVIRONMENT=dev`
- `AZURE_LOCATION=centralus`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_POSTGRES_HOST`
- `AZURE_POSTGRES_DATABASE`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX`
- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_SERVICEBUS_NAMESPACE`
- `AZURE_AI_SERVICES_ENDPOINT`

Authentication in Azure mode is designed around:

- `DefaultAzureCredential`
- managed identities in Azure
- `az login` for local developer authentication

### Deploy The DEV Infrastructure

From the implementation folder:

```powershell
az deployment group create ^
  --resource-group <your-dev-rg> ^
  --template-file .\infra\bicep\main.bicep ^
  --parameters .\infra\bicep\main.dev.bicepparam
```

Before first deployment, update:

- resource names if needed for uniqueness
- the PostgreSQL Entra admin object ID
- any subnet or private DNS values if you are moving beyond public DEV defaults
- the placeholder Container App image reference

### Azure Services In The Current Scaffold

- Azure Container Apps
- Azure Database for PostgreSQL Flexible Server
- Apache AGE extension configuration
- Azure Storage account with Data Lake Gen2 enabled
- Azure Service Bus namespace and queues
- Azure AI Search
- Azure AI multi-service account
- Azure OpenAI account
- Log Analytics workspace
- Application Insights
- user-assigned managed identity

## What The Agents Do

The system is not a general chatbot. It is a structured EPC operations assistant with domain-specific agents.

### Orchestrator

The orchestrator:

- receives the request
- inspects the request text
- routes it to a specialist agent
- returns a single stable response format

### Specialist Agents

Examples of specialist behavior:

- Scheduling Agent: critical path, float erosion, variance, milestone timing
- Procurement Agent: PO tracking, material slips, supplier risk, delivery cascade
- Project Delivery Agent: readiness, constraints, dashboard, work package status
- Construction and Engineering Agents: execution and technical context
- Cost Agent: commercial impact and exposure
- HSE Agent: safety and weather-related logic

## Workflows

The project includes more than direct question-answering.

### Autonomous Workflows

These run without human approval and generate structured results.

Examples:

- procurement delay cascade
- schedule variance detection
- document readiness check

### HITL Workflows

These create approval items for humans to review.

Examples:

- IWP release approval
- change order approval
- supplier qualification review

### Simulation Workflows

These perform what-if analysis.

Examples:

- supply chain shock
- extreme weather event
- labor shortage

## Why The Graph Matters

A normal application might keep schedules, documents, suppliers, and work packages in disconnected tables and systems. This project treats them as connected entities.

That makes it possible to answer questions such as:

- if a PO slips, which materials are affected
- if those materials slip, which activities are affected
- if those activities are affected, which milestones are now at risk

That connected reasoning path is the foundation of both the agent responses and the future Azure implementation.

## Mock Versus Azure Summary

This is the current practical status.

### Mock Mode

- fully retained
- still the primary local runtime
- used by the seeded in-memory graph
- safe for local testing and demos

### Azure Mode

- configuration scaffolded
- dependencies installed
- Bicep deployment scaffolded
- not yet fully wired across every runtime data path

The project is therefore not Azure-only. The mock path still exists and is still important.

## Detailed Azure Architecture

The implementation architecture draw.io file is here:

- [EPC.drawio](c:/Projects/GithubLocal/EPC%20Knowledge%20Graph/EPC%20Multi-agent%20Implementation/EPC.drawio)

The updated diagram now reflects:

- Entra-authenticated user and operator access
- FastAPI plus Container Apps hosting
- LangGraph orchestrator and specialist agents
- document ingestion and enrichment path
- AI extraction and model services
- PostgreSQL plus Apache AGE graph storage
- AI Search retrieval tier
- Storage and Service Bus pipeline components
- monitoring and security context
- explicit mock mode and Azure mode relationship

## Stop The Server

In the terminal where Uvicorn is running, press:

```text
Ctrl+C
```

## Common Failure Cases

- the server is not running
- the page was opened from the filesystem instead of `http://127.0.0.1:8000/`
- the server was started from the wrong directory
- `.env` is configured for the wrong mode
- Azure mode was selected before the live Azure-backed runtime paths were finished
