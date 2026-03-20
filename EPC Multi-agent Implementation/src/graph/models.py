"""Pydantic v2 models for every vertex type in the EPC knowledge graph."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────────────

class ProjectStatus(str, Enum):
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class PhaseType(str, Enum):
    CONCEPT = "Concept"
    FEED = "FEED"
    DETAIL_DESIGN = "Detail Design"
    PROCUREMENT = "Procurement"
    CONSTRUCTION = "Construction"
    COMMISSIONING = "Commissioning"

class ActivityStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DELAYED = "Delayed"

class MilestoneType(str, Enum):
    GATE = "Gate"
    CONTRACTUAL = "Contractual"
    INTERNAL = "Internal"

class MilestoneStatus(str, Enum):
    PENDING = "Pending"
    ACHIEVED = "Achieved"
    AT_RISK = "At Risk"
    MISSED = "Missed"

class SupplierQualification(str, Enum):
    APPROVED = "Approved"
    CONDITIONAL = "Conditional"
    UNDER_REVIEW = "Under Review"
    DISQUALIFIED = "Disqualified"

class POStatus(str, Enum):
    DRAFT = "Draft"
    ISSUED = "Issued"
    ACKNOWLEDGED = "Acknowledged"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CLOSED = "Closed"

class DeliveryStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    ON_SITE = "On Site"

class DocApproval(str, Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    IFC = "Issued for Construction"
    SUPERSEDED = "Superseded"

class WPType(str, Enum):
    AWP = "AWP"
    CWP = "CWP"
    IWP = "IWP"

class WPStatus(str, Enum):
    PLANNED = "Planned"
    READY = "Ready"
    RELEASED = "Released"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"

class InstallStatus(str, Enum):
    NOT_INSTALLED = "Not Installed"
    IN_PROGRESS = "In Progress"
    INSTALLED = "Installed"
    COMMISSIONED = "Commissioned"

class DependencyType(str, Enum):
    FS = "Finish-to-Start"
    FF = "Finish-to-Finish"
    SS = "Start-to-Start"
    SF = "Start-to-Finish"

class Industry(str, Enum):
    CONVENTIONAL_ENERGY = "Conventional Energy"
    LOW_CARBON_ENERGY = "Low Carbon Energy"
    CHEMICALS_FUELS = "Chemicals & Fuels"
    RESOURCES = "Resources"


# ── Vertex Models ───────────────────────────────────────────────────────────

class Project(BaseModel):
    id: str
    name: str
    client: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    budget: float = 0.0
    currency: str = "USD"
    location: str = ""
    country: str = ""
    industry: Industry = Industry.CONVENTIONAL_ENERGY
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class Phase(BaseModel):
    id: str
    name: str
    phase_type: PhaseType
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None

class WBS(BaseModel):
    id: str
    code: str
    name: str
    level: int = 1
    parent_wbs_id: Optional[str] = None

class Activity(BaseModel):
    id: str
    name: str
    activity_type: str = "Task"
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None
    duration_days: int = 0
    total_float: int = 0
    pct_complete: float = Field(0.0, ge=0.0, le=100.0)
    is_critical: bool = False
    status: ActivityStatus = ActivityStatus.NOT_STARTED

class Milestone(BaseModel):
    id: str
    name: str
    milestone_type: MilestoneType = MilestoneType.INTERNAL
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: MilestoneStatus = MilestoneStatus.PENDING

class Supplier(BaseModel):
    id: str
    name: str
    country: str = ""
    category: str = ""
    qualification_status: SupplierQualification = SupplierQualification.APPROVED
    compliance_score: float = Field(100.0, ge=0.0, le=100.0)
    contact_email: str = ""
    performance_rating: float = Field(5.0, ge=0.0, le=5.0)

class PurchaseOrder(BaseModel):
    id: str
    po_number: str
    value: float = 0.0
    currency: str = "USD"
    status: POStatus = POStatus.DRAFT
    issue_date: Optional[date] = None
    promised_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    need_date: Optional[date] = None
    description: str = ""

class Material(BaseModel):
    id: str
    tag_number: str
    description: str = ""
    specification: str = ""
    quantity: float = 0.0
    unit: str = "EA"
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    on_site: bool = False

class Document(BaseModel):
    id: str
    doc_number: str
    title: str = ""
    revision: str = "A"
    discipline: str = ""
    doc_type: str = ""
    status: str = "Active"
    approval_status: DocApproval = DocApproval.DRAFT
    issue_date: Optional[date] = None

class WorkPackage(BaseModel):
    id: str
    wp_type: WPType
    name: str = ""
    discipline: str = ""
    status: WPStatus = WPStatus.PLANNED
    constraints_clear: bool = False
    planned_start: Optional[date] = None
    crew_size: int = 0
    engineering_ready: bool = False
    materials_ready: bool = False
    scaffolding_ready: bool = False
    permits_ready: bool = False

class Equipment(BaseModel):
    id: str
    tag_number: str
    description: str = ""
    equipment_type: str = ""
    specification: str = ""
    weight_kg: float = 0.0
    install_status: InstallStatus = InstallStatus.NOT_INSTALLED
    manufacturer: str = ""


# ── Edge Models ─────────────────────────────────────────────────────────────

class DependsOnEdge(BaseModel):
    from_id: str
    to_id: str
    dependency_type: DependencyType = DependencyType.FS
    lag_days: int = 0

class SuppliedByEdge(BaseModel):
    from_id: str
    to_id: str
    contract_id: str = ""

class OrderedViaEdge(BaseModel):
    from_id: str
    to_id: str
    line_item: int = 1

class NeededByEdge(BaseModel):
    from_id: str
    to_id: str
    need_date: Optional[date] = None

class SimpleEdge(BaseModel):
    """Generic edge with no extra properties."""
    from_id: str
    to_id: str
