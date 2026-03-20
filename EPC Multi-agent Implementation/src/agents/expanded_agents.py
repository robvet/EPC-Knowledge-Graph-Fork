import json
from typing import Any, Dict, List, Optional
from src.agents import BaseAgent

# ═════════════════════════════════════════════════════════════════════════════
# 1. Construction / Site Execution Agent
# ═════════════════════════════════════════════════════════════════════════════
class ConstructionAgent(BaseAgent):
    """
    Monitors daily site progress, tool time, and crew productivity against the baseline.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Construction Agent"
        self.role = "Monitors site progress, tool time, and crew productivity."
        self.icon = "👷"
        self.mode = mode
        self.register_tool(self.get_crew_utilization, "Analyzes current site crew utilization and productivity vs plan.")

    def get_crew_utilization(self, project_id: str) -> Dict[str, Any]:
        """Analyzes current site crew utilization and productivity vs plan."""
        return {
            "status": "Analysis Complete",
            "findings": "Piping crew utilization at 68% due to scaffolding constraints at Area 3.",
            "recommendation": "Reallocate 2 piping crews to Area 4 where constraints are clear."
        }
        
    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.get_crew_utilization(context.get("project_id", "PRJ-001"))
        self.log_activity("Analyzed crew utilzation", tool_calls=["get_crew_utilization"])
        return {
            "agent": self.name,
            "response": "Based on current site execution data, piping crew utilization is lower than planned due to scaffolding constraints. I recommend reallocating crews to Area 4.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 2. Engineering & Design Agent
# ═════════════════════════════════════════════════════════════════════════════
class EngineeringAgent(BaseAgent):
    """
    Tracks 3D model progression, clash detection reports, and drawing approvals (IFC dates).
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Engineering Agent"
        self.role = "Tracks 3D model status, clash reports, and document approvals."
        self.icon = "📐"
        self.mode = mode
        self.register_tool(self.check_ifc_status, "Checks Issued for Construction (IFC) drawing status.")

    def check_ifc_status(self, subsystem: str) -> Dict[str, Any]:
        """Checks Issued for Construction (IFC) drawing status."""
        return {
            "subsystem": subsystem,
            "ifc_readiness": "85%",
            "blocking_issue": "Clash detection unresolved on Pipe Rack C.",
            "impact": "May delay Mechanical CWP-102."
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.check_ifc_status("Pipe Rack C")
        self.log_activity("Checked IFC drawing status", tool_calls=["check_ifc_status"])
        return {
            "agent": self.name,
            "response": "IFC drawings for Pipe Rack C are held up by an unresolved clash detection. This threatens Mechanical CWP-102.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 3. Logistics & Expediting Agent
# ═════════════════════════════════════════════════════════════════════════════
class LogisticsAgent(BaseAgent):
    """
    Tracks materials globally—from factory floor to port, customs, and last-mile delivery.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Logistics Agent"
        self.role = "Tracks shipments globally and monitors route congestion."
        self.icon = "🚢"
        self.mode = mode
        self.register_tool(self.track_shipment, "Tracks a shipment's location and estimated arrival.")

    def track_shipment(self, po_number: str) -> Dict[str, Any]:
        """Tracks a shipment's location and estimated arrival."""
        return {
            "po": po_number,
            "status": "In Transit - Delayed",
            "location": "Port of Singapore (Congestion)",
            "estimated_arrival": "+14 days",
            "action": "Expediting team notified to secure priority unloading."
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.track_shipment("PO-1234")
        self.log_activity("Tracked critical shipment", tool_calls=["track_shipment"])
        return {
            "agent": self.name,
            "response": "Shipment PO-1234 is delayed by 14 days due to congestion at the Port of Singapore.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 4. Cost & Commercial Agent
# ═════════════════════════════════════════════════════════════════════════════
class CostAgent(BaseAgent):
    """
    Manages Earned Value Management (EVM), cash flow, and cost variances (CPI/SPI).
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Cost Agent"
        self.role = "Manages EVM, cash flow, and cost variances."
        self.icon = "💰"
        self.mode = mode
        self.register_tool(self.calculate_evm, "Calculates Earned Value metrics for the project.")

    def calculate_evm(self, project_id: str) -> Dict[str, Any]:
        """Calculates Earned Value metrics for the project."""
        return {
            "SPI": 0.94,
            "CPI": 0.98,
            "variance_at_completion": "-$1.2M",
            "driver": "Higher than expected scaffolding costs in Phase 2."
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.calculate_evm(context.get("project_id", "PRJ-001"))
        self.log_activity("Calculated EVM metrics", tool_calls=["calculate_evm"])
        return {
            "agent": self.name,
            "response": "The project is currently running at an SPI of 0.94 and a CPI of 0.98. Higher scaffolding costs are driving the variance.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 5. HSE (Health, Safety & Environment) Agent
# ═════════════════════════════════════════════════════════════════════════════
class HSEAgent(BaseAgent):
    """
    Monitors site safety compliance, weather forecasts, and permit-to-work statuses.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "HSE Agent"
        self.role = "Monitors safety compliance, weather, and permits."
        self.icon = "🛡️"
        self.mode = mode
        self.register_tool(self.check_weather_risk, "Checks weather forecasts against active high-risk IWPs.")

    def check_weather_risk(self, location: str) -> Dict[str, Any]:
        """Checks weather forecasts against active high-risk IWPs."""
        return {
            "alert_level": "High",
            "forecast": "Gale-force winds (>40 knots) expected in 48 hours.",
            "impact": "All heavy lifting operations exceeding 50 tons must be suspended.",
            "affected_iwps": ["IWP-Lift-001", "IWP-Lift-002"]
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.check_weather_risk("Site")
        self.log_activity("Checked weather risk", tool_calls=["check_weather_risk"])
        return {
            "agent": self.name,
            "response": "Warning: Gale-force winds are expected in 48 hours. Recommend suspending heavy lifting IWPs.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 6. Quality Assurance (QA/QC) Agent
# ═════════════════════════════════════════════════════════════════════════════
class QAAgent(BaseAgent):
    """
    Tracks Non-Conformance Reports (NCRs), inspection test plans (ITPs), and welding pass rates.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "QA/QC Agent"
        self.role = "Tracks NCRs, inspections, and quality metrics."
        self.icon = "🛑"
        self.mode = mode
        self.register_tool(self.get_ncr_status, "Retrieves active Non-Conformance Reports severity.")

    def get_ncr_status(self) -> Dict[str, Any]:
        """Retrieves active Non-Conformance Reports severity."""
        return {
            "open_ncrs": 12,
            "critical": 1,
            "critical_details": "Weld failure on main cryogenic line. Requires re-work.",
            "impacted_system": "System 14 - Liquefaction"
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.get_ncr_status()
        self.log_activity("Checked NCR status", tool_calls=["get_ncr_status"])
        return {
            "agent": self.name,
            "response": "There are 12 open NCRs. One is critical involving a weld failure on the main cryogenic line.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 7. Contracts & Claims Agent
# ═════════════════════════════════════════════════════════════════════════════
class ContractsAgent(BaseAgent):
    """
    Analyzes commercial exposure, liquidated damages, and builds defensible claim data.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Contracts Agent"
        self.role = "Analyzes commercial exposure and claims."
        self.icon = "⚖️"
        self.mode = mode
        self.register_tool(self.analyze_commercial_exposure, "Analyzes exposure to liquidated damages.")

    def analyze_commercial_exposure(self, milestone: str) -> Dict[str, Any]:
        """Analyzes exposure to liquidated damages."""
        return {
            "milestone": milestone,
            "contractual_date": "2024-12-15",
            "forecast_date": "2024-12-30",
            "liquidated_damages_exposure": "$1,500,000",
            "mitigation_plan": "Prepare Extension of Time (EoT) claim based on late client engineering approvals."
        }

    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.analyze_commercial_exposure("Mechanical Completion")
        self.log_activity("Analyzed commercial exposure", tool_calls=["analyze_commercial_exposure"])
        return {
            "agent": self.name,
            "response": "We are currently exposed to $1.5M in liquidated damages due to a 15-day forecast slip on Mechanical Completion. Compiling an EoT claim based on engineering delays.",
            "data": tool_res
        }


# ═════════════════════════════════════════════════════════════════════════════
# 8. Commissioning & Start-up Agent
# ═════════════════════════════════════════════════════════════════════════════
class CommissioningAgent(BaseAgent):
    """
    Manages system turnover packages, loop checks, and punch-list burn-down.
    """
    def __init__(self, mode: str = "mock"):
        super().__init__()
        self.name = "Commissioning Agent"
        self.role = "Manages system turnover and punch-lists."
        self.icon = "🔌"
        self.mode = mode
        self.register_tool(self.check_turnover_readiness, "Checks readiness of systems for commissioning turnover.")

    def check_turnover_readiness(self, system: str) -> Dict[str, Any]:
        """Checks readiness of systems for commissioning turnover."""
        return {
            "system": system,
            "status": "Not Ready",
            "punch_items": 42,
            "category_A_punch": 3,
            "blocking_issue": "Instrument loop checks pending for 3 pressure transmitters."
        }
        
    async def process_query_mock(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        self.log_activity("Processing query: " + query)
        tool_res = self.check_turnover_readiness("System 14")
        self.log_activity("Checked turnover readiness", tool_calls=["check_turnover_readiness"])
        return {
            "agent": self.name,
            "response": "System 14 is not ready for turnover. There are 3 Category A punch items remaining, blocked by pending instrument loop checks.",
            "data": tool_res
        }
