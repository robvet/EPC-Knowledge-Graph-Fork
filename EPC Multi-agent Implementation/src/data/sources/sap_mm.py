"""SAP MM — procurement & material data source.

Generates suppliers, purchase orders and materials for the LNG project.
Includes some POs that deliberately slip past need dates to trigger agent alerts.
"""

from __future__ import annotations

from datetime import date, timedelta
from src.graph.client import GraphClient
from src.graph.models import (
    DeliveryStatus, Material, POStatus, PurchaseOrder,
    Supplier, SupplierQualification,
)


def _d(base: date, offset: int) -> date:
    return base + timedelta(days=offset)


def ingest(graph: GraphClient, project_id: str = "PRJ-001") -> None:
    base = date(2025, 1, 15)

    # ── Suppliers ────────────────────────────────────────────────────
    suppliers = [
        Supplier(id="SUP-01", name="Arabian Heavy Industries", country="Saudi Arabia",
                 category="Pressure Vessels", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=92, performance_rating=4.5),
        Supplier(id="SUP-02", name="TechnipFMC Valve Division", country="France",
                 category="Valves & Actuators", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=95, performance_rating=4.8),
        Supplier(id="SUP-03", name="Hyundai Heavy Industries", country="South Korea",
                 category="Heat Exchangers", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=88, performance_rating=4.2),
        Supplier(id="SUP-04", name="Sulzer Pumps", country="Switzerland",
                 category="Rotating Equipment", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=96, performance_rating=4.7),
        Supplier(id="SUP-05", name="Yokogawa Electric", country="Japan",
                 category="Instrumentation & Control", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=97, performance_rating=4.9),
        Supplier(id="SUP-06", name="Pacific Steel Corp", country="China",
                 category="Structural Steel", qualification_status=SupplierQualification.CONDITIONAL,
                 compliance_score=72, performance_rating=3.5),
        Supplier(id="SUP-07", name="Gulf Piping LLC", country="UAE",
                 category="Piping & Fittings", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=85, performance_rating=4.0),
        Supplier(id="SUP-08", name="Consolidated Cables Inc", country="USA",
                 category="Electrical / Cables", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=90, performance_rating=4.3),
        Supplier(id="SUP-09", name="Delta Insulation Works", country="India",
                 category="Insulation & Fireproofing", qualification_status=SupplierQualification.UNDER_REVIEW,
                 compliance_score=64, performance_rating=3.1),
        Supplier(id="SUP-10", name="Atlas Fabrication Group", country="Turkey",
                 category="Modular Fabrication", qualification_status=SupplierQualification.APPROVED,
                 compliance_score=83, performance_rating=3.9),
    ]
    for s in suppliers:
        graph.add_vertex("Supplier", s)

    # ── Purchase Orders ──────────────────────────────────────────────
    purchase_orders = [
        PurchaseOrder(id="PO-001", po_number="4500001", value=2_800_000, currency="USD",
                      status=POStatus.SHIPPED, description="LNG Cryogenic Heat Exchanger",
                      issue_date=_d(base, 220), promised_delivery_date=_d(base, 380),
                      need_date=_d(base, 370)),
        PurchaseOrder(id="PO-002", po_number="4500002", value=1_500_000, currency="USD",
                      status=POStatus.ACKNOWLEDGED, description="Cryogenic Valves Package",
                      issue_date=_d(base, 230), promised_delivery_date=_d(base, 390),
                      need_date=_d(base, 360)),  # ⚠️ SLIPPING: delivery 30 days late
        PurchaseOrder(id="PO-003", po_number="4500003", value=3_200_000, currency="USD",
                      status=POStatus.SHIPPED, description="LNG Storage Vessel V-101",
                      issue_date=_d(base, 215), promised_delivery_date=_d(base, 375),
                      need_date=_d(base, 365)),
        PurchaseOrder(id="PO-004", po_number="4500004", value=950_000, currency="USD",
                      status=POStatus.ACKNOWLEDGED, description="Centrifugal Compressor Package",
                      issue_date=_d(base, 240), promised_delivery_date=_d(base, 420),
                      need_date=_d(base, 390)),  # ⚠️ SLIPPING: 30 days late
        PurchaseOrder(id="PO-005", po_number="4500005", value=680_000, currency="USD",
                      status=POStatus.ISSUED, description="DCS & SIS System",
                      issue_date=_d(base, 250), promised_delivery_date=_d(base, 400),
                      need_date=_d(base, 410)),
        PurchaseOrder(id="PO-006", po_number="4500006", value=420_000, currency="USD",
                      status=POStatus.SHIPPED, description="Structural Steel Package",
                      issue_date=_d(base, 260), promised_delivery_date=_d(base, 355),
                      need_date=_d(base, 340)),
        PurchaseOrder(id="PO-007", po_number="4500007", value=350_000, currency="USD",
                      status=POStatus.ACKNOWLEDGED, description="Piping Spools — SS316",
                      issue_date=_d(base, 270), promised_delivery_date=_d(base, 395),
                      need_date=_d(base, 380)),
        PurchaseOrder(id="PO-008", po_number="4500008", value=180_000, currency="USD",
                      status=POStatus.DELIVERED, description="Electrical Cable Package",
                      issue_date=_d(base, 240), promised_delivery_date=_d(base, 340),
                      actual_delivery_date=_d(base, 335), need_date=_d(base, 350)),
        PurchaseOrder(id="PO-009", po_number="4500009", value=120_000, currency="USD",
                      status=POStatus.ISSUED, description="Insulation Materials",
                      issue_date=_d(base, 290), promised_delivery_date=_d(base, 430),
                      need_date=_d(base, 420)),
        PurchaseOrder(id="PO-010", po_number="4500010", value=1_100_000, currency="USD",
                      status=POStatus.ACKNOWLEDGED, description="Pipe Rack Modules — Prefab",
                      issue_date=_d(base, 255), promised_delivery_date=_d(base, 400),
                      need_date=_d(base, 385)),
    ]
    po_supplier = {
        "PO-001": "SUP-03", "PO-002": "SUP-02", "PO-003": "SUP-01",
        "PO-004": "SUP-04", "PO-005": "SUP-05", "PO-006": "SUP-06",
        "PO-007": "SUP-07", "PO-008": "SUP-08", "PO-009": "SUP-09",
        "PO-010": "SUP-10",
    }
    for po in purchase_orders:
        graph.add_vertex("PurchaseOrder", po)
        graph.add_edge("BELONGS_TO", po.id, project_id)
        supp_id = po_supplier.get(po.id)
        if supp_id:
            graph.add_edge("CONTRACTED_WITH", supp_id, po.id)

    # ── Materials ────────────────────────────────────────────────────
    materials = [
        Material(id="MAT-01", tag_number="HX-101", description="LNG Cryogenic Heat Exchanger",
                 specification="ASME VIII Div 1", quantity=1, unit="EA",
                 delivery_status=DeliveryStatus.IN_TRANSIT),
        Material(id="MAT-02", tag_number="VLV-PKG-01", description="Cryogenic Valve Package (24 pcs)",
                 specification="API 608", quantity=24, unit="EA",
                 delivery_status=DeliveryStatus.PENDING),
        Material(id="MAT-03", tag_number="V-101", description="LNG Storage Vessel",
                 specification="ASME VIII Div 2", quantity=1, unit="EA",
                 delivery_status=DeliveryStatus.IN_TRANSIT),
        Material(id="MAT-04", tag_number="C-101", description="Centrifugal Compressor",
                 specification="API 617", quantity=1, unit="EA",
                 delivery_status=DeliveryStatus.PENDING),
        Material(id="MAT-05", tag_number="DCS-SYS", description="DCS & SIS Control System",
                 specification="IEC 61511", quantity=1, unit="LOT",
                 delivery_status=DeliveryStatus.PENDING),
        Material(id="MAT-06", tag_number="STL-PKG-01", description="Structural Steel Package",
                 specification="AISC 360", quantity=450, unit="TON",
                 delivery_status=DeliveryStatus.IN_TRANSIT),
        Material(id="MAT-07", tag_number="PIPE-SS316", description="Piping Spools SS316",
                 specification="ASME B31.3", quantity=2800, unit="LM",
                 delivery_status=DeliveryStatus.PENDING),
        Material(id="MAT-08", tag_number="CBL-PKG-01", description="Electrical Cable Package",
                 specification="IEC 60502", quantity=15000, unit="LM",
                 delivery_status=DeliveryStatus.ON_SITE, on_site=True),
        Material(id="MAT-09", tag_number="INS-PKG-01", description="Insulation Material Package",
                 specification="ASTM C547", quantity=3200, unit="SQM",
                 delivery_status=DeliveryStatus.PENDING),
        Material(id="MAT-10", tag_number="MOD-PR-01", description="Pipe Rack Modules — Prefabricated",
                 specification="Project Spec PR-001", quantity=6, unit="EA",
                 delivery_status=DeliveryStatus.PENDING),
    ]
    mat_po = {
        "MAT-01": "PO-001", "MAT-02": "PO-002", "MAT-03": "PO-003",
        "MAT-04": "PO-004", "MAT-05": "PO-005", "MAT-06": "PO-006",
        "MAT-07": "PO-007", "MAT-08": "PO-008", "MAT-09": "PO-009",
        "MAT-10": "PO-010",
    }
    mat_supplier = {
        "MAT-01": "SUP-03", "MAT-02": "SUP-02", "MAT-03": "SUP-01",
        "MAT-04": "SUP-04", "MAT-05": "SUP-05", "MAT-06": "SUP-06",
        "MAT-07": "SUP-07", "MAT-08": "SUP-08", "MAT-09": "SUP-09",
        "MAT-10": "SUP-10",
    }
    # Materials needed by construction activities
    mat_activity_need = {
        "MAT-01": ("ACT-016", _d(base, 400)),  # Equipment Installation
        "MAT-02": ("ACT-017", _d(base, 410)),  # Piping Installation
        "MAT-03": ("ACT-016", _d(base, 395)),  # Equipment Installation
        "MAT-04": ("ACT-016", _d(base, 405)),  # Equipment Installation
        "MAT-05": ("ACT-018", _d(base, 430)),  # E&I Installation
        "MAT-06": ("ACT-015", _d(base, 370)),  # Steel Erection
        "MAT-07": ("ACT-017", _d(base, 415)),  # Piping Installation
        "MAT-08": ("ACT-018", _d(base, 435)),  # E&I Installation
        "MAT-09": ("ACT-017", _d(base, 480)),  # late stage piping
        "MAT-10": ("ACT-015", _d(base, 375)),  # Steel Erection
    }
    for m in materials:
        graph.add_vertex("Material", m)
        if m.id in mat_po:
            graph.add_edge("ORDERED_VIA", m.id, mat_po[m.id], line_item=1)
        if m.id in mat_supplier:
            graph.add_edge("SUPPLIED_BY", m.id, mat_supplier[m.id])
        if m.id in mat_activity_need:
            act_id, need_dt = mat_activity_need[m.id]
            graph.add_edge("NEEDED_BY", m.id, act_id,
                           need_date=need_dt.isoformat())
