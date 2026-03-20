"""Human-in-the-loop (HITL) workflows — require human approval to proceed."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents import log_activity
from src.api_models import HITLItemResponse
from src.agents.project_delivery import ProjectDeliveryAgent
from src.agents.procurement import ProcurementAgent
from src.graph.client import get_graph


# ── HITL Queue ──────────────────────────────────────────────────────────────

class HITLItem:
    """An item pending human review."""

    def __init__(
        self,
        title: str,
        workflow_name: str,
        requesting_agent: str,
        summary: str,
        details: Dict[str, Any],
        impact: str = "",
    ):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.workflow_name = workflow_name
        self.requesting_agent = requesting_agent
        self.summary = summary
        self.details = details
        self.impact = impact
        self.status = "pending"  # pending | approved | rejected
        self.created_at = datetime.now().isoformat()
        self.resolved_at: Optional[str] = None
        self.resolved_by: Optional[str] = None
        self.rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return HITLItemResponse(
            id=self.id,
            title=self.title,
            workflow_name=self.workflow_name,
            requesting_agent=self.requesting_agent,
            summary=self.summary,
            details=self.details,
            impact=self.impact,
            status=self.status,
            created_at=self.created_at,
            resolved_at=self.resolved_at,
            resolved_by=self.resolved_by,
            rejection_reason=self.rejection_reason,
        ).model_dump()


# Global HITL queue
_hitl_queue: List[HITLItem] = []


def get_hitl_queue() -> List[HITLItem]:
    return _hitl_queue


def get_pending_items() -> List[HITLItem]:
    return [item for item in _hitl_queue if item.status == "pending"]


def get_resolved_items() -> List[HITLItem]:
    return [item for item in _hitl_queue if item.status != "pending"]


def approve_item(item_id: str, approved_by: str = "Human Operator") -> Optional[HITLItem]:
    for item in _hitl_queue:
        if item.id == item_id and item.status == "pending":
            item.status = "approved"
            item.resolved_at = datetime.now().isoformat()
            item.resolved_by = approved_by

            log_activity("System", "✅", f"HITL Approved: {item.title}",
                         f"Approved by {approved_by}")

            # Execute post-approval action
            _on_approval(item)
            return item
    return None


def reject_item(item_id: str, reason: str = "", rejected_by: str = "Human Operator") -> Optional[HITLItem]:
    for item in _hitl_queue:
        if item.id == item_id and item.status == "pending":
            item.status = "rejected"
            item.resolved_at = datetime.now().isoformat()
            item.resolved_by = rejected_by
            item.rejection_reason = reason

            log_activity("System", "❌", f"HITL Rejected: {item.title}",
                         f"Rejected by {rejected_by}: {reason}")
            return item
    return None


def _on_approval(item: HITLItem) -> None:
    """Post-approval actions — update graph state."""
    g = get_graph()
    if item.workflow_name == "IWP Release Approval":
        iwp_id = item.details.get("iwp_id")
        if iwp_id:
            g.update_vertex(iwp_id, status="Released")
            log_activity("Project Delivery Agent", "📋",
                         f"IWP Released: {item.details.get('iwp_name', iwp_id)}",
                         "Status updated to Released in knowledge graph")
    elif item.workflow_name == "Change Order Approval":
        po_id = item.details.get("po_id")
        if po_id:
            new_value = item.details.get("new_value")
            if new_value:
                g.update_vertex(po_id, value=new_value)
            log_activity("Procurement Agent", "🛒",
                         f"Change order applied to {po_id}",
                         "PO updated in knowledge graph")


# ── HITL Workflow Triggers ─────────────────────────────────────────────────

def trigger_iwp_release_approval() -> List[HITLItem]:
    """Workflow 4: Find ready IWPs and create approval requests."""
    log_activity("System", "⚡", "HITL Workflow triggered",
                 "IWP Release Approval — scanning for ready IWPs")

    delivery = ProjectDeliveryAgent()
    result = delivery.respond("Check IWP readiness")
    ready = result.get("data", {}).get("ready", [])

    new_items = []
    for iwp in ready:
        # Only create if not already in queue
        existing = [i for i in _hitl_queue
                    if i.details.get("iwp_id") == iwp["id"]
                    and i.status == "pending"]
        if existing:
            continue

        item = HITLItem(
            title=f"IWP Release: {iwp.get('name', iwp['id'])}",
            workflow_name="IWP Release Approval",
            requesting_agent="Project Delivery Agent",
            summary=(
                f"IWP {iwp.get('name', iwp['id'])} has all constraints clear "
                f"and is recommended for release."
            ),
            details={
                "iwp_id": iwp["id"],
                "iwp_name": iwp.get("name", ""),
                "discipline": iwp.get("discipline", ""),
                "constraints": iwp.get("constraints", {}),
                "recommendation": "Release to field crew",
            },
            impact=f"Enables {iwp.get('discipline', '')} crew to begin work",
        )
        _hitl_queue.append(item)
        new_items.append(item)

        log_activity("Project Delivery Agent", "📋",
                     f"Approval requested: {item.title}",
                     item.summary)

    log_activity("System", "⏳", "HITL items created",
                 f"{len(new_items)} IWP release approvals queued")
    return new_items


def trigger_change_order_approval() -> List[HITLItem]:
    """Workflow 5: Detect POs needing change orders and create approval requests."""
    log_activity("System", "⚡", "HITL Workflow triggered",
                 "Change Order Approval — scanning for PO amendments")

    g = get_graph()
    procurement = ProcurementAgent()
    slips = procurement.respond("Check material delivery slips")
    slip_data = slips.get("data", [])

    new_items = []
    for slip in slip_data:
        po_number = slip.get("po_number", "")
        pos = g.find_vertices("PurchaseOrder", po_number=po_number)
        if not pos:
            continue
        po = pos[0]

        existing = [i for i in _hitl_queue
                    if i.details.get("po_id") == po["id"]
                    and i.status == "pending"]
        if existing:
            continue

        current_value = po.get("value", 0)
        proposed_increase = round(current_value * 0.15, 2)  # 15% increase for expediting

        item = HITLItem(
            title=f"Change Order: PO {po_number}",
            workflow_name="Change Order Approval",
            requesting_agent="Procurement Agent",
            summary=(
                f"PO {po_number} ({po.get('description', '')}) is slipping "
                f"{slip.get('slip_days', 0)} days. Recommend expediting with "
                f"cost increase of ${proposed_increase:,.0f}."
            ),
            details={
                "po_id": po["id"],
                "po_number": po_number,
                "description": po.get("description", ""),
                "current_value": current_value,
                "proposed_increase": proposed_increase,
                "new_value": current_value + proposed_increase,
                "slip_days": slip.get("slip_days", 0),
                "need_date": slip.get("need_date", ""),
                "delivery_date": slip.get("delivery_date", ""),
            },
            impact=f"Budget increase: ${proposed_increase:,.0f} | Schedule recovery: ~{slip.get('slip_days', 0)} days",
        )
        _hitl_queue.append(item)
        new_items.append(item)

        log_activity("Procurement Agent", "🛒",
                     f"Change order requested: PO {po_number}",
                     item.summary)

    log_activity("System", "⏳", "HITL items created",
                 f"{len(new_items)} change order approvals queued")
    return new_items


def trigger_supplier_qualification_review() -> List[HITLItem]:
    """Workflow 6: Flag at-risk suppliers for human review."""
    log_activity("System", "⚡", "HITL Workflow triggered",
                 "Supplier Qualification Review — scanning for at-risk suppliers")

    g = get_graph()
    suppliers = g.get_vertices_by_label("Supplier")
    at_risk = [s for s in suppliers if s.get("compliance_score", 100) < 75]

    new_items = []
    for sup in at_risk:
        existing = [i for i in _hitl_queue
                    if i.details.get("supplier_id") == sup["id"]
                    and i.status == "pending"]
        if existing:
            continue

        linked_pos = g.incoming(sup["id"], "CONTRACTED_WITH")

        item = HITLItem(
            title=f"Supplier Review: {sup.get('name', sup['id'])}",
            workflow_name="Supplier Qualification Review",
            requesting_agent="Procurement Agent",
            summary=(
                f"Supplier {sup.get('name', '')} has compliance score "
                f"{sup.get('compliance_score', 0)}% (threshold: 75%). "
                f"Currently has {len(linked_pos)} linked PO(s)."
            ),
            details={
                "supplier_id": sup["id"],
                "supplier_name": sup.get("name", ""),
                "country": sup.get("country", ""),
                "compliance_score": sup.get("compliance_score", 0),
                "qualification_status": sup.get("qualification_status", ""),
                "performance_rating": sup.get("performance_rating", 0),
                "linked_pos": [po.get("po_number", po["id"]) for po in linked_pos],
                "options": ["Continue", "Place on Watch List", "Disqualify"],
            },
            impact=f"Affects {len(linked_pos)} active PO(s)",
        )
        _hitl_queue.append(item)
        new_items.append(item)

        log_activity("Procurement Agent", "🛒",
                     f"Supplier review flagged: {sup.get('name', '')}",
                     item.summary)

    log_activity("System", "⏳", "HITL items created",
                 f"{len(new_items)} supplier reviews queued")
    return new_items


def clear_hitl_queue() -> None:
    _hitl_queue.clear()


# ── Registry ────────────────────────────────────────────────────────────────

HITL_WORKFLOWS = {
    "iwp_release_approval": {
        "name": "IWP Release Approval",
        "description": "Review and approve ready IWPs for field release",
        "trigger": trigger_iwp_release_approval,
    },
    "change_order_approval": {
        "name": "Change Order Approval",
        "description": "Review PO change orders for slipping deliveries",
        "trigger": trigger_change_order_approval,
    },
    "supplier_qualification_review": {
        "name": "Supplier Qualification Review",
        "description": "Review at-risk suppliers with low compliance scores",
        "trigger": trigger_supplier_qualification_review,
    },
}
