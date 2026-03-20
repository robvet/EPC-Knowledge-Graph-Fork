"""Aconex — document management data source."""

from __future__ import annotations
from datetime import date, timedelta
from src.graph.client import GraphClient
from src.graph.models import DocApproval, Document


def _d(base: date, offset: int) -> date:
    return base + timedelta(days=offset)


def ingest(graph: GraphClient, project_id: str = "PRJ-001") -> None:
    base = date(2025, 1, 15)

    documents = [
        Document(id="DOC-001", doc_number="PID-001", title="P&ID — LNG Main Process",
                 revision="C", discipline="Process", doc_type="P&ID",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 160)),
        Document(id="DOC-002", doc_number="PID-002", title="P&ID — Utilities & Flare",
                 revision="B", discipline="Process", doc_type="P&ID",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 170)),
        Document(id="DOC-003", doc_number="DS-V101", title="Datasheet — LNG Storage Vessel V-101",
                 revision="B", discipline="Mechanical", doc_type="Datasheet",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 175)),
        Document(id="DOC-004", doc_number="DS-HX101", title="Datasheet — Cryogenic Heat Exchanger HX-101",
                 revision="A", discipline="Mechanical", doc_type="Datasheet",
                 approval_status=DocApproval.APPROVED, issue_date=_d(base, 180)),
        Document(id="DOC-005", doc_number="ISO-001", title="Piping Isometric — Main Header",
                 revision="A", discipline="Piping", doc_type="Isometric",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 200)),
        Document(id="DOC-006", doc_number="GA-STR-01", title="General Arrangement — Structural Steel",
                 revision="B", discipline="Structural", doc_type="GA Drawing",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 190)),
        Document(id="DOC-007", doc_number="SLD-001", title="Single Line Diagram — Main Power",
                 revision="A", discipline="Electrical", doc_type="SLD",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 210)),
        Document(id="DOC-008", doc_number="INST-HK-01", title="Instrument Hook-Up Typical",
                 revision="B", discipline="Instrumentation", doc_type="Hook-Up",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 220)),
        Document(id="DOC-009", doc_number="HAZOP-RPT", title="HAZOP Study Report",
                 revision="A", discipline="Process Safety", doc_type="Report",
                 approval_status=DocApproval.APPROVED, issue_date=_d(base, 80)),
        Document(id="DOC-010", doc_number="SP-PIPE-01", title="Piping Material Specification",
                 revision="C", discipline="Piping", doc_type="Specification",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 165)),
        Document(id="DOC-011", doc_number="PFD-001", title="Process Flow Diagram — LNG Train",
                 revision="B", discipline="Process", doc_type="PFD",
                 approval_status=DocApproval.IFC, issue_date=_d(base, 50)),
        Document(id="DOC-012", doc_number="CIVIL-FDN-01", title="Foundation Layout — Equipment Area",
                 revision="A", discipline="Civil", doc_type="Layout Drawing",
                 approval_status=DocApproval.IN_REVIEW, issue_date=_d(base, 310)),
    ]
    # Which activities produce which documents
    doc_activity = {
        "DOC-001": "ACT-004", "DOC-002": "ACT-004", "DOC-003": "ACT-005",
        "DOC-004": "ACT-005", "DOC-005": "ACT-006", "DOC-006": "ACT-006",
        "DOC-007": "ACT-007", "DOC-008": "ACT-007", "DOC-009": "ACT-002",
        "DOC-010": "ACT-004", "DOC-011": "ACT-001", "DOC-012": "ACT-014",
    }
    # Which documents reference which equipment
    doc_equip = {
        "DOC-003": "EQP-01",  # V-101
        "DOC-004": "EQP-02",  # HX-101
    }
    for doc in documents:
        graph.add_vertex("Document", doc)
        graph.add_edge("BELONGS_TO", doc.id, project_id)
        if doc.id in doc_activity:
            graph.add_edge("PRODUCES", doc_activity[doc.id], doc.id)
        if doc.id in doc_equip:
            graph.add_edge("REFERENCES", doc.id, doc_equip[doc.id])
