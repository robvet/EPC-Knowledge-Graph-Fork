"""Procurement Agent — PO tracking, supplier risk, material expediting."""

from __future__ import annotations
import re
from typing import Any, Dict
from src.agents import BaseAgent, log_activity
from src.tools.graph_tools import (
    tool_get_pending_deliveries,
    tool_get_supplier_risk_profile,
    tool_get_material_need_vs_delivery,
    tool_get_delivery_cascade_impact,
)


class ProcurementAgent(BaseAgent):
    name = "Procurement Agent"
    icon = "🛒"
    system_prompt = (
        "You are the Procurement Agent for an EPC LNG project. "
        "You track purchase orders, monitor supplier performance, "
        "detect delivery risks, and manage expediting. When a delivery "
        "slips past its need date, flag it and trace the schedule impact."
    )

    def __init__(self) -> None:
        super().__init__()
        self.register_tool("get_pending_deliveries", tool_get_pending_deliveries)
        self.register_tool("get_supplier_risk_profile", tool_get_supplier_risk_profile)
        self.register_tool("get_material_need_vs_delivery", tool_get_material_need_vs_delivery)
        self.register_tool("get_delivery_cascade_impact", tool_get_delivery_cascade_impact)

    def _extract_po_reference(self, message: str) -> str:
        match = re.search(r"\bPO-\d+\b", message, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        match = re.search(r"\b45\d{5,}\b", message)
        if match:
            return match.group(0)

        return ""

    def respond(self, message: str) -> Dict[str, Any]:
        msg = message.lower()

        if "cascade" in msg or ("impact" in msg and ("po" in msg or "purchase order" in msg)):
            po_ref = self._extract_po_reference(message)
            if not po_ref:
                pending = self.call_tool("get_pending_deliveries")
                examples = ", ".join(po.get("id", "") for po in pending[:5] if po.get("id"))
                summary = (
                    "Please specify a purchase order, for example "
                    f"{examples}."
                ) if examples else "Please specify a purchase order ID such as PO-002."
                log_activity(self.name, self.icon, "Impact cascade request missing PO", summary)
                return {"agent": self.name, "response": summary, "data": []}

            data = self.call_tool("get_delivery_cascade_impact", po_id=po_ref)
            if data.get("error"):
                pending = self.call_tool("get_pending_deliveries")
                examples = ", ".join(po.get("id", "") for po in pending[:5] if po.get("id"))
                summary = (
                    f"{data['error']}. Try one of the mock POs: {examples}."
                    if examples
                    else data["error"]
                )
                log_activity(self.name, self.icon, "Impact cascade lookup failed", summary, entities=[po_ref])
                return {"agent": self.name, "response": summary, "data": data}

            materials = data.get("affected_materials", [])
            activities = data.get("affected_activities", [])
            milestones = data.get("affected_milestones", [])
            po = data.get("po", {})

            material_lines = [
                f"• {m.get('tag_number', m.get('id', 'Unknown'))}: {m.get('description', '')}"
                for m in materials
            ]
            activity_lines = [
                f"• {a.get('name', a.get('id', 'Unknown'))}"
                for a in activities
            ]
            milestone_lines = [
                f"• {m.get('name', m.get('id', 'Unknown'))} ({m.get('status', 'Unknown')})"
                for m in milestones
            ]

            summary_lines = [
                f"Impact cascade for {po.get('id', po_ref)} / PO {po.get('po_number', po_ref)}",
                data.get("impact_summary", ""),
                "",
                "Affected materials:",
                *(material_lines or ["• None"]),
                "",
                "Affected activities:",
                *(activity_lines or ["• None"]),
                "",
                "Affected milestones:",
                *(milestone_lines or ["• None"]),
            ]
            summary = "\n".join(summary_lines)
            log_activity(self.name, self.icon, "Delivery cascade impact", summary, entities=[po.get("id", po_ref)])
            return {"agent": self.name, "response": summary, "data": data}

        if "pending" in msg or "delivery" in msg or "deliveries" in msg:
            data = self.call_tool("get_pending_deliveries")
            items = [f"• PO {po.get('po_number', po['id'])}: {po.get('description', '')} "
                     f"— Status: {po.get('status', 'Unknown')}"
                     for po in data]
            summary = f"📦 {len(data)} pending deliveries:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Pending delivery check",
                         summary, entities=[po["id"] for po in data])
            return {"agent": self.name, "response": summary, "data": data}

        if "slip" in msg or "late" in msg or "need date" in msg or "material" in msg:
            data = self.call_tool("get_material_need_vs_delivery")
            if not data:
                summary = "✅ All material deliveries are on track vs. need dates."
            else:
                items = [f"• {s['material_tag']} ({s['description']}): "
                         f"PO {s['po_number']} — delivery {s['slip_days']} days late "
                         f"(need: {s['need_date']}, delivery: {s['delivery_date']})"
                         for s in data]
                summary = f"⚠️ {len(data)} materials slipping past need dates:\n" + "\n".join(items)
            log_activity(self.name, self.icon, "Material slip detection",
                         summary, entities=[s["material_id"] for s in data])
            return {"agent": self.name, "response": summary, "data": data}

        if "supplier" in msg or "risk" in msg:
            # Try to find supplier ID
            sup_id = ""
            for token in message.split():
                if token.upper().startswith("SUP-"):
                    sup_id = token.upper()
            if sup_id:
                data = self.call_tool("get_supplier_risk_profile", supplier_id=sup_id)
                summary = (f"Supplier: {data.get('name', sup_id)}\n"
                           f"  Country: {data.get('country', '')}\n"
                           f"  Compliance: {data.get('compliance_score', 'N/A')}%\n"
                           f"  Risk Level: {data.get('risk_level', 'Unknown')}\n"
                           f"  Open POs: {data.get('open_po_count', 0)}")
                log_activity(self.name, self.icon, f"Supplier risk profile: {sup_id}",
                             summary, entities=[sup_id])
                return {"agent": self.name, "response": summary, "data": data}
            # No specific supplier — scan all at-risk
            from src.graph.client import get_graph
            g = get_graph()
            suppliers = g.get_vertices_by_label("Supplier")
            at_risk = [s for s in suppliers if s.get("compliance_score", 100) < 80]
            items = [f"• {s.get('name', s['id'])}: {s.get('compliance_score', 'N/A')}% "
                     f"({s.get('qualification_status', '')})" for s in at_risk]
            summary = f"🔍 {len(at_risk)} supplier(s) with compliance < 80%:\n" + "\n".join(items) if at_risk else "✅ All suppliers are in good standing."
            log_activity(self.name, self.icon, "Supplier risk scan", summary)
            return {"agent": self.name, "response": summary, "data": at_risk}

        return super().respond(message)
