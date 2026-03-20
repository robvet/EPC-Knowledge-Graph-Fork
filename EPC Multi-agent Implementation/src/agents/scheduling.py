"""Scheduling Agent — critical path analysis, delay detection, float monitoring."""

from __future__ import annotations
from typing import Any, Dict
from src.agents import BaseAgent, log_activity
from src.tools.graph_tools import (
    tool_get_critical_path,
    tool_get_float_erosion,
    tool_get_schedule_variance,
    tool_get_delivery_cascade_impact,
    tool_get_milestone_status,
)


class SchedulingAgent(BaseAgent):
    name = "Scheduling Agent"
    icon = "📅"
    system_prompt = (
        "You are the Scheduling Agent for an EPC LNG project. "
        "You analyze critical path, detect schedule delays, calculate "
        "float erosion, and recommend mitigation sequences. "
        "When procurement delays are reported, recalculate the impact "
        "on construction milestones."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool("get_critical_path", tool_get_critical_path)
        self.register_tool("get_schedule_variance", tool_get_schedule_variance)
        self.register_tool("get_float_erosion", tool_get_float_erosion)
        self.register_tool("get_delivery_cascade_impact", tool_get_delivery_cascade_impact)
        self.register_tool("get_milestone_status", tool_get_milestone_status)

    def respond(self, message: str) -> Dict[str, Any]:
        msg = message.lower()

        if "critical path" in msg:
            data = self.call_tool("get_critical_path")
            activities = [f"• {a['name']} ({a.get('pct_complete', 0)}% complete, float: {a.get('total_float', 0)}d)"
                          for a in data]
            summary = f"Critical path has {len(data)} activities:\n" + "\n".join(activities)
            log_activity(self.name, self.icon, "Critical path analysis",
                         summary, entities=[a["id"] for a in data])
            return {"agent": self.name, "response": summary, "data": data}

        if "variance" in msg or "behind" in msg or "delayed" in msg:
            data = self.call_tool("get_schedule_variance")
            if not data:
                summary = "✅ No activities are significantly behind schedule."
            else:
                items = [f"• {a['name']}: {a.get('pct_complete', 0)}% vs expected {a.get('expected_pct', 0)}% "
                         f"(variance: {a.get('variance', 0)}%)" for a in data]
                summary = f"⚠️ {len(data)} activities behind schedule:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Schedule variance scan", summary)
            return {"agent": self.name, "response": summary, "data": data}

        if "float" in msg:
            data = self.call_tool("get_float_erosion", threshold_days=5)
            items = [f"• {a['name']}: {a.get('total_float', 0)} days float remaining"
                     for a in data]
            summary = f"{len(data)} activities with critically low float:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Float erosion check", summary)
            return {"agent": self.name, "response": summary, "data": data}

        if "impact" in msg or "cascade" in msg:
            # Try to extract PO ID
            po_id = ""
            for token in message.split():
                if token.upper().startswith("PO-"):
                    po_id = token.upper()
            if po_id:
                data = self.call_tool("get_delivery_cascade_impact", po_id=po_id)
                summary = data.get("impact_summary", "No impact data available")
                log_activity(self.name, self.icon, f"Delay cascade analysis for {po_id}",
                             summary, entities=[po_id])
                return {"agent": self.name, "response": summary, "data": data}

        if "milestone" in msg:
            data = self.call_tool("get_milestone_status")
            items = [f"• {m['name']}: {m.get('status', 'Unknown')}" for m in data]
            summary = "Milestone status:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Milestone status check", summary)
            return {"agent": self.name, "response": summary, "data": data}

        return super().respond(message)
