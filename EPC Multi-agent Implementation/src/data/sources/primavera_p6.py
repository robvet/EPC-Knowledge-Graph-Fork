"""Primavera P6 — schedule data source.

Generates WBS, activities, milestones and dependencies for a realistic
LNG processing facility project.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple

from src.graph.client import GraphClient
from src.graph.models import (
    WBS, Activity, ActivityStatus, DependencyType, DependsOnEdge,
    Milestone, MilestoneStatus, MilestoneType, Phase, PhaseType, SimpleEdge,
)


def _d(base: date, offset_days: int) -> date:
    return base + timedelta(days=offset_days)


def ingest(graph: GraphClient, project_id: str = "PRJ-001") -> None:
    """Populate schedule data into *graph*."""

    base = date(2025, 1, 15)  # project start

    # ── Phases ───────────────────────────────────────────────────────
    phases = [
        Phase(id="PH-01", name="FEED", phase_type=PhaseType.FEED,
              status=ActivityStatus.COMPLETED,
              planned_start=_d(base, 0), planned_finish=_d(base, 90),
              actual_start=_d(base, 0), actual_finish=_d(base, 95)),
        Phase(id="PH-02", name="Detail Design", phase_type=PhaseType.DETAIL_DESIGN,
              status=ActivityStatus.COMPLETED,
              planned_start=_d(base, 91), planned_finish=_d(base, 240),
              actual_start=_d(base, 96), actual_finish=_d(base, 250)),
        Phase(id="PH-03", name="Procurement", phase_type=PhaseType.PROCUREMENT,
              status=ActivityStatus.IN_PROGRESS,
              planned_start=_d(base, 180), planned_finish=_d(base, 400),
              actual_start=_d(base, 190)),
        Phase(id="PH-04", name="Construction", phase_type=PhaseType.CONSTRUCTION,
              status=ActivityStatus.IN_PROGRESS,
              planned_start=_d(base, 300), planned_finish=_d(base, 550),
              actual_start=_d(base, 310)),
        Phase(id="PH-05", name="Commissioning", phase_type=PhaseType.COMMISSIONING,
              status=ActivityStatus.NOT_STARTED,
              planned_start=_d(base, 520), planned_finish=_d(base, 600)),
    ]
    for ph in phases:
        graph.add_vertex("Phase", ph)
        graph.add_edge("BELONGS_TO", ph.id, project_id)

    # ── WBS hierarchy ────────────────────────────────────────────────
    wbs_nodes = [
        WBS(id="WBS-1", code="1.0", name="LNG Processing Facility", level=1),
        WBS(id="WBS-1.1", code="1.1", name="Process Engineering", level=2, parent_wbs_id="WBS-1"),
        WBS(id="WBS-1.2", code="1.2", name="Mechanical/Piping", level=2, parent_wbs_id="WBS-1"),
        WBS(id="WBS-1.3", code="1.3", name="Electrical & Instrumentation", level=2, parent_wbs_id="WBS-1"),
        WBS(id="WBS-1.4", code="1.4", name="Civil/Structural", level=2, parent_wbs_id="WBS-1"),
        WBS(id="WBS-1.5", code="1.5", name="Procurement", level=2, parent_wbs_id="WBS-1"),
        WBS(id="WBS-1.1.1", code="1.1.1", name="Process Design", level=3, parent_wbs_id="WBS-1.1"),
        WBS(id="WBS-1.1.2", code="1.1.2", name="HAZOP Studies", level=3, parent_wbs_id="WBS-1.1"),
        WBS(id="WBS-1.2.1", code="1.2.1", name="Equipment Procurement", level=3, parent_wbs_id="WBS-1.2"),
        WBS(id="WBS-1.2.2", code="1.2.2", name="Piping Installation", level=3, parent_wbs_id="WBS-1.2"),
        WBS(id="WBS-1.4.1", code="1.4.1", name="Foundation Works", level=3, parent_wbs_id="WBS-1.4"),
        WBS(id="WBS-1.4.2", code="1.4.2", name="Steel Erection", level=3, parent_wbs_id="WBS-1.4"),
    ]
    for w in wbs_nodes:
        graph.add_vertex("WBS", w)
        graph.add_edge("BELONGS_TO", w.id, project_id)
        if w.parent_wbs_id:
            graph.add_edge("PARENT_OF", w.parent_wbs_id, w.id, level=w.level)

    # ── Activities ───────────────────────────────────────────────────
    activities: List[Activity] = [
        # FEED phase — completed
        Activity(id="ACT-001", name="Process Simulation & FEED", activity_type="Task",
                 planned_start=_d(base, 0), planned_finish=_d(base, 45),
                 actual_start=_d(base, 0), actual_finish=_d(base, 48),
                 duration_days=45, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-002", name="HAZOP Study", activity_type="Task",
                 planned_start=_d(base, 46), planned_finish=_d(base, 75),
                 actual_start=_d(base, 49), actual_finish=_d(base, 80),
                 duration_days=30, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-003", name="FEED Deliverables Package", activity_type="Task",
                 planned_start=_d(base, 76), planned_finish=_d(base, 90),
                 actual_start=_d(base, 81), actual_finish=_d(base, 95),
                 duration_days=15, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),

        # Detail Design — completed
        Activity(id="ACT-004", name="P&ID Development", activity_type="Task",
                 planned_start=_d(base, 91), planned_finish=_d(base, 150),
                 actual_start=_d(base, 96), actual_finish=_d(base, 158),
                 duration_days=60, total_float=5, pct_complete=100, is_critical=False,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-005", name="Equipment Datasheet Preparation", activity_type="Task",
                 planned_start=_d(base, 120), planned_finish=_d(base, 170),
                 actual_start=_d(base, 125), actual_finish=_d(base, 175),
                 duration_days=50, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-006", name="3D Model Development", activity_type="Task",
                 planned_start=_d(base, 130), planned_finish=_d(base, 220),
                 actual_start=_d(base, 135), actual_finish=_d(base, 230),
                 duration_days=90, total_float=3, pct_complete=100, is_critical=False,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-007", name="Instrument Index & Hook-up", activity_type="Task",
                 planned_start=_d(base, 160), planned_finish=_d(base, 210),
                 actual_start=_d(base, 165), actual_finish=_d(base, 220),
                 duration_days=50, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),
        Activity(id="ACT-008", name="MTO & Material Requisitions", activity_type="Task",
                 planned_start=_d(base, 200), planned_finish=_d(base, 240),
                 actual_start=_d(base, 210), actual_finish=_d(base, 250),
                 duration_days=40, total_float=0, pct_complete=100, is_critical=True,
                 status=ActivityStatus.COMPLETED),

        # Procurement — in progress
        Activity(id="ACT-009", name="Long-Lead Equipment Ordering", activity_type="Task",
                 planned_start=_d(base, 200), planned_finish=_d(base, 330),
                 actual_start=_d(base, 215),
                 duration_days=130, total_float=0, pct_complete=65, is_critical=True,
                 status=ActivityStatus.IN_PROGRESS),
        Activity(id="ACT-010", name="Bulk Material Procurement", activity_type="Task",
                 planned_start=_d(base, 250), planned_finish=_d(base, 370),
                 actual_start=_d(base, 260),
                 duration_days=120, total_float=8, pct_complete=45, is_critical=False,
                 status=ActivityStatus.IN_PROGRESS),
        Activity(id="ACT-011", name="Vendor Document Review", activity_type="Task",
                 planned_start=_d(base, 280), planned_finish=_d(base, 380),
                 actual_start=_d(base, 290),
                 duration_days=100, total_float=0, pct_complete=35, is_critical=True,
                 status=ActivityStatus.IN_PROGRESS),
        Activity(id="ACT-012", name="Expediting & Inspection", activity_type="Task",
                 planned_start=_d(base, 300), planned_finish=_d(base, 400),
                 actual_start=_d(base, 312),
                 duration_days=100, total_float=3, pct_complete=25, is_critical=False,
                 status=ActivityStatus.IN_PROGRESS),

        # Construction — early stages
        Activity(id="ACT-013", name="Site Preparation & Earthworks", activity_type="Task",
                 planned_start=_d(base, 300), planned_finish=_d(base, 340),
                 actual_start=_d(base, 310),
                 duration_days=40, total_float=0, pct_complete=70, is_critical=True,
                 status=ActivityStatus.IN_PROGRESS),
        Activity(id="ACT-014", name="Foundation Construction", activity_type="Task",
                 planned_start=_d(base, 330), planned_finish=_d(base, 390),
                 actual_start=_d(base, 342),
                 duration_days=60, total_float=0, pct_complete=30, is_critical=True,
                 status=ActivityStatus.IN_PROGRESS),
        Activity(id="ACT-015", name="Steel Structure Erection", activity_type="Task",
                 planned_start=_d(base, 370), planned_finish=_d(base, 440),
                 duration_days=70, total_float=0, pct_complete=0, is_critical=True,
                 status=ActivityStatus.NOT_STARTED),
        Activity(id="ACT-016", name="Equipment Installation", activity_type="Task",
                 planned_start=_d(base, 400), planned_finish=_d(base, 480),
                 duration_days=80, total_float=0, pct_complete=0, is_critical=True,
                 status=ActivityStatus.NOT_STARTED),
        Activity(id="ACT-017", name="Piping Installation", activity_type="Task",
                 planned_start=_d(base, 410), planned_finish=_d(base, 500),
                 duration_days=90, total_float=5, pct_complete=0, is_critical=False,
                 status=ActivityStatus.NOT_STARTED),
        Activity(id="ACT-018", name="E&I Installation", activity_type="Task",
                 planned_start=_d(base, 430), planned_finish=_d(base, 510),
                 duration_days=80, total_float=4, pct_complete=0, is_critical=False,
                 status=ActivityStatus.NOT_STARTED),
        Activity(id="ACT-019", name="Pre-commissioning", activity_type="Task",
                 planned_start=_d(base, 500), planned_finish=_d(base, 540),
                 duration_days=40, total_float=0, pct_complete=0, is_critical=True,
                 status=ActivityStatus.NOT_STARTED),
        Activity(id="ACT-020", name="Commissioning & Handover", activity_type="Task",
                 planned_start=_d(base, 540), planned_finish=_d(base, 600),
                 duration_days=60, total_float=0, pct_complete=0, is_critical=True,
                 status=ActivityStatus.NOT_STARTED),
    ]
    phase_map = {
        "ACT-001": "PH-01", "ACT-002": "PH-01", "ACT-003": "PH-01",
        "ACT-004": "PH-02", "ACT-005": "PH-02", "ACT-006": "PH-02",
        "ACT-007": "PH-02", "ACT-008": "PH-02",
        "ACT-009": "PH-03", "ACT-010": "PH-03", "ACT-011": "PH-03",
        "ACT-012": "PH-03",
        "ACT-013": "PH-04", "ACT-014": "PH-04", "ACT-015": "PH-04",
        "ACT-016": "PH-04", "ACT-017": "PH-04", "ACT-018": "PH-04",
        "ACT-019": "PH-05", "ACT-020": "PH-05",
    }
    for a in activities:
        graph.add_vertex("Activity", a)
        graph.add_edge("BELONGS_TO", a.id, project_id)
        if a.id in phase_map:
            graph.add_edge("IN_PHASE", a.id, phase_map[a.id])

    # ── Dependencies (critical chain) ────────────────────────────────
    deps: List[Tuple[str, str, str, int]] = [
        ("ACT-001", "ACT-002", "FS", 0),
        ("ACT-002", "ACT-003", "FS", 0),
        ("ACT-003", "ACT-004", "FS", 0),
        ("ACT-003", "ACT-005", "FS", 5),
        ("ACT-004", "ACT-006", "FS", 0),
        ("ACT-005", "ACT-007", "FS", 0),
        ("ACT-005", "ACT-008", "FS", 10),
        ("ACT-008", "ACT-009", "FS", 0),
        ("ACT-008", "ACT-010", "FS", 10),
        ("ACT-009", "ACT-011", "FS", 15),
        ("ACT-011", "ACT-012", "FS", 0),
        ("ACT-009", "ACT-013", "SS", 60),
        ("ACT-013", "ACT-014", "FS", 0),
        ("ACT-014", "ACT-015", "FS", 0),
        ("ACT-009", "ACT-016", "FS", 0),
        ("ACT-015", "ACT-016", "SS", 20),
        ("ACT-016", "ACT-017", "SS", 10),
        ("ACT-016", "ACT-018", "SS", 20),
        ("ACT-017", "ACT-019", "FS", 0),
        ("ACT-018", "ACT-019", "FS", 0),
        ("ACT-019", "ACT-020", "FS", 0),
    ]
    for from_id, to_id, dep_type, lag in deps:
        graph.add_edge("DEPENDS_ON", from_id, to_id,
                       dependency_type=dep_type, lag_days=lag)

    # ── Milestones ───────────────────────────────────────────────────
    milestones = [
        Milestone(id="MS-01", name="FEED Approval Gate",
                  milestone_type=MilestoneType.GATE,
                  planned_date=_d(base, 90), actual_date=_d(base, 95),
                  status=MilestoneStatus.ACHIEVED),
        Milestone(id="MS-02", name="MTO Issued",
                  milestone_type=MilestoneType.INTERNAL,
                  planned_date=_d(base, 240), actual_date=_d(base, 250),
                  status=MilestoneStatus.ACHIEVED),
        Milestone(id="MS-03", name="Long-Lead Equipment Ordered",
                  milestone_type=MilestoneType.CONTRACTUAL,
                  planned_date=_d(base, 260),
                  status=MilestoneStatus.ACHIEVED),
        Milestone(id="MS-04", name="Construction Start",
                  milestone_type=MilestoneType.GATE,
                  planned_date=_d(base, 300), actual_date=_d(base, 310),
                  status=MilestoneStatus.ACHIEVED),
        Milestone(id="MS-05", name="Major Equipment On-Site",
                  milestone_type=MilestoneType.CONTRACTUAL,
                  planned_date=_d(base, 380),
                  status=MilestoneStatus.AT_RISK),
        Milestone(id="MS-06", name="Mechanical Completion",
                  milestone_type=MilestoneType.CONTRACTUAL,
                  planned_date=_d(base, 500),
                  status=MilestoneStatus.PENDING),
        Milestone(id="MS-07", name="Ready for Start-Up",
                  milestone_type=MilestoneType.GATE,
                  planned_date=_d(base, 540),
                  status=MilestoneStatus.PENDING),
        Milestone(id="MS-08", name="Project Handover",
                  milestone_type=MilestoneType.CONTRACTUAL,
                  planned_date=_d(base, 600),
                  status=MilestoneStatus.PENDING),
    ]
    milestone_activity = {
        "MS-01": "ACT-003", "MS-02": "ACT-008", "MS-03": "ACT-009",
        "MS-04": "ACT-013", "MS-05": "ACT-009", "MS-06": "ACT-017",
        "MS-07": "ACT-019", "MS-08": "ACT-020",
    }
    for ms in milestones:
        graph.add_vertex("Milestone", ms)
        graph.add_edge("BELONGS_TO", ms.id, project_id)
        if ms.id in milestone_activity:
            graph.add_edge("ACHIEVES", milestone_activity[ms.id], ms.id)
