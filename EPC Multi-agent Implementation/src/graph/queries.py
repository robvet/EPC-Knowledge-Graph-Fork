"""Reusable graph queries for the EPC Golden Triangle agents.

Each function operates on a :class:`GraphClient` and returns structured data
that agent tools can serialise and return to the LLM.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.api_models import (
    ActivityResponse,
    DashboardMilestonesResponse,
    DashboardProcurementResponse,
    DashboardResponse,
    DashboardScheduleResponse,
    DashboardWorkPackagesResponse,
    DeliveryCascadeImpactResponse,
    IWPConstraintStatusResponse,
    MaterialResponse,
    MilestoneResponse,
    ProcurementSlipResponse,
    PurchaseOrderResponse,
    SupplierRiskProfileResponse,
    WorkPackageConstraintStatusResponse,
)
from src.graph.client import GraphClient, get_graph


def _today() -> str:
    return date.today().isoformat()


# ── Scheduling Queries ──────────────────────────────────────────────────────

def get_critical_path(graph: Optional[GraphClient] = None, project_id: str = "") -> List[Dict]:
    """Return all activities on the critical path (is_critical == True)."""
    g = graph or get_graph()
    activities = g.get_vertices_by_label("Activity")
    return [ActivityResponse(**a).model_dump() for a in activities if a.get("is_critical")]


def get_schedule_variance(graph: Optional[GraphClient] = None, project_id: str = "") -> List[Dict]:
    """Return activities that are behind plan (pct_complete < expected)."""
    g = graph or get_graph()
    behind = []
    today = date.today()
    for a in g.get_vertices_by_label("Activity"):
        ps = a.get("planned_start")
        pf = a.get("planned_finish")
        pct = a.get("pct_complete", 0)
        if not ps or not pf:
            continue
        try:
            start = date.fromisoformat(ps) if isinstance(ps, str) else ps
            finish = date.fromisoformat(pf) if isinstance(pf, str) else pf
        except (TypeError, ValueError):
            continue
        total = (finish - start).days or 1
        elapsed = (today - start).days
        if elapsed <= 0:
            continue
        expected_pct = min(100.0, (elapsed / total) * 100)
        if pct < expected_pct - 10:  # >10% behind threshold
            behind.append({
                **a,
                "expected_pct": round(expected_pct, 1),
                "variance": round(pct - expected_pct, 1),
            })
    validated = [ActivityResponse(**activity).model_dump() for activity in behind]
    return sorted(validated, key=lambda x: x["variance"])


def get_float_erosion(
    graph: Optional[GraphClient] = None,
    project_id: str = "",
    threshold_days: int = 5,
) -> List[Dict]:
    """Activities whose total float is below *threshold_days*."""
    g = graph or get_graph()
    return [
        ActivityResponse(**a).model_dump()
        for a in g.get_vertices_by_label("Activity")
        if a.get("total_float", 999) <= threshold_days
        and a.get("status") != "Completed"
    ]


# ── Procurement Queries ─────────────────────────────────────────────────────

def get_pending_deliveries(graph: Optional[GraphClient] = None, project_id: str = "") -> List[Dict]:
    """POs that are not yet delivered."""
    g = graph or get_graph()
    return [
        PurchaseOrderResponse(**po).model_dump()
        for po in g.get_vertices_by_label("PurchaseOrder")
        if po.get("status") not in ("Delivered", "Closed")
    ]


def get_supplier_risk_profile(
    graph: Optional[GraphClient] = None,
    supplier_id: str = "",
) -> Optional[Dict]:
    """Return supplier details + linked POs + compliance assessment."""
    g = graph or get_graph()
    supplier = g.get_vertex(supplier_id)
    if not supplier:
        return None
    linked_pos = g.incoming(supplier_id, "CONTRACTED_WITH")
    open_po_count = sum(
        1 for po in linked_pos if po.get("status") not in ("Delivered", "Closed")
    )
    return SupplierRiskProfileResponse(**{
        **supplier,
        "open_po_count": open_po_count,
        "total_po_count": len(linked_pos),
        "risk_level": (
            "High" if supplier.get("compliance_score", 100) < 70
            else "Medium" if supplier.get("compliance_score", 100) < 85
            else "Low"
        ),
    }).model_dump()


def get_material_need_vs_delivery(
    graph: Optional[GraphClient] = None,
    project_id: str = "",
) -> List[Dict]:
    """Cross-reference material need-dates with PO delivery dates.

    Returns materials where delivery date > need date (slipping).
    """
    g = graph or get_graph()
    slips = []
    for mat in g.get_vertices_by_label("Material"):
        # Find linked PO
        po_list = g.outgoing(mat["id"], "ORDERED_VIA")
        if not po_list:
            continue
        po = po_list[0]
        delivery = po.get("promised_delivery_date")
        # Find need-date from NEEDED_BY edge
        needed_edges = g.get_edges(label="NEEDED_BY", from_id=mat["id"])
        if not needed_edges:
            continue
        need = needed_edges[0].get("need_date")
        if not delivery or not need:
            continue
        try:
            d_date = date.fromisoformat(delivery) if isinstance(delivery, str) else delivery
            n_date = date.fromisoformat(need) if isinstance(need, str) else need
        except (TypeError, ValueError):
            continue
        if d_date > n_date:
            slip_days = (d_date - n_date).days
            slips.append({
                "material_id": mat["id"],
                "material_tag": mat.get("tag_number", ""),
                "description": mat.get("description", ""),
                "po_number": po.get("po_number", ""),
                "need_date": need if isinstance(need, str) else need.isoformat(),
                "delivery_date": delivery if isinstance(delivery, str) else delivery.isoformat(),
                "slip_days": slip_days,
            })
    validated = [ProcurementSlipResponse(**slip).model_dump() for slip in slips]
    return sorted(validated, key=lambda x: -x["slip_days"])


# ── Project Delivery Queries ────────────────────────────────────────────────

def get_iwp_constraint_status(
    graph: Optional[GraphClient] = None,
    project_id: str = "",
) -> Dict[str, List[Dict]]:
    """Categorise IWPs into 'ready' and 'blocked' based on constraints."""
    g = graph or get_graph()
    ready, blocked = [], []
    for wp in g.find_vertices("WorkPackage", wp_type="IWP"):
        constraints = {
            "engineering_ready": wp.get("engineering_ready", False),
            "materials_ready": wp.get("materials_ready", False),
            "scaffolding_ready": wp.get("scaffolding_ready", False),
            "permits_ready": wp.get("permits_ready", False),
        }
        all_clear = all(constraints.values())
        entry = WorkPackageConstraintStatusResponse(
            "id": wp["id"],
            "name": wp.get("name", ""),
            "discipline": wp.get("discipline", ""),
            "status": wp.get("status", ""),
            "constraints": constraints,
            "constraints_clear": all_clear,
        ).model_dump()
        (ready if all_clear else blocked).append(entry)
    return IWPConstraintStatusResponse(ready=ready, blocked=blocked).model_dump()


def get_milestone_status(
    graph: Optional[GraphClient] = None,
    project_id: str = "",
) -> List[Dict]:
    """Return all milestones with their current status."""
    g = graph or get_graph()
    return [MilestoneResponse(**milestone).model_dump() for milestone in g.get_vertices_by_label("Milestone")]


# ── Cross-Domain Queries ────────────────────────────────────────────────────

def get_delivery_cascade_impact(
    graph: Optional[GraphClient] = None,
    po_id: str = "",
) -> Dict[str, Any]:
    """Trace a PO delay → affected materials → activities → milestones."""
    g = graph or get_graph()
    po_lookup = po_id.strip()
    po = g.get_vertex(po_lookup)
    if not po and po_lookup:
        normalized = po_lookup.upper()
        for candidate in g.get_vertices_by_label("PurchaseOrder"):
            candidate_id = str(candidate.get("id", "")).upper()
            candidate_number = str(candidate.get("po_number", "")).upper()
            if normalized in {candidate_id, candidate_number}:
                po = candidate
                po_lookup = candidate.get("id", po_lookup)
                break
    if not po:
        return {"error": f"PO {po_id} not found"}

    # Materials on this PO
    affected_materials = g.incoming(po_lookup, "ORDERED_VIA")

    # Activities that need those materials
    affected_activities = []
    for mat in affected_materials:
        needed_edges = g.get_edges(label="NEEDED_BY", from_id=mat["id"])
        for edge in needed_edges:
            act = g.get_vertex(edge["to_id"])
            if act:
                affected_activities.append(act)

    # Milestones that those activities achieve
    affected_milestones = []
    for act in affected_activities:
        ms_list = g.outgoing(act["id"], "ACHIEVES")
        affected_milestones.extend(ms_list)

    return DeliveryCascadeImpactResponse(
        po=PurchaseOrderResponse(**po),
        affected_materials=[MaterialResponse(**item) for item in affected_materials],
        affected_activities=[ActivityResponse(**item) for item in affected_activities],
        affected_milestones=[MilestoneResponse(**item) for item in affected_milestones],
        impact_summary=(
            f"PO {po.get('po_number', po_id)} delay impacts "
            f"{len(affected_materials)} material(s), "
            f"{len(affected_activities)} activity/activities, "
            f"{len(affected_milestones)} milestone(s)"
        ),
    ).model_dump()


def get_project_dashboard(
    graph: Optional[GraphClient] = None,
    project_id: str = "",
) -> Dict[str, Any]:
    """Aggregated KPI dashboard for the project."""
    g = graph or get_graph()

    activities = g.get_vertices_by_label("Activity")
    total_act = len(activities) or 1
    completed = sum(1 for a in activities if a.get("status") == "Completed")
    in_progress = sum(1 for a in activities if a.get("status") == "In Progress")
    avg_pct = sum(a.get("pct_complete", 0) for a in activities) / total_act

    pos = g.get_vertices_by_label("PurchaseOrder")
    open_pos = [po for po in pos if po.get("status") not in ("Delivered", "Closed")]

    iwp_status = get_iwp_constraint_status(g, project_id)

    milestones = g.get_vertices_by_label("Milestone")
    at_risk = [m for m in milestones if m.get("status") in ("At Risk", "Missed")]

    slips = get_material_need_vs_delivery(g, project_id)

    return DashboardResponse(
        schedule=DashboardScheduleResponse(
            "total_activities": total_act,
            "completed": completed,
            "in_progress": in_progress,
            "avg_pct_complete": round(avg_pct, 1),
            "critical_path_count": sum(1 for a in activities if a.get("is_critical")),
        ),
        procurement=DashboardProcurementResponse(
            "total_pos": len(pos),
            "open_pos": len(open_pos),
            "material_slips": len(slips),
            "top_slips": slips[:3],
        ),
        work_packages=DashboardWorkPackagesResponse(
            "iwp_ready": len(iwp_status["ready"]),
            "iwp_blocked": len(iwp_status["blocked"]),
            "total_iwps": len(iwp_status["ready"]) + len(iwp_status["blocked"]),
        ),
        milestones=DashboardMilestonesResponse(
            "total": len(milestones),
            "at_risk": len(at_risk),
            "achieved": sum(1 for m in milestones if m.get("status") == "Achieved"),
        ),
    ).model_dump()
