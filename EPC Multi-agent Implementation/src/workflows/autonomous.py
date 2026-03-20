"""Autonomous workflows — run without human intervention."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from src.agents import log_activity
from src.api_models import (
    ConstraintBlockerResponse,
    DeliveryCascadeSummaryResponse,
    DocumentReadinessWorkflowResponse,
    ProcurementDelayCascadeWorkflowResponse,
    ScheduleVarianceWorkflowResponse,
)
from src.agents.orchestrator import OrchestratorAgent
from src.agents.scheduling import SchedulingAgent
from src.agents.procurement import ProcurementAgent
from src.agents.project_delivery import ProjectDeliveryAgent


def run_procurement_delay_cascade() -> Dict[str, Any]:
    """Workflow 1: Detect procurement delays and trace schedule impact.

    Fully autonomous — no human approval needed.
    """
    log_activity("System", "⚡", "Workflow triggered",
                 "Procurement Delay Cascade — autonomous scan starting")

    procurement = ProcurementAgent()
    scheduling = SchedulingAgent()

    # Step 1: Procurement agent scans for material slips
    log_activity("System", "⚡", "Step 1/4", "Procurement Agent scanning for delivery slips...")
    slips = procurement.respond("Check material delivery slips vs need dates")
    slip_data = slips.get("data", [])

    if not slip_data:
        log_activity("System", "✅", "Workflow complete",
                     "No procurement delays detected — all deliveries on track")
        return ProcurementDelayCascadeWorkflowResponse(
            workflow="Procurement Delay Cascade",
            status="completed",
            result="No delays detected",
            steps_completed=1,
        ).model_dump()

    # Step 2: For each slipping PO, trace cascade impact
    log_activity("System", "⚡", "Step 2/4",
                 f"Tracing cascade impact for {len(slip_data)} slipping materials...")
    cascade_results = []
    for slip in slip_data[:3]:  # Top 3 worst slips
        po_id = slip.get("po_number", "")
        # Find PO vertex ID from the graph
        from src.graph.client import get_graph
        g = get_graph()
        pos = g.find_vertices("PurchaseOrder", po_number=po_id)
        if pos:
            impact = scheduling.respond(f"Analyze cascade impact for {pos[0]['id']}")
            cascade_results.append({
                "material": slip.get("material_tag", ""),
                "po": po_id,
                "slip_days": slip.get("slip_days", 0),
                "impact": impact.get("data", {}),
            })

    # Step 3: Scheduling agent checks milestone impact
    log_activity("System", "⚡", "Step 3/4",
                 "Scheduling Agent checking milestone impact...")
    milestones = scheduling.respond("Check milestone status")

    # Step 4: Generate consolidated report
    log_activity("System", "⚡", "Step 4/4", "Generating delay impact report...")

    affected_milestones = [m for m in milestones.get("data", [])
                           if m.get("status") in ("At Risk", "Missed")]

    report = ProcurementDelayCascadeWorkflowResponse(
        workflow="Procurement Delay Cascade",
        status="completed",
        total_material_slips=len(slip_data),
        cascades_analyzed=len(cascade_results),
        affected_milestones=len(affected_milestones),
        cascade_details=[DeliveryCascadeSummaryResponse(**item) for item in cascade_results],
        recommendations=[
            f"Expedite PO {s.get('po_number', '')} — {s.get('slip_days', 0)} days behind need date"
            for s in slip_data[:3]
        ],
        steps_completed=4,
    ).model_dump()

    log_activity("System", "✅", "Workflow complete",
                 f"Procurement Delay Cascade — {len(slip_data)} slips detected, "
                 f"{len(affected_milestones)} milestones at risk")

    return report


def run_schedule_variance_detection() -> Dict[str, Any]:
    """Workflow 2: Scan for activities behind plan.

    Fully autonomous — generates variance report.
    """
    log_activity("System", "⚡", "Workflow triggered",
                 "Schedule Variance Detection — autonomous scan starting")

    scheduling = SchedulingAgent()

    # Step 1: Run variance scan
    log_activity("System", "⚡", "Step 1/3",
                 "Scanning for activities >10% behind plan...")
    variance = scheduling.respond("Check schedule variance for behind-plan activities")
    variance_data = variance.get("data", [])

    # Step 2: Check float erosion
    log_activity("System", "⚡", "Step 2/3", "Checking float erosion...")
    float_data = scheduling.respond("Check float erosion")

    # Step 3: Generate report
    log_activity("System", "⚡", "Step 3/3", "Generating variance report...")

    report = ScheduleVarianceWorkflowResponse(
        workflow="Schedule Variance Detection",
        status="completed",
        activities_behind=len(variance_data),
        low_float_activities=len(float_data.get("data", [])),
        variance_details=variance_data,
        recommendations=[
            f"Fast-track {a.get('name', '')}: {a.get('variance', 0)}% behind"
            for a in variance_data[:5]
        ] if variance_data else ["All activities on track"],
        steps_completed=3,
    ).model_dump()

    log_activity("System", "✅", "Workflow complete",
                 f"Schedule Variance — {len(variance_data)} activities behind plan")

    return report


def run_document_readiness_check() -> Dict[str, Any]:
    """Workflow 3: Check IWP constraint readiness.

    Fully autonomous — marks ready IWPs and generates constraint reports.
    """
    log_activity("System", "⚡", "Workflow triggered",
                 "Document Readiness Check — autonomous scan starting")

    delivery = ProjectDeliveryAgent()

    # Step 1: Check all IWP constraints
    log_activity("System", "⚡", "Step 1/2",
                 "Checking IWP constraints across all work packages...")
    result = delivery.respond("Check IWP constraint readiness status")
    iwp_data = result.get("data", {})

    ready = iwp_data.get("ready", [])
    blocked = iwp_data.get("blocked", [])

    # Step 2: Generate readiness report
    log_activity("System", "⚡", "Step 2/2", "Generating readiness report...")

    blockers = []
    for w in blocked:
        missing = [k.replace("_ready", "").replace("_", " ").title()
                   for k, v in w.get("constraints", {}).items() if not v]
        blockers.append(ConstraintBlockerResponse(
            iwp=w.get("name", w.get("id", "")),
            discipline=w.get("discipline", ""),
            blocked_by=missing,
        ))

    report = DocumentReadinessWorkflowResponse(
        workflow="Document Readiness Check",
        status="completed",
        iwps_ready=len(ready),
        iwps_blocked=len(blocked),
        ready_for_release=[w.get("name", w.get("id", "")) for w in ready],
        blockers=blockers,
        steps_completed=2,
    ).model_dump()

    log_activity("System", "✅", "Workflow complete",
                 f"IWP Readiness — {len(ready)} ready, {len(blocked)} blocked")

    return report


# ── Registry ────────────────────────────────────────────────────────────────

AUTONOMOUS_WORKFLOWS = {
    "procurement_delay_cascade": {
        "name": "Procurement Delay Cascade",
        "description": "Detect PO delivery slips, trace schedule/milestone impact",
        "run": run_procurement_delay_cascade,
    },
    "schedule_variance_detection": {
        "name": "Schedule Variance Detection",
        "description": "Scan for behind-plan activities and float erosion",
        "run": run_schedule_variance_detection,
    },
    "document_readiness_check": {
        "name": "Document Readiness Check",
        "description": "Check IWP constraints and identify ready/blocked packages",
        "run": run_document_readiness_check,
    },
}
