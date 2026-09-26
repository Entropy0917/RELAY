"""FROZEN CONTRACT -- the seam between the backend and frontend tracks.

Every template receives exactly one of these as its context. Backend builds
them from the database; frontend designs against contracts/fixtures/*.json
through the preview harness. When the two meet, the route swaps
load_fixture() for build_viewmodel() and the template does not change.

RULES (planv0.2.md section 1):
  1. A fixture that does not validate against its model is a build error.
  2. Changes here require BOTH engineers. Propose freely; nobody edits alone.
  3. No engagement content in this file -- no names, no sectors (section 0.5).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import (
    FindingKind,
    KnowledgeType,
    RequirementKind,
    Role,
    SessionStage,
    Status,
    TransferState,
)

# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------


class PersonRef(BaseModel):
    id: str
    name: str
    title: str
    role: Role
    initials: str


class MetricTile(BaseModel):
    """A headline number. `formula` drives the 'how is this calculated' popover."""

    label: str
    value: str  # pre-formatted: "68%", "28 days", "4"
    caption: str | None = None
    delta: str | None = None  # "+2" / "-1"; None = no change indicator
    formula: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)


class CapabilityRow(BaseModel):
    capability_id: str
    capability: str
    level: int = Field(ge=0, le=6)
    level_label: str
    exposures: int
    last_demonstrated: str | None = None
    next_experience: str | None = None
    trainer_ready: bool = False


class RequirementRow(BaseModel):
    id: str
    kind: RequirementKind
    label: str
    description: str
    state: TransferState
    glyph: str


class RiskItem(BaseModel):
    severity: Status  # CRITICAL / AT_RISK / IN_PROGRESS
    title: str
    problem: str
    local_trainer: str | None = None
    recommended_action: str


class KnowledgeCard(BaseModel):
    id: str
    title: str
    type: KnowledgeType
    type_label: str
    area: str
    capability: str | None = None
    expert: str
    source_session: str | None = None
    validated: bool
    people_exposed: list[str] = Field(default_factory=list)
    summary: str


# ---------------------------------------------------------------------------
# Shell -- wraps every page
# ---------------------------------------------------------------------------


class NavItem(BaseModel):
    key: str
    label: str
    href: str
    active: bool = False


class EngagementRef(BaseModel):
    id: str
    name: str
    org: str


class ShellVM(BaseModel):
    """Always present. Proves multi-engagement support is real, not claimed."""

    nav: list[NavItem]
    engagements: list[EngagementRef]
    current_engagement: EngagementRef
    personas: list[PersonRef]
    current_persona: PersonRef


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


class OverviewVM(BaseModel):
    shell: ShellVM
    metrics: list[MetricTile]
    departing_expert: PersonRef | None = None
    days_until_departure: int | None = None
    risks: list[RiskItem]
    priority_actions: list[str]
    recent_knowledge: list[KnowledgeCard]
    trainer_progress: list[CapabilityRow]


class AreaCard(BaseModel):
    id: str
    name: str
    local_owner: PersonRef | None = None
    formal_pct: int = Field(ge=0, le=100)
    informal_pct: int = Field(ge=0, le=100)
    local_capability: str  # "Strong" / "Developing" / "Limited"
    trainer_coverage: bool
    status: Status
    status_label: str


class OperatingModelVM(BaseModel):
    shell: ShellVM
    mission: str
    areas: list[AreaCard]


class AreaDetailVM(BaseModel):
    """Drawer content. `dimensions` keys match vocabulary.OM_DIMENSIONS."""

    shell: ShellVM
    area: AreaCard
    dimensions: dict[str, list[str]]
    requirements: list[RequirementRow]
    capabilities: list[CapabilityRow]


class BlueprintAreaVM(BaseModel):
    area: AreaCard
    groups: dict[RequirementKind, list[RequirementRow]]
    local_capability: list[CapabilityRow]
    transfer_risk: Status


class BlueprintVM(BaseModel):
    shell: ShellVM
    areas: list[BlueprintAreaVM]


class PeopleVM(BaseModel):
    shell: ShellVM
    experts: list[PersonRef]
    counterparts: list[PersonRef]
    trainers: list[PersonRef]


class PassportVM(BaseModel):
    shell: ShellVM
    person: PersonRef
    capabilities: list[CapabilityRow]
    evidence_count: int
    knowledge_exposed: list[KnowledgeCard]


class KnowledgeVM(BaseModel):
    shell: ShellVM
    items: list[KnowledgeCard]
    counts_by_type: dict[KnowledgeType, int]
    active_filters: dict[str, str] = Field(default_factory=dict)


class PropagationNode(BaseModel):
    person: PersonRef
    taught_by: str | None = None
    children: list[str] = Field(default_factory=list)  # person ids


class ReadinessVM(BaseModel):
    shell: ShellVM
    metrics: list[MetricTile]
    areas: list[AreaCard]
    risks: list[RiskItem]
    before_departure: list[str]
    propagation: list[PropagationNode]
    propagation_capability: str | None = None


# ---------------------------------------------------------------------------
# Session loop
# ---------------------------------------------------------------------------


class SessionRef(BaseModel):
    id: str
    title: str
    date: str
    stage: SessionStage
    stage_label: str
    expert: PersonRef
    learners: list[PersonRef]
    capability_focus: str


class SessionListVM(BaseModel):
    shell: ShellVM
    upcoming: list[SessionRef]
    past: list[SessionRef]


class SessionBriefVM(BaseModel):
    """The 30-second briefing. Must stay short enough that an expert reads it."""

    primary_target: str
    current_level: str
    todays_objective: str
    your_role: str
    ask_before_explaining: str
    watch_for: list[str]
    knowledge_gap_to_explore: str


class DebriefQuestion(BaseModel):
    id: str
    question: str
    answer: str | None = None


class FindingVM(BaseModel):
    """One AI finding awaiting human validation.

    `ai_suggestion` and `validated_by` stay separate concepts -- the spec's
    AI-safety requirement. AI proposes; only a human validates.
    """

    id: str
    kind: FindingKind
    title: str
    body: dict[str, object]  # shape varies by kind; rendered per-kind
    confidence: str  # low / medium / high
    evidence_sources: list[str]
    rationale: str  # "why RELAY recommended this"
    impact: str  # which operating-model component this affects
    risk_if_untransferred: str
    validated_by: str | None = None
    validation_action: str | None = None


class SessionStageVM(BaseModel):
    shell: ShellVM
    session: SessionRef
    stage: SessionStage
    stages: list[dict[str, str]]  # stepper: key/label/state
    brief: SessionBriefVM | None = None
    transcript: str | None = None
    notes: str | None = None
    expert_questions: list[DebriefQuestion] = Field(default_factory=list)
    learner_questions: list[DebriefQuestion] = Field(default_factory=list)
    findings: list[FindingVM] = Field(default_factory=list)
    next_brief: SessionBriefVM | None = None
    can_act: bool = True  # False when the current persona is not the actor
    blocked_reason: str | None = None


# ---------------------------------------------------------------------------
# Partials returned by HTMX endpoints
# ---------------------------------------------------------------------------


class FindingPartialVM(BaseModel):
    finding: FindingVM


class CapabilityRowPartialVM(BaseModel):
    row: CapabilityRow
    person: PersonRef


class ErrorPartialVM(BaseModel):
    """Fail-loud policy: AI errors are DESIGNED, never a stack trace."""

    title: str
    detail: str
    retry_href: str | None = None
    kind: str  # provider_unreachable / schema_violation / timeout


VIEWMODELS: dict[str, type[BaseModel]] = {
    "overview": OverviewVM,
    "operating_model": OperatingModelVM,
    "area_detail": AreaDetailVM,
    "blueprint": BlueprintVM,
    "people": PeopleVM,
    "passport": PassportVM,
    "knowledge": KnowledgeVM,
    "readiness": ReadinessVM,
    "session_list": SessionListVM,
    "session_stage": SessionStageVM,
    "partial_finding": FindingPartialVM,
    "partial_capability_row": CapabilityRowPartialVM,
    "partial_error": ErrorPartialVM,
}
