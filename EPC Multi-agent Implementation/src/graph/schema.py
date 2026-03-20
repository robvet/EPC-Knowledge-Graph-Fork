"""Knowledge-graph schema definitions for the EPC Golden Triangle.

Vertex types, edge types, and their expected properties — used to bootstrap
the Cosmos DB Gremlin container and to validate data during ingestion.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


# ── Vertex Definitions ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class VertexType:
    label: str
    properties: List[str]
    source_system: str
    description: str


VERTEX_TYPES: Dict[str, VertexType] = {
    "Project": VertexType(
        label="Project",
        properties=["id", "name", "client", "status", "budget", "currency",
                     "location", "country", "industry", "start_date", "end_date"],
        source_system="All",
        description="Capital project or programme",
    ),
    "Phase": VertexType(
        label="Phase",
        properties=["id", "name", "phase_type", "status", "planned_start",
                     "planned_finish", "actual_start", "actual_finish"],
        source_system="Primavera P6",
        description="Lifecycle stage (Concept / FEED / Detail Design / Procurement / Construction / Commissioning)",
    ),
    "WBS": VertexType(
        label="WBS",
        properties=["id", "code", "name", "level", "parent_wbs_id"],
        source_system="Primavera P6",
        description="Work-breakdown-structure node",
    ),
    "Activity": VertexType(
        label="Activity",
        properties=["id", "name", "activity_type", "planned_start", "planned_finish",
                     "actual_start", "actual_finish", "duration_days", "total_float",
                     "pct_complete", "is_critical", "status"],
        source_system="Primavera P6",
        description="Scheduled activity / task",
    ),
    "Milestone": VertexType(
        label="Milestone",
        properties=["id", "name", "milestone_type", "planned_date",
                     "actual_date", "status"],
        source_system="Primavera P6",
        description="Gate / contractual / internal milestone",
    ),
    "Supplier": VertexType(
        label="Supplier",
        properties=["id", "name", "country", "category",
                     "qualification_status", "compliance_score",
                     "contact_email", "performance_rating"],
        source_system="SAP MM",
        description="Vendor or subcontractor",
    ),
    "PurchaseOrder": VertexType(
        label="PurchaseOrder",
        properties=["id", "po_number", "value", "currency", "status",
                     "issue_date", "promised_delivery_date", "actual_delivery_date",
                     "need_date", "description"],
        source_system="SAP MM",
        description="Procurement purchase order",
    ),
    "Material": VertexType(
        label="Material",
        properties=["id", "tag_number", "description", "specification",
                     "quantity", "unit", "delivery_status", "on_site"],
        source_system="SAP MM / SmartPlant",
        description="Bulk material or tagged item",
    ),
    "Document": VertexType(
        label="Document",
        properties=["id", "doc_number", "title", "revision", "discipline",
                     "doc_type", "status", "approval_status", "issue_date"],
        source_system="Aconex",
        description="Engineering drawing, specification or report",
    ),
    "WorkPackage": VertexType(
        label="WorkPackage",
        properties=["id", "wp_type", "name", "discipline", "status",
                     "constraints_clear", "planned_start", "crew_size",
                     "engineering_ready", "materials_ready",
                     "scaffolding_ready", "permits_ready"],
        source_system="O3 AWP",
        description="AWP / CWP / IWP work package",
    ),
    "Equipment": VertexType(
        label="Equipment",
        properties=["id", "tag_number", "description", "equipment_type",
                     "specification", "weight_kg", "install_status",
                     "manufacturer"],
        source_system="SmartPlant",
        description="Tagged equipment item (vessel, pump, HX, etc.)",
    ),
}


# ── Edge Definitions ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EdgeType:
    label: str
    from_vertex: str
    to_vertex: str
    properties: List[str] = field(default_factory=list)
    description: str = ""


EDGE_TYPES: Dict[str, EdgeType] = {
    "BELONGS_TO": EdgeType(
        label="BELONGS_TO",
        from_vertex="*",   # WBS | Activity | WorkPackage
        to_vertex="Project",
        description="Entity belongs to a project",
    ),
    "PARENT_OF": EdgeType(
        label="PARENT_OF",
        from_vertex="WBS",
        to_vertex="WBS",
        properties=["level"],
        description="WBS hierarchy",
    ),
    "IN_PHASE": EdgeType(
        label="IN_PHASE",
        from_vertex="Activity",
        to_vertex="Phase",
        description="Activity falls within a project phase",
    ),
    "DEPENDS_ON": EdgeType(
        label="DEPENDS_ON",
        from_vertex="Activity",
        to_vertex="Activity",
        properties=["dependency_type", "lag_days"],
        description="Schedule dependency (FS / FF / SS / SF)",
    ),
    "ACHIEVES": EdgeType(
        label="ACHIEVES",
        from_vertex="Activity",
        to_vertex="Milestone",
        description="Activity achieves / gates a milestone",
    ),
    "SUPPLIED_BY": EdgeType(
        label="SUPPLIED_BY",
        from_vertex="Material",
        to_vertex="Supplier",
        properties=["contract_id"],
        description="Material or equipment supplied by vendor",
    ),
    "ORDERED_VIA": EdgeType(
        label="ORDERED_VIA",
        from_vertex="Material",
        to_vertex="PurchaseOrder",
        properties=["line_item"],
        description="Material procured through a PO",
    ),
    "NEEDED_BY": EdgeType(
        label="NEEDED_BY",
        from_vertex="Material",
        to_vertex="Activity",
        properties=["need_date"],
        description="Material needed by a schedule activity",
    ),
    "PRODUCES": EdgeType(
        label="PRODUCES",
        from_vertex="Activity",
        to_vertex="Document",
        description="Activity produces an engineering deliverable",
    ),
    "REFERENCES": EdgeType(
        label="REFERENCES",
        from_vertex="Document",
        to_vertex="Equipment",
        description="Document references equipment",
    ),
    "PACKAGED_IN": EdgeType(
        label="PACKAGED_IN",
        from_vertex="Activity",
        to_vertex="WorkPackage",
        description="Activity is packaged into a work-package",
    ),
    "REQUIRES_MATERIAL": EdgeType(
        label="REQUIRES_MATERIAL",
        from_vertex="WorkPackage",
        to_vertex="Material",
        description="Work-package requires material to proceed",
    ),
    "CONTRACTED_WITH": EdgeType(
        label="CONTRACTED_WITH",
        from_vertex="Supplier",
        to_vertex="PurchaseOrder",
        description="Supplier contracted via purchase order",
    ),
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def all_vertex_labels() -> List[str]:
    return list(VERTEX_TYPES.keys())

def all_edge_labels() -> List[str]:
    return list(EDGE_TYPES.keys())
