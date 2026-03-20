"""Pydantic models for FastAPI request and response validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentActivityResponse(BaseModel):
    id: str
    agent_name: str
    agent_icon: str
    action: str
    detail: str
    timestamp: str
    entities: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)


class DashboardScheduleResponse(BaseModel):
    total_activities: int
    completed: int
    in_progress: int
    avg_pct_complete: float
    critical_path_count: int


class ProcurementSlipResponse(BaseModel):
    material_id: str
    material_tag: str
    description: str
    po_number: str
    need_date: str
    delivery_date: str
    slip_days: int


class DashboardProcurementResponse(BaseModel):
    total_pos: int
    open_pos: int
    material_slips: int
    top_slips: list[ProcurementSlipResponse] = Field(default_factory=list)


class DashboardWorkPackagesResponse(BaseModel):
    iwp_ready: int
    iwp_blocked: int
    total_iwps: int


class DashboardMilestonesResponse(BaseModel):
    total: int
    at_risk: int
    achieved: int


class DashboardResponse(BaseModel):
    schedule: DashboardScheduleResponse
    procurement: DashboardProcurementResponse
    work_packages: DashboardWorkPackagesResponse
    milestones: DashboardMilestonesResponse


class ActivityResponse(BaseModel):
    id: str
    name: str
    activity_type: str | None = None
    planned_start: str | None = None
    planned_finish: str | None = None
    actual_start: str | None = None
    actual_finish: str | None = None
    duration_days: int | None = None
    total_float: int | None = None
    pct_complete: float | None = None
    is_critical: bool | None = None
    status: str | None = None
    expected_pct: float | None = None
    variance: float | None = None

    model_config = ConfigDict(extra='allow')


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str | None = None
    value: float | None = None
    currency: str | None = None
    status: str | None = None
    issue_date: str | None = None
    promised_delivery_date: str | None = None
    actual_delivery_date: str | None = None
    need_date: str | None = None
    description: str | None = None

    model_config = ConfigDict(extra='allow')


class SupplierRiskProfileResponse(BaseModel):
    id: str
    name: str
    country: str | None = None
    category: str | None = None
    qualification_status: str | None = None
    compliance_score: float | None = None
    contact_email: str | None = None
    performance_rating: float | None = None
    open_po_count: int
    total_po_count: int
    risk_level: str

    model_config = ConfigDict(extra='allow')


class ConstraintSetResponse(BaseModel):
    engineering_ready: bool
    materials_ready: bool
    scaffolding_ready: bool
    permits_ready: bool


class WorkPackageConstraintStatusResponse(BaseModel):
    id: str
    name: str
    discipline: str
    status: str
    constraints: ConstraintSetResponse
    constraints_clear: bool


class IWPConstraintStatusResponse(BaseModel):
    ready: list[WorkPackageConstraintStatusResponse] = Field(default_factory=list)
    blocked: list[WorkPackageConstraintStatusResponse] = Field(default_factory=list)


class MilestoneResponse(BaseModel):
    id: str
    name: str
    milestone_type: str | None = None
    planned_date: str | None = None
    actual_date: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra='allow')


class MaterialResponse(BaseModel):
    id: str
    tag_number: str | None = None
    description: str | None = None
    specification: str | None = None
    quantity: float | None = None
    unit: str | None = None
    delivery_status: str | None = None
    on_site: bool | None = None

    model_config = ConfigDict(extra='allow')


class DeliveryCascadeImpactResponse(BaseModel):
    po: PurchaseOrderResponse
    affected_materials: list[MaterialResponse] = Field(default_factory=list)
    affected_activities: list[ActivityResponse] = Field(default_factory=list)
    affected_milestones: list[MilestoneResponse] = Field(default_factory=list)
    impact_summary: str


class DeliveryCascadeSummaryResponse(BaseModel):
    material: str
    po: str
    slip_days: int
    impact: dict[str, Any] = Field(default_factory=dict)


class ConstraintBlockerResponse(BaseModel):
    iwp: str
    discipline: str
    blocked_by: list[str] = Field(default_factory=list)


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    is_critical: bool = False


class GraphLinkResponse(BaseModel):
    source: str
    target: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNodeResponse] = Field(default_factory=list)
    links: list[GraphLinkResponse] = Field(default_factory=list)


class AgentQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AgentQueryResponse(BaseModel):
    orchestrator: str | None = None
    routed_to: str | None = None
    agent: str
    response: str
    data: Any = None

    model_config = ConfigDict(extra='allow')


class WorkflowDefinitionResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str


class WorkflowListResponse(BaseModel):
    autonomous: list[WorkflowDefinitionResponse] = Field(default_factory=list)
    hitl: list[WorkflowDefinitionResponse] = Field(default_factory=list)


class HITLItemResponse(BaseModel):
    id: str
    title: str
    workflow_name: str
    requesting_agent: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    impact: str = ''
    status: str
    created_at: str
    resolved_at: str | None = None
    resolved_by: str | None = None
    rejection_reason: str | None = None


class HITLQueueResponse(BaseModel):
    pending: list[HITLItemResponse] = Field(default_factory=list)
    resolved: list[HITLItemResponse] = Field(default_factory=list)


class HITLItemsCreatedResponse(BaseModel):
    items_created: int
    items: list[HITLItemResponse] = Field(default_factory=list)


class WorkflowRunResponse(BaseModel):
    workflow: str | None = None
    status: str | None = None
    result: str | None = None
    steps_completed: int | None = None
    items_created: int | None = None
    items: list[HITLItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='allow')


class ProcurementDelayCascadeWorkflowResponse(WorkflowRunResponse):
    total_material_slips: int | None = None
    cascades_analyzed: int | None = None
    affected_milestones: int | None = None
    cascade_details: list[DeliveryCascadeSummaryResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ScheduleVarianceWorkflowResponse(WorkflowRunResponse):
    activities_behind: int | None = None
    low_float_activities: int | None = None
    variance_details: list[ActivityResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DocumentReadinessWorkflowResponse(WorkflowRunResponse):
    iwps_ready: int | None = None
    iwps_blocked: int | None = None
    ready_for_release: list[str] = Field(default_factory=list)
    blockers: list[ConstraintBlockerResponse] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    project_id: str = Field(default='PRJ-001', min_length=1)


class SimulationImpactResponse(BaseModel):
    critical_path_extended_days: int
    new_critical_activities: int
    key_milestone_impacted: str


class SimulationCostImpactResponse(BaseModel):
    total_exposure: float
    liquidated_damages: float
    prolonged_overhead: float


class SimulationResponse(BaseModel):
    scenario: str
    description: str
    affected_pos: list[str] = Field(default_factory=list)
    schedule_impact: SimulationImpactResponse
    cost_impact: SimulationCostImpactResponse
    narrative: str
    recommendation: str

    model_config = ConfigDict(extra='allow')


class RejectRequest(BaseModel):
    reason: str = Field(default='', max_length=2000)