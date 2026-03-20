"""Graph query tools exposed as callable functions for agents.

Each function is designed to be registered as an agent tool — it takes simple
primitive arguments and returns a JSON-serialisable dict.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.graph.client import get_graph
from src.graph import queries


def tool_get_project_dashboard(project_id: str = "PRJ-001") -> Dict[str, Any]:
    """Get aggregated KPI dashboard for the project including schedule progress,
    procurement status, work package readiness, and milestone health."""
    return queries.get_project_dashboard(get_graph(), project_id)


def tool_get_critical_path(project_id: str = "PRJ-001") -> List[Dict]:
    """Get all activities on the critical path — these are the activities
    that directly determine the project end date."""
    return queries.get_critical_path(get_graph(), project_id)


def tool_get_schedule_variance(project_id: str = "PRJ-001") -> List[Dict]:
    """Find activities that are behind plan (actual progress more than 10%
    below expected progress based on elapsed time)."""
    return queries.get_schedule_variance(get_graph(), project_id)


def tool_get_float_erosion(project_id: str = "PRJ-001", threshold_days: int = 5) -> List[Dict]:
    """Find activities whose total float has eroded below the threshold,
    meaning they are at risk of becoming critical."""
    return queries.get_float_erosion(get_graph(), project_id, threshold_days)


def tool_get_pending_deliveries(project_id: str = "PRJ-001") -> List[Dict]:
    """Get all purchase orders that have not yet been delivered."""
    return queries.get_pending_deliveries(get_graph(), project_id)


def tool_get_supplier_risk_profile(supplier_id: str = "") -> Dict[str, Any]:
    """Get detailed risk profile for a supplier including compliance score,
    open PO count, and risk classification."""
    return queries.get_supplier_risk_profile(get_graph(), supplier_id) or {}


def tool_get_material_need_vs_delivery(project_id: str = "PRJ-001") -> List[Dict]:
    """Find materials where the PO delivery date is later than the construction
    need date — these are materials that will cause schedule delays."""
    return queries.get_material_need_vs_delivery(get_graph(), project_id)


def tool_get_iwp_constraint_status(project_id: str = "PRJ-001") -> Dict[str, List[Dict]]:
    """Check all IWPs and categorise them as 'ready' (all constraints clear)
    or 'blocked' (one or more constraints not met)."""
    return queries.get_iwp_constraint_status(get_graph(), project_id)


def tool_get_milestone_status(project_id: str = "PRJ-001") -> List[Dict]:
    """Get status of all project milestones."""
    return queries.get_milestone_status(get_graph(), project_id)


def tool_get_delivery_cascade_impact(po_id: str = "") -> Dict[str, Any]:
    """Trace the cascade impact of a PO delay: which materials, activities,
    and milestones are affected."""
    return queries.get_delivery_cascade_impact(get_graph(), po_id)


# ── Tool Registry ───────────────────────────────────────────────────────────

ALL_TOOLS = {
    "get_project_dashboard": tool_get_project_dashboard,
    "get_critical_path": tool_get_critical_path,
    "get_schedule_variance": tool_get_schedule_variance,
    "get_float_erosion": tool_get_float_erosion,
    "get_pending_deliveries": tool_get_pending_deliveries,
    "get_supplier_risk_profile": tool_get_supplier_risk_profile,
    "get_material_need_vs_delivery": tool_get_material_need_vs_delivery,
    "get_iwp_constraint_status": tool_get_iwp_constraint_status,
    "get_milestone_status": tool_get_milestone_status,
    "get_delivery_cascade_impact": tool_get_delivery_cascade_impact,
}
