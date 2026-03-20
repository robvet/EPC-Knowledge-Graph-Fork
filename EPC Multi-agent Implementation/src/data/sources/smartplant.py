"""SmartPlant — engineering / equipment data source."""

from __future__ import annotations
from src.graph.client import GraphClient
from src.graph.models import Equipment, InstallStatus


def ingest(graph: GraphClient, project_id: str = "PRJ-001") -> None:
    equipment = [
        Equipment(id="EQP-01", tag_number="V-101", description="LNG Storage Vessel",
                  equipment_type="Pressure Vessel", specification="ASME VIII Div 2",
                  weight_kg=185_000, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Arabian Heavy Industries"),
        Equipment(id="EQP-02", tag_number="HX-101", description="Cryogenic MCHE",
                  equipment_type="Heat Exchanger", specification="ASME VIII Div 1",
                  weight_kg=92_000, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Hyundai Heavy Industries"),
        Equipment(id="EQP-03", tag_number="C-101", description="Refrigerant Compressor",
                  equipment_type="Compressor", specification="API 617",
                  weight_kg=28_000, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Sulzer Pumps"),
        Equipment(id="EQP-04", tag_number="P-101A", description="Feed Pump A",
                  equipment_type="Centrifugal Pump", specification="API 610",
                  weight_kg=3_200, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Sulzer Pumps"),
        Equipment(id="EQP-05", tag_number="P-101B", description="Feed Pump B (Spare)",
                  equipment_type="Centrifugal Pump", specification="API 610",
                  weight_kg=3_200, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Sulzer Pumps"),
        Equipment(id="EQP-06", tag_number="FV-1001", description="Feed Control Valve",
                  equipment_type="Control Valve", specification="API 608",
                  weight_kg=450, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="TechnipFMC Valve Division"),
        Equipment(id="EQP-07", tag_number="DCS-001", description="DCS Main Cabinet",
                  equipment_type="DCS", specification="IEC 61511",
                  weight_kg=1_500, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Yokogawa Electric"),
        Equipment(id="EQP-08", tag_number="SIS-001", description="SIS Logic Solver",
                  equipment_type="SIS", specification="IEC 61511 SIL3",
                  weight_kg=800, install_status=InstallStatus.NOT_INSTALLED,
                  manufacturer="Yokogawa Electric"),
    ]
    equip_supplier = {
        "EQP-01": "SUP-01", "EQP-02": "SUP-03", "EQP-03": "SUP-04",
        "EQP-04": "SUP-04", "EQP-05": "SUP-04", "EQP-06": "SUP-02",
        "EQP-07": "SUP-05", "EQP-08": "SUP-05",
    }
    for eq in equipment:
        graph.add_vertex("Equipment", eq)
        graph.add_edge("BELONGS_TO", eq.id, project_id)
        if eq.id in equip_supplier:
            graph.add_edge("SUPPLIED_BY", eq.id, equip_supplier[eq.id])
