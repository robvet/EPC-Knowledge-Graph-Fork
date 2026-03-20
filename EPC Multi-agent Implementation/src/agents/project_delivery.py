"""Project Delivery Agent — deliverables, IWP readiness, milestone tracking."""

from __future__ import annotations
from typing import Any, Dict
from src.agents import BaseAgent, log_activity
from src.tools.graph_tools import (
    tool_get_iwp_constraint_status,
    tool_get_milestone_status,
    tool_get_project_dashboard,
)


class ProjectDeliveryAgent(BaseAgent):
    name = "Project Delivery Agent"
    icon = "📋"
    system_prompt = (
        "You are the Project Delivery Agent for an EPC LNG project. "
        "You track deliverables, IWP readiness, milestone status, "
        "and constraint clearance. When IWPs have all constraints clear, "
        "you recommend them for release."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool("get_iwp_constraint_status", tool_get_iwp_constraint_status)
        self.register_tool("get_milestone_status", tool_get_milestone_status)
        self.register_tool("get_project_dashboard", tool_get_project_dashboard)

    def respond(self, message: str) -> Dict[str, Any]:
        msg = message.lower()

        if "iwp" in msg or "constraint" in msg or "readiness" in msg or "work package" in msg:
            data = self.call_tool("get_iwp_constraint_status")
            ready = data.get("ready", [])
            blocked = data.get("blocked", [])

            ready_items = [f"  ✅ {w['name']} ({w['discipline']})" for w in ready]
            blocked_items = []
            for w in blocked:
                missing = [k for k, v in w["constraints"].items() if not v]
                blocked_items.append(
                    f"  ❌ {w['name']} ({w['discipline']}) — blocked by: {', '.join(missing)}"
                )
            summary = (
                f"IWP Readiness Report:\n"
                f"  Ready for release: {len(ready)}\n"
                + "\n".join(ready_items) + "\n"
                f"  Blocked: {len(blocked)}\n"
                + "\n".join(blocked_items)
            )
            log_activity(self.name, self.icon, "IWP constraint check", summary,
                         entities=[w["id"] for w in ready + blocked])
            return {"agent": self.name, "response": summary, "data": data}

        if "milestone" in msg:
            data = self.call_tool("get_milestone_status")
            items = []
            for m in data:
                status = m.get("status", "Unknown")
                icon = {"Achieved": "✅", "At Risk": "⚠️", "Missed": "❌", "Pending": "⏳"}.get(status, "❓")
                items.append(f"  {icon} {m.get('name', m['id'])}: {status} "
                             f"(planned: {m.get('planned_date', 'TBD')})")
            summary = "Milestone Status:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Milestone review", summary)
            return {"agent": self.name, "response": summary, "data": data}

        if "dashboard" in msg or "status" in msg or "overview" in msg:
            data = self.call_tool("get_project_dashboard")
            s = data["schedule"]
            p = data["procurement"]
            w = data["work_packages"]
            m = data["milestones"]
            summary = (
                f"📊 LNG Train 4 — Dashboard\n"
                f"  Schedule: {s['avg_pct_complete']}% complete, "
                f"{s['critical_path_count']} critical activities\n"
                f"  Procurement: {p['open_pos']} open POs, "
                f"{p['material_slips']} material slips\n"
                f"  Work Packages: {w['iwp_ready']}/{w['total_iwps']} IWPs ready\n"
                f"  Milestones: {m['achieved']} achieved, "
                f"{m['at_risk']} at risk, {m['total'] - m['achieved'] - m['at_risk']} pending"
            )
            log_activity(self.name, self.icon, "Project dashboard", summary)
            return {"agent": self.name, "response": summary, "data": data}

        return super().respond(message)
