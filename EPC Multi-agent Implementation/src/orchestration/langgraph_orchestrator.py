# pyright: reportArgumentType=false, reportReturnType=false

"""LangGraph-backed orchestration for EPC specialist agents."""

from __future__ import annotations

from typing import Any, Dict, cast

from langgraph.graph import END, START, StateGraph

from src.agents import BaseAgent, log_activity
from src.agents.expanded_agents import (
    CommissioningAgent,
    ConstructionAgent,
    ContractsAgent,
    CostAgent,
    EngineeringAgent,
    HSEAgent,
    LogisticsAgent,
    QAAgent,
)
from src.agents.procurement import ProcurementAgent
from src.agents.project_delivery import ProjectDeliveryAgent
from src.agents.scheduling import SchedulingAgent


class OrchestratorAgent(BaseAgent):
    name = "Orchestrator"
    icon = "🧠"
    system_prompt = (
        "You are the EPC Project Orchestrator. You decompose user requests "
        "into sub-tasks, route them to specialist agents, and aggregate results."
    )

    def __init__(self) -> None:
        super().__init__()
        self.scheduling = SchedulingAgent()
        self.procurement = ProcurementAgent()
        self.project_delivery = ProjectDeliveryAgent()
        self.construction = ConstructionAgent()
        self.engineering = EngineeringAgent()
        self.logistics = LogisticsAgent()
        self.cost = CostAgent()
        self.hse = HSEAgent()
        self.qa = QAAgent()
        self.contracts = ContractsAgent()
        self.commissioning = CommissioningAgent()
        self._agents: Dict[str, BaseAgent] = {
            "Scheduling Agent": self.scheduling,
            "Procurement Agent": self.procurement,
            "Project Delivery Agent": self.project_delivery,
            "Construction Agent": self.construction,
            "Engineering Agent": self.engineering,
            "Logistics Agent": self.logistics,
            "Cost Agent": self.cost,
            "HSE Agent": self.hse,
            "QA/QC Agent": self.qa,
            "Contracts Agent": self.contracts,
            "Commissioning Agent": self.commissioning,
        }
        self._workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(dict[str, Any])
        graph.add_node("route_request", self._route_request)
        graph.add_node("dispatch_request", self._dispatch_request)
        graph.add_edge(START, "route_request")
        graph.add_edge("route_request", "dispatch_request")
        graph.add_edge("dispatch_request", END)
        return graph.compile()

    def _route(self, message: str) -> str:
        msg = message.lower()
        routing_map = {
            "schedule": "Scheduling Agent",
            "float": "Scheduling Agent",
            "critical path": "Scheduling Agent",
            "delay": "Scheduling Agent",
            "variance": "Scheduling Agent",
            "behind": "Scheduling Agent",
            "milestone timeline": "Scheduling Agent",
            "procurement": "Procurement Agent",
            "impact cascade": "Procurement Agent",
            "cascade": "Procurement Agent",
            "impact": "Procurement Agent",
            "supplier": "Procurement Agent",
            "purchase order": "Procurement Agent",
            "po-": "Procurement Agent",
            "po ": "Procurement Agent",
            "delivery": "Procurement Agent",
            "vendor": "Procurement Agent",
            "material slip": "Procurement Agent",
            "expedit": "Procurement Agent",
            "iwp": "Project Delivery Agent",
            "work package": "Project Delivery Agent",
            "constraint": "Project Delivery Agent",
            "readiness": "Project Delivery Agent",
            "milestone": "Project Delivery Agent",
            "deliverable": "Project Delivery Agent",
            "dashboard": "Project Delivery Agent",
            "status": "Project Delivery Agent",
            "overview": "Project Delivery Agent",
            "kpi": "Project Delivery Agent",
            "report": "Project Delivery Agent",
            "construction": "Construction Agent",
            "crew": "Construction Agent",
            "site": "Construction Agent",
            "build": "Construction Agent",
            "engineering": "Engineering Agent",
            "ifc": "Engineering Agent",
            "model": "Engineering Agent",
            "clash": "Engineering Agent",
            "design": "Engineering Agent",
            "logistics": "Logistics Agent",
            "shipment": "Logistics Agent",
            "freight": "Logistics Agent",
            "route": "Logistics Agent",
            "transport": "Logistics Agent",
            "cost": "Cost Agent",
            "evm": "Cost Agent",
            "budget": "Cost Agent",
            "cash flow": "Cost Agent",
            "spend": "Cost Agent",
            "hse": "HSE Agent",
            "safety": "HSE Agent",
            "weather": "HSE Agent",
            "permit": "HSE Agent",
            "hazard": "HSE Agent",
            "qa": "QA/QC Agent",
            "qc": "QA/QC Agent",
            "quality": "QA/QC Agent",
            "ncr": "QA/QC Agent",
            "inspection": "QA/QC Agent",
            "contract": "Contracts Agent",
            "claim": "Contracts Agent",
            "damages": "Contracts Agent",
            "exposure": "Contracts Agent",
            "legal": "Contracts Agent",
            "commissioning": "Commissioning Agent",
            "turnover": "Commissioning Agent",
            "punch": "Commissioning Agent",
            "start-up": "Commissioning Agent",
            "testing": "Commissioning Agent",
        }
        for keyword, agent_name in routing_map.items():
            if keyword in msg:
                return agent_name
        return "Project Delivery Agent"

    def _route_request(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state.get("message", "")
        target = self._route(message)
        log_activity(self.name, self.icon, "Received query", message[:200])
        log_activity(self.name, self.icon, f"Routing to {target}", f"Query: {message[:100]}...")
        return {"routed_to": target, "visited": [target]}

    def _dispatch_request(self, state: dict[str, Any]) -> dict[str, Any]:
        target = state.get("routed_to", "Project Delivery Agent")
        message = state.get("message", "")
        agent = self._agents.get(target)
        if agent is None:
            result = {
                "agent": self.name,
                "response": (
                    "I couldn't identify the specific domain for your query. "
                    "I can route questions to Scheduling, Procurement, Project Delivery, "
                    "Engineering, Construction, Logistics, Cost, HSE, QA/QC, Contracts, "
                    "or Commissioning agents."
                ),
            }
        else:
            result = agent.respond(message)

        log_activity(
            self.name,
            self.icon,
            "Response aggregated",
            f"Agent: {result.get('agent', 'Unknown')} - completed",
        )
        return {
            "result": {
                "orchestrator": self.name,
                "routed_to": target,
                **result,
            }
        }

    def respond(self, message: str) -> Dict[str, Any]:
        state = self._workflow.invoke(cast(dict[str, Any], {"message": message, "visited": []}))
        return state.get("result", {
            "orchestrator": self.name,
            "routed_to": "Project Delivery Agent",
            "agent": self.name,
            "response": "No orchestrator result was produced.",
        })

    def run_full_status(self) -> Dict[str, Any]:
        log_activity(self.name, self.icon, "Full status check initiated", "Querying all specialist agents...")

        dashboard = self.project_delivery.respond("project dashboard overview")
        variance = self.scheduling.respond("schedule variance check")
        slips = self.procurement.respond("material delivery slips")
        iwps = self.project_delivery.respond("iwp constraint readiness")

        log_activity(self.name, self.icon, "Full status check complete", "All specialist agents have reported")

        return {
            "dashboard": dashboard.get("data", {}),
            "schedule_variance": variance.get("data", []),
            "material_slips": slips.get("data", []),
            "iwp_status": iwps.get("data", {}),
        }