from typing import Any, Dict, List

from src.api_models import SimulationCostImpactResponse, SimulationImpactResponse, SimulationResponse
from src.graph.client import get_graph
from src.graph import queries
from src.agents import log_activity
from src.agents.expanded_agents import LogisticsAgent, CostAgent, HSEAgent, ConstructionAgent, EngineeringAgent
from src.agents.scheduling import SchedulingAgent

def run_supply_chain_shock(project_id: str) -> Dict[str, Any]:
    """
    Simulates a major supply chain shock (e.g. Red Sea blockage).
    """
    log_activity("System", "🔮", "Started Simulation", "Running Scenario: Supply Chain Shock")
    
    # Initialize agents
    logistics = LogisticsAgent()
    scheduling = SchedulingAgent()
    cost = CostAgent()
    
    # 1. Logistics Agent identifies affected shipments
    log_activity(logistics.name, logistics.icon, "Scanning active shipments", "Checking for routes exposed to the shock...")
    affected_pos = ["PO-001", "PO-003", "PO-006"] # Mocking affected POs
    log_activity(logistics.name, logistics.icon, "Found affected shipments", f"Identified {len(affected_pos)} Purchase Orders facing a 4-week delay.", tool_calls=["identify_exposed_routes"])
    
    # 2. Add delay to graph (mocking the graph update for simulation)
    # In a real scenario, we would branch the graph or create "what-if" properties
    delay_days = 28
    impacted_activities = []
    
    # 3. Schedule Agent traces impact
    g = get_graph()
    log_activity(scheduling.name, scheduling.icon, "Tracing schedule impact", f"Analyzing cascading effects of a {delay_days}-day delay on {len(affected_pos)} POs...", tool_calls=["analyze_delay_impact"])
    
    # Use existing query to find cascade impact
    for po in affected_pos:
        impact = queries.get_delivery_cascade_impact(g, po)
        if impact and impact.get("affected_activities"):
            impacted_activities.extend(impact["affected_activities"])
            
    # Remove duplicates
    unique_impacted = {a["id"]: a for a in impacted_activities}.values()
    
    log_activity(scheduling.name, scheduling.icon, "Schedule impact calculated", f"The delay will push {len(unique_impacted)} construction activities onto the critical path. Mechanical Completion is delayed by 18 days.")

    # 4. Cost agent estimates commercial exposure
    log_activity(cost.name, cost.icon, "Estimating commercial impact", "Calculating schedule extension costs and liquidated damages exposure...", tool_calls=["calculate_commercial_exposure"])
    
    revenue_loss = 18 * 150000 # $150k per day LD
    overhead = 18 * 45000 # $45k daily overhead
    
    log_activity(cost.name, cost.icon, "Commercial analysis complete", f"Expected commercial exposure: ${revenue_loss + overhead:,.0f} ($ {revenue_loss:,.0f} LDs + ${overhead:,.0f} prolonged overhead overhead).")
    
    return SimulationResponse(
        scenario="Supply Chain Shock",
        description="A 4-week blockage on key shipping routes affecting current active POs.",
        affected_pos=affected_pos,
        schedule_impact=SimulationImpactResponse(
            critical_path_extended_days=18,
            new_critical_activities=len(unique_impacted),
            key_milestone_impacted="Mechanical Completion",
        ),
        cost_impact=SimulationCostImpactResponse(
            total_exposure=revenue_loss + overhead,
            liquidated_damages=revenue_loss,
            prolonged_overhead=overhead,
        ),
        narrative="A 4-week disruption in the shipping routes has halted the bulk transport of critical cryogenic equipment. Logistics analysis flags 3 major shipments delayed. The Schedule Agent warns this will exhaust the remaining float and push construction onto the critical path. The Cost Agent estimates a total of $3.5M in exposure due to extended overhead and liquidated damages.",
        recommendation="Expedite secondary suppliers for PO-001 and PO-003. Authorize air freight for critical valves to mitigate the 18-day slip.",
    ).model_dump()

def run_extreme_weather(project_id: str) -> Dict[str, Any]:
    """
    Simulates a Category 4 cyclone hitting the primary modular fabrication yard.
    """
    log_activity("System", "🔮", "Started Simulation", "Running Scenario: Extreme Weather Event")
    
    hse = HSEAgent()
    construction = ConstructionAgent()
    scheduling = SchedulingAgent()
    cost = CostAgent()
    
    # 1. HSE Agent assesses impact
    log_activity(hse.name, hse.icon, "Assessing weather impact", "Analyzing site readiness and damage forecasts for Category 4 cyclone...", tool_calls=["assess_weather_risk"])
    
    yard_downtime = 14
    
    # 2. Construction Agent evaluates modular yard
    log_activity(construction.name, construction.icon, "Evaluating yard damage", "Category 4 winds caused structural damage to the pipe rack fabrication bays.", tool_calls=["evaluate_yard_status"])
    
    # 3. Schedule impact
    log_activity(scheduling.name, scheduling.icon, "Tracing schedule impact", f"Analyzing effects of {yard_downtime}-day yard shutdown on downstream module installation...", tool_calls=["analyze_delay_impact"])
    
    # 4. Cost impact
    log_activity(cost.name, cost.icon, "Estimating commercial impact", "Calculating repair costs and schedule extension penalties...", tool_calls=["calculate_commercial_exposure"])
    
    repair_costs = 2500000
    ld_exposure = 14 * 150000
    
    return SimulationResponse(
        scenario="Extreme Weather Event",
        description="Simulate a Category 4 cyclone hitting the primary modular fabrication yard.",
        affected_pos=[],
        schedule_impact=SimulationImpactResponse(
            critical_path_extended_days=14,
            new_critical_activities=8,
            key_milestone_impacted="Mechanical Completion",
        ),
        cost_impact=SimulationCostImpactResponse(
            total_exposure=repair_costs + ld_exposure,
            liquidated_damages=ld_exposure,
            prolonged_overhead=repair_costs,
        ),
        narrative="A Category 4 cyclone has devastated the primary modular fabrication yard. The HSE Agent has enforced a mandatory 14-day shutdown for safety and damage assessment. The Construction Agent confirms structural damage to the pipe rack bays. The Schedule Agent forecasts a 14-day delay to the Mechanical Completion milestone, while the Cost Agent estimates $4.6M in damages and extended overhead.",
        recommendation="Activate emergency response workflows to secure the site. Divert critical path pipe rack fabrication to secondary yards in the region to recover schedule.",
    ).model_dump()

def run_labor_shortage(project_id: str) -> Dict[str, Any]:
    """
    Simulate only 60% mobilization of critical exotic-metal welders for the next quarter.
    """
    log_activity("System", "🔮", "Started Simulation", "Running Scenario: Labor Shortage")
    
    construction = ConstructionAgent()
    scheduling = SchedulingAgent()
    cost = CostAgent()
    
    # 1. Construction Agent identifies shortfall
    log_activity(construction.name, construction.icon, "Analyzing labor profiles", "Detected only 60% mobilization for exotic-metal welders (Super Duplex/Inconel)...", tool_calls=["analyze_resource_curves"])
    
    # 2. Schedule Agent traces impact
    log_activity(scheduling.name, scheduling.icon, "Tracing schedule impact", "Extrapolating welding duration extensions across critical path spools...", tool_calls=["analyze_productivity_impact"])
    
    # 3. Cost impact
    log_activity(cost.name, cost.icon, "Estimating commercial impact", "Calculating premium rates for expedited workforce mobilization...", tool_calls=["calculate_resource_costs"])
    
    premium_mobilization = 1800000
    ld_exposure = 12 * 150000
    
    return SimulationResponse(
        scenario="Labor Shortage",
        description="Simulate only 60% mobilization of critical exotic-metal welders for the next quarter.",
        affected_pos=[],
        schedule_impact=SimulationImpactResponse(
            critical_path_extended_days=12,
            new_critical_activities=15,
            key_milestone_impacted="Hydrotesting & Pre-Commissioning",
        ),
        cost_impact=SimulationCostImpactResponse(
            total_exposure=premium_mobilization + ld_exposure,
            liquidated_damages=ld_exposure,
            prolonged_overhead=premium_mobilization,
        ),
        narrative="A severe labor shortage has resulted in only 60% of required exotic-metal welders mobilizing for the next quarter. The Construction Agent identifies massive productivity bottlenecks for Super Duplex and Inconel welding. The Schedule Agent translates this shortfall into a 12-day critical path delay. The Cost Agent estimates a $3.6M impact to cover premium mobilization rates and potential schedule penalties.",
        recommendation="Authorize premium incentive pay (+40%) to attract specialized welders from competing regional megaprojects. Accelerate visa processing via the government relations liaison.",
    ).model_dump()

SIMULATIONS = {
    "supply_chain_shock": {
        "name": "Supply Chain Shock",
        "description": "Simulate a 4-week delay on major shipping routes.",
        "run": run_supply_chain_shock
    },
    "extreme_weather": {
        "name": "Extreme Weather Event",
        "description": "Simulate a Category 4 cyclone hitting the primary modular fabrication yard.",
        "run": run_extreme_weather
    },
    "labor_shortage": {
        "name": "Labor Shortage",
        "description": "Simulate only 60% mobilization of critical exotic-metal welders for the next quarter.",
        "run": run_labor_shortage
    }
}
