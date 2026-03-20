"""O3 AWP — Advanced Work Packaging data source.

Generates AWPs → CWPs → IWPs with constraint statuses.  Some IWPs have all
constraints clear (for autonomous release demo); others are deliberately blocked.
"""

from __future__ import annotations
from datetime import date, timedelta
from src.graph.client import GraphClient
from src.graph.models import WPStatus, WPType, WorkPackage


def _d(base: date, offset: int) -> date:
    return base + timedelta(days=offset)


def ingest(graph: GraphClient, project_id: str = "PRJ-001") -> None:
    base = date(2025, 1, 15)

    # ── AWPs (area-level) ────────────────────────────────────────────
    awps = [
        WorkPackage(id="AWP-01", wp_type=WPType.AWP, name="Equipment Area — Foundation & Steel",
                    discipline="Civil/Structural", status=WPStatus.IN_PROGRESS,
                    planned_start=_d(base, 330)),
        WorkPackage(id="AWP-02", wp_type=WPType.AWP, name="Equipment Area — Mechanical Install",
                    discipline="Mechanical", status=WPStatus.PLANNED,
                    planned_start=_d(base, 400)),
        WorkPackage(id="AWP-03", wp_type=WPType.AWP, name="Pipe Rack Area — Piping",
                    discipline="Piping", status=WPStatus.PLANNED,
                    planned_start=_d(base, 410)),
    ]

    # ── CWPs (discipline-level) ──────────────────────────────────────
    cwps = [
        WorkPackage(id="CWP-01", wp_type=WPType.CWP, name="Foundation Concrete Works",
                    discipline="Civil", status=WPStatus.IN_PROGRESS,
                    planned_start=_d(base, 330)),
        WorkPackage(id="CWP-02", wp_type=WPType.CWP, name="Steel Erection — Equipment Area",
                    discipline="Structural", status=WPStatus.PLANNED,
                    planned_start=_d(base, 370)),
        WorkPackage(id="CWP-03", wp_type=WPType.CWP, name="Heavy Equipment Setting",
                    discipline="Mechanical", status=WPStatus.PLANNED,
                    planned_start=_d(base, 400)),
        WorkPackage(id="CWP-04", wp_type=WPType.CWP, name="Main Header Piping",
                    discipline="Piping", status=WPStatus.PLANNED,
                    planned_start=_d(base, 415)),
    ]

    # ── IWPs (crew-level) with constraints ───────────────────────────
    iwps = [
        # ✅ All clear — ready for autonomous release
        WorkPackage(id="IWP-001", wp_type=WPType.IWP, name="Foundation Pour — V-101 Pad",
                    discipline="Civil", status=WPStatus.READY, crew_size=12,
                    planned_start=_d(base, 342), constraints_clear=True,
                    engineering_ready=True, materials_ready=True,
                    scaffolding_ready=True, permits_ready=True),
        # ✅ All clear
        WorkPackage(id="IWP-002", wp_type=WPType.IWP, name="Foundation Pour — HX-101 Pad",
                    discipline="Civil", status=WPStatus.READY, crew_size=10,
                    planned_start=_d(base, 350), constraints_clear=True,
                    engineering_ready=True, materials_ready=True,
                    scaffolding_ready=True, permits_ready=True),
        # ❌ Blocked — materials not on site
        WorkPackage(id="IWP-003", wp_type=WPType.IWP, name="Steel Erection — Bay 1",
                    discipline="Structural", status=WPStatus.BLOCKED, crew_size=15,
                    planned_start=_d(base, 372), constraints_clear=False,
                    engineering_ready=True, materials_ready=False,
                    scaffolding_ready=True, permits_ready=True),
        # ❌ Blocked — engineering drawing in review
        WorkPackage(id="IWP-004", wp_type=WPType.IWP, name="Steel Erection — Bay 2",
                    discipline="Structural", status=WPStatus.BLOCKED, crew_size=15,
                    planned_start=_d(base, 380), constraints_clear=False,
                    engineering_ready=False, materials_ready=False,
                    scaffolding_ready=True, permits_ready=True),
        # ✅ All clear
        WorkPackage(id="IWP-005", wp_type=WPType.IWP, name="Anchor Bolt Installation — C-101",
                    discipline="Civil", status=WPStatus.READY, crew_size=6,
                    planned_start=_d(base, 355), constraints_clear=True,
                    engineering_ready=True, materials_ready=True,
                    scaffolding_ready=True, permits_ready=True),
        # ❌ Blocked — permits pending
        WorkPackage(id="IWP-006", wp_type=WPType.IWP, name="Heavy Lift — V-101 Setting",
                    discipline="Mechanical", status=WPStatus.BLOCKED, crew_size=20,
                    planned_start=_d(base, 405), constraints_clear=False,
                    engineering_ready=True, materials_ready=False,
                    scaffolding_ready=True, permits_ready=False),
        # ❌ Blocked — materials pending
        WorkPackage(id="IWP-007", wp_type=WPType.IWP, name="Main Pipe Header Spool Install",
                    discipline="Piping", status=WPStatus.BLOCKED, crew_size=14,
                    planned_start=_d(base, 418), constraints_clear=False,
                    engineering_ready=True, materials_ready=False,
                    scaffolding_ready=False, permits_ready=True),
        # ✅ All clear
        WorkPackage(id="IWP-008", wp_type=WPType.IWP, name="Cable Tray Installation — Area 1",
                    discipline="Electrical", status=WPStatus.READY, crew_size=8,
                    planned_start=_d(base, 435), constraints_clear=True,
                    engineering_ready=True, materials_ready=True,
                    scaffolding_ready=True, permits_ready=True),
        # ❌ Blocked — engineering + materials
        WorkPackage(id="IWP-009", wp_type=WPType.IWP, name="DCS Cabinet Installation",
                    discipline="Instrumentation", status=WPStatus.BLOCKED, crew_size=6,
                    planned_start=_d(base, 440), constraints_clear=False,
                    engineering_ready=False, materials_ready=False,
                    scaffolding_ready=True, permits_ready=True),
        # ✅ All clear
        WorkPackage(id="IWP-010", wp_type=WPType.IWP, name="Foundation Pour — Pipe Rack PR-01",
                    discipline="Civil", status=WPStatus.READY, crew_size=10,
                    planned_start=_d(base, 360), constraints_clear=True,
                    engineering_ready=True, materials_ready=True,
                    scaffolding_ready=True, permits_ready=True),
    ]

    # CWP <-> IWP parent mapping
    iwp_cwp = {
        "IWP-001": "CWP-01", "IWP-002": "CWP-01", "IWP-005": "CWP-01",
        "IWP-010": "CWP-01",
        "IWP-003": "CWP-02", "IWP-004": "CWP-02",
        "IWP-006": "CWP-03",
        "IWP-007": "CWP-04",
        "IWP-008": "CWP-04", "IWP-009": "CWP-04",
    }
    # CWP <-> AWP parent
    cwp_awp = {
        "CWP-01": "AWP-01", "CWP-02": "AWP-01",
        "CWP-03": "AWP-02",
        "CWP-04": "AWP-03",
    }
    # IWP materials needed
    iwp_materials = {
        "IWP-003": ["MAT-06"],
        "IWP-004": ["MAT-06"],
        "IWP-006": ["MAT-03"],
        "IWP-007": ["MAT-07"],
        "IWP-009": ["MAT-05"],
    }
    # IWP linked to schedule activities
    iwp_activity = {
        "IWP-001": "ACT-014", "IWP-002": "ACT-014", "IWP-005": "ACT-014",
        "IWP-010": "ACT-014",
        "IWP-003": "ACT-015", "IWP-004": "ACT-015",
        "IWP-006": "ACT-016",
        "IWP-007": "ACT-017",
        "IWP-008": "ACT-018", "IWP-009": "ACT-018",
    }

    for wp in awps + cwps + iwps:
        graph.add_vertex("WorkPackage", wp)
        graph.add_edge("BELONGS_TO", wp.id, project_id)

    for cwp_id, awp_id in cwp_awp.items():
        graph.add_edge("PARENT_OF", awp_id, cwp_id)
    for iwp_id, cwp_id in iwp_cwp.items():
        graph.add_edge("PARENT_OF", cwp_id, iwp_id)
    for iwp_id, mat_ids in iwp_materials.items():
        for mid in mat_ids:
            graph.add_edge("REQUIRES_MATERIAL", iwp_id, mid)
    for iwp_id, act_id in iwp_activity.items():
        graph.add_edge("PACKAGED_IN", act_id, iwp_id)
