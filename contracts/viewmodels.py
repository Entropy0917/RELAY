"""Frozen view-model contract (planv0.2 §1).

One Pydantic model per page and per HTMX partial. Each model IS the template's
context: the backend's `build_viewmodel()` returns it, the frontend's preview
harness loads it from `contracts/fixtures/<name>.json`. Neither side edits this
file alone.

Conventions
- Every page model has `shell: Shell`. Partials do not.
- Every number shown to a user that is a score is a `Metric` (value + formula +
  inputs), so the UI can always explain it.
- `href` fields are complete URLs built server-side; templates never build URLs.
- Dates are ISO `date`; display formatting is the template's job.
- No engagement content in this file (§0.5). Labels for product vocabulary come
  from `contracts.vocab`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from contracts.vocab import (
    AIErrorKind,
    CapabilityLevel,
    Confidence,
    DebriefRole,
    EvidenceType,
    FindingAction,
    FindingKind,
    FindingStatus,
    KnowledgeType,
    LocalCapability,
    LearnerResultTag,
    OMDimension,
    PersonaRole,
    PersonKind,
    RequirementCategory,
    SessionStage,
    Severity,
    Status,
    StepState,
    TransferRail,
    TransferState,
    ValidationStatus,
)


class VM(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ─────────────────────────── shared building blocks ───────────────────────────


class Link(VM):
    label: str
    href: str


class Option(VM):
    value: str
    label: str
    count: int | None = None


class PersonRef(VM):
    id: str
    name: str
    initials: str
    title: str  # job title, e.g. "Plant Operations Lead"
    kind: PersonKind
    href: str  # capability passport / profile


class CapabilityRef(VM):
    id: str
    name: str
    critical: bool = True


class AreaRef(VM):
    id: str
    name: str
    href: str  # full PAGE url (/blueprint?area=<id>); the drawer partial url lives only on AreaCard


class PersonLevel(VM):
    """One person's level on one capability (chip + name)."""

    person: PersonRef
    level: CapabilityLevel


class FormulaInput(VM):
    label: str
    value: float
    display: str  # "7 / 10", "0.25", "82%"


class Formula(VM):
    expression: str  # human-readable, e.g. "capabilities with ≥1 local at level ≥4 ÷ critical capabilities"
    inputs: list[FormulaInput]


class Metric(VM):
    """A derived score. Never shown without its formula (spec: no unexplained scores)."""

    key: str  # stable id, e.g. "om_readiness"
    label: str  # "OPERATING MODEL READINESS"
    value: float  # exact, unrounded: 0–1 for percentages, raw count otherwise
    display: str  # "68%", "4", "28 DAYS" — backend rounds (half-up); templates print display, never value
    unit: Literal["percent", "count", "days"]
    formula: Formula
    status: Status | None = None
    delta: str | None = None  # "+4 pts since last session", shown after the loop


class Rationale(VM):
    """'Why RELAY recommended this' — required on every AI recommendation."""

    why: str
    evidence: list[str]
    om_component: str | None = None
    if_not_transferred: str | None = None


class AIError(VM):
    """Designed error state (fail-loud policy). Rendered by the error_state macro."""

    kind: AIErrorKind
    function: str  # AI function name, e.g. "analyze_session"
    message: str
    retry_href: str
    retry_method: Literal["GET", "POST"] = "POST"


class ActionItem(VM):
    rank: int
    text: str
    href: str | None = None
    capability: CapabilityRef | None = None
    person: PersonRef | None = None
    ai_suggested: bool = True


# ──────────────────────────────── app shell ────────────────────────────────


class EngagementRef(VM):
    id: str
    name: str  # engagement title
    organization: str
    sector: str
    region: str


class Persona(VM):
    id: str
    role: PersonaRole
    person: PersonRef


class Departure(VM):
    expert: PersonRef
    departure_date: date
    days_remaining: int


class NavItem(VM):
    key: Literal[
        "overview",
        "operating_model",
        "blueprint",
        "people",
        "sessions",
        "knowledge",
        "readiness",
    ]
    label: str
    href: str
    badge: str | None = None  # e.g. pending validations count


class Shell(VM):
    engagement: EngagementRef
    engagements: list[EngagementRef]
    personas: list[Persona]
    current_persona: Persona
    nav: list[NavItem]
    active: Literal[
        "overview", "operating_model", "blueprint", "people", "sessions", "knowledge", "readiness"
    ]
    departure: Departure | None = None
    engagement_switch_href: str  # POST target, form field engagement_id
    persona_switch_href: str  # POST target, form field persona_id


# ──────────────────────────────── overview ────────────────────────────────


class RiskCard(VM):
    severity: Severity
    title: str  # capability / area name
    problem: str
    local_label: Literal["LOCAL TRAINER", "LOCAL CAPABILITY"]
    local_value: str  # "None", "<name> — Performed with Supervision"
    recommended_action: str
    area: AreaRef | None = None
    rationale: Rationale | None = None


class KnowledgeSummary(VM):
    id: str
    title: str
    type: KnowledgeType
    area: AreaRef | None = None
    captured_on: date
    source: Link | None = None
    validation_status: ValidationStatus
    href: str


class TrainTheTrainer(VM):
    capability: CapabilityRef
    current_expert: PersonRef
    candidate_trainer: PersonRef
    current_level: CapabilityLevel
    target_level: CapabilityLevel
    recommended_activity: str
    rationale: Rationale | None = None


class OverviewVM(VM):
    shell: Shell
    headline: list[Metric]  # 5 tiles: OM readiness, localization, teachable, expert-dependent, days
    knowledge_at_risk: list[RiskCard]
    priority_actions: list[ActionItem]
    recent_knowledge: list[KnowledgeSummary]
    train_the_trainer: list[TrainTheTrainer]


# ───────────────────────────── operating model ─────────────────────────────


class AreaCard(VM):
    id: str
    name: str
    href: str  # GET → AreaDrawerVM partial (hx-get only; not a page)
    local_owner: PersonRef | None
    owner_confirmed: bool
    formal_pct: float  # 0–1
    informal_pct: float
    local_capability: LocalCapability
    trainer_coverage: bool
    status: Status


class OperatingModelVM(VM):
    shell: Shell
    title: str  # e.g. "<FUNCTION> OPERATING MODEL"
    mission: str
    summary: list[Metric]
    areas: list[AreaCard]


class DimensionItem(VM):
    label: str
    detail: str | None = None
    owner: PersonRef | None = None
    depends_on_expert: bool = False


class DimensionSection(VM):
    dimension: OMDimension
    items: list[DimensionItem]


class AreaDrawerVM(VM):
    """Partial: GET /operating-model/areas/<area_id>."""

    area: AreaCard
    description: str
    dimensions: list[DimensionSection]  # all 8, in OMDimension order
    transfer_readiness: Metric
    blueprint_href: str


# ──────────────────────────── transfer blueprint ────────────────────────────


class RequirementItem(VM):
    id: str
    label: str
    state: TransferState


class RequirementGroup(VM):
    category: RequirementCategory
    items: list[RequirementItem]


class GapCallout(VM):
    """POTENTIAL FORMAL / INFORMAL KNOWLEDGE GAP."""

    title: str
    formal_rule: str
    expert_practice: list[str]
    capture_href: str | None = None


class BlueprintComponent(VM):
    id: str
    area: AreaRef
    name: str
    status: Status
    local_owner_target: PersonRef | None
    local_capability: list[PersonLevel]
    local_trainer: PersonRef | None
    transfer_risk: str
    groups: list[RequirementGroup]
    gap_callouts: list[GapCallout] = Field(default_factory=list)
    recommended_action: str | None = None
    changed: bool = False  # highlight after a validation moved this component


class BlueprintVM(VM):
    shell: Shell
    summary: list[Metric]  # formal transfer, informal transfer, local ownership
    components: list[BlueprintComponent]
    focus_area_id: str | None = None  # from ?area=<id>: scroll to + highlight that component


# ───────────────────────────────── people ─────────────────────────────────


class PersonCard(VM):
    person: PersonRef
    role_summary: str
    tenure: str | None = None  # "18 years' experience", "Assignment: month 8 of 9"
    departure: Departure | None = None
    independent_count: int  # capabilities at level ≥4
    teachable_count: int  # capabilities at level 6
    owned_areas: list[AreaRef] = Field(default_factory=list)


class PeopleVM(VM):
    shell: Shell
    experts: list[PersonCard]
    counterparts: list[PersonCard]
    trainers: list[PersonCard]  # local trainers + candidates; may repeat counterparts, with trainer-focused summaries


class EvidenceItem(VM):
    id: str
    capability: CapabilityRef
    evidence_type: EvidenceType
    description: str
    source: Link | None  # source session
    recorded_on: date
    ai_interpretation: str | None = None
    validated_by: PersonRef | None = None
    validation_status: ValidationStatus
    level_before: CapabilityLevel | None = None
    level_after: CapabilityLevel | None = None
    resulting_recommendation: str | None = None


class PassportRow(VM):
    capability: CapabilityRef
    level: CapabilityLevel
    rail: TransferRail  # where on the Transfer Rails this capability sits
    evidence_count: int
    exposures: int
    last_demonstrated: date | None
    next_experience: str | None
    trainer_ready: bool
    changed: bool = False  # level moved in the latest validation


class PassportVM(VM):
    shell: Shell
    person: PersonCard
    rows: list[PassportRow]
    evidence: list[EvidenceItem]  # newest first, full append-only history


# ──────────────────────────────── knowledge ────────────────────────────────


class KnowledgeItem(VM):
    """Full Expert Insight template."""

    id: str
    title: str
    type: KnowledgeType
    capability: CapabilityRef | None
    area: AreaRef | None
    situation: str
    observed_signals: list[str]
    expert_reasoning: str
    recommended_response: str
    why_it_matters: str
    source: Link | None
    expert: PersonRef | None
    validation_status: ValidationStatus
    validated_by: PersonRef | None = None
    people_exposed: list[PersonRef]
    captured_on: date
    is_new: bool = False  # captured in the most recent session


class KnowledgeFilter(VM):
    param: Literal["area", "capability", "expert", "person", "type", "status"]  # query param name
    label: str
    options: list[Option]


class GrowthPoint(VM):
    on: date
    total: int


class KnowledgeResultsVM(VM):
    """Partial: GET /knowledge/results?<filters> (HTMX filter swap)."""

    items: list[KnowledgeItem]
    total: int
    active: dict[str, str]  # KnowledgeFilter.param → selected value


class KnowledgeVM(VM):
    shell: Shell
    type_counts: list[Option]  # one per KnowledgeType, value = type
    filters: list[KnowledgeFilter]  # in display order
    results_href: str
    results: KnowledgeResultsVM
    growth: list[GrowthPoint]  # library growth over the engagement


# ──────────────────────────────── readiness ────────────────────────────────


class ReadinessRow(VM):
    area: AreaRef
    formal_pct: float
    informal_pct: float
    local_owner: PersonRef | None
    status: Status


class DepartureStat(VM):
    label: str  # "OPERATING MODEL AREAS"
    display: str  # "7 / 9"
    caption: str  # "locally owned"
    metric: Metric | None = None


class DeparturePanel(VM):
    departure: Departure
    stats: list[DepartureStat]
    before_departure: list[ActionItem]


class RiskFlag(VM):
    kind: Literal[
        "no_local_coverage",
        "undocumented_tacit",
        "no_local_owner",
        "observed_only",
        "single_holder",
        "expert_relationship",
        "no_local_trainer",
    ]
    label: str
    detail: str
    area: AreaRef | None = None
    capability: CapabilityRef | None = None
    severity: Severity


class PropagationNode(VM):
    """Nodes are listed in DFS preorder; the tree macro lays out each depth as a
    row in order of appearance, which guarantees no crossing edges."""

    id: str
    person: PersonRef | None  # None for aggregate group nodes (group_label set)
    level: CapabilityLevel | None  # None for group nodes
    depth: int  # 0 = original holder
    group_label: str | None = None  # e.g. "Shift operators (6)" for aggregate nodes


class PropagationEdge(VM):
    source: str  # node id
    target: str
    state: Literal["demonstrated", "in_progress", "planned"] = "demonstrated"
    label: str | None = None  # "taught 12 Mar"


class PropagationVM(VM):
    """Partial: GET /readiness/propagation?capability=<id>."""

    capability: CapabilityRef
    capability_options: list[Option]
    nodes: list[PropagationNode]
    edges: list[PropagationEdge]
    href: str  # filter target


class WeightRow(VM):
    component: str
    weight: float
    metric_key: str


class ReadinessVM(VM):
    shell: Shell
    headline: Metric  # OM readiness
    metrics: list[Metric]  # localization, ownership, trainer coverage, formal, informal, dependency, departure, knowledge at risk
    weights: list[WeightRow]
    areas: list[ReadinessRow]
    departure: DeparturePanel | None
    flags: list[RiskFlag]
    propagation: PropagationVM


# ──────────────────────────────── sessions ────────────────────────────────


class SessionSummary(VM):
    id: str
    title: str
    held_on: date
    expert: PersonRef
    learner: PersonRef
    focus: CapabilityRef
    stage: SessionStage
    complete: bool
    knowledge_captured: int
    evidence_recorded: int
    teaching_opportunities: int
    follow_ups: int
    href: str


class SessionsVM(VM):
    shell: Shell
    today: SessionSummary | None
    sessions: list[SessionSummary]  # previous, newest first


class StageStep(VM):
    stage: SessionStage
    state: StepState
    href: str | None  # None when not yet reachable


class SessionHeader(VM):
    id: str
    title: str
    held_on: date
    context: str  # one-line situation, e.g. "Line 2 intake, turbidity alarm 06:40"
    expert: PersonRef
    learner: PersonRef
    focus: CapabilityRef
    stage: SessionStage
    steps: list[StageStep]  # all 7, in order


class SessionBrief(VM):
    """The 30-second Session Brief (PREPARE, and NEXT ACTION's next brief)."""

    heading: str  # "TODAY WITH <LEARNER>"
    primary_target: CapabilityRef
    current_level: CapabilityLevel
    todays_objective: str
    your_role: str
    let_learner_lead: str | None = None
    expose_if_possible: CapabilityRef | None = None
    ask_before_explaining: list[str]
    watch_for: list[str]  # rendered as □ checkboxes
    knowledge_gap_to_explore: str | None = None
    coaching_suggestion: str | None = None
    rationale: Rationale


class PrepareVM(VM):
    shell: Shell
    session: SessionHeader
    brief: SessionBrief | None  # None when ai_error is set
    ai_error: AIError | None = None
    start_href: str  # → capture


class CaptureVM(VM):
    shell: Shell
    session: SessionHeader
    transcript: str
    notes: str
    sample_transcript_label: str | None = None  # "Load <session> transcript"
    sample_transcript: str | None = None
    submit_href: str  # POST, fields: transcript, notes


class DebriefQuestion(VM):
    id: str
    prompt: str
    rationale: str  # why this question, tied to the transcript
    answer: str | None = None
    tags: list[LearnerResultTag] = Field(default_factory=list)  # learner debrief only


class DebriefVM(VM):
    """Used for both EXPERT DEBRIEF and LEARNER DEBRIEF stages."""

    shell: Shell
    session: SessionHeader
    role: DebriefRole
    respondent: PersonRef
    allowed: bool  # current persona is the respondent; else show "switch persona" gate
    switch_to_persona_id: str | None = None  # set when allowed is false
    questions: list[DebriefQuestion]
    ai_error: AIError | None = None
    submit_href: str  # POST, fields: answer_<question id>


class FindingBase(VM):
    id: str
    title: str
    status: FindingStatus
    confidence: Confidence
    evidence_sources: list[str]
    rationale: Rationale
    actions: list[FindingAction]  # empty once resolved; resolved findings are not re-actioned
    action_href: str  # POST <action_href>/<action>
    ai_label: str = "AI SUGGESTION"
    validated_by: PersonRef | None = None
    validated_at: datetime | None = None
    reviewer_note: str | None = None


class CapabilityEvidenceFinding(FindingBase):
    kind: Literal[FindingKind.CAPABILITY_EVIDENCE] = FindingKind.CAPABILITY_EVIDENCE
    person: PersonRef
    capability: CapabilityRef
    evidence: list[str]
    current_level: CapabilityLevel
    suggested_level: CapabilityLevel


class TacitKnowledgeFinding(FindingBase):
    kind: Literal[FindingKind.TACIT_KNOWLEDGE] = FindingKind.TACIT_KNOWLEDGE
    formal_rule: str
    expert_practice: list[str]
    proposed_record: KnowledgeItem  # finding.status is the source of truth; approval writes the record as validated


class RemainingGapFinding(FindingBase):
    kind: Literal[FindingKind.REMAINING_GAP] = FindingKind.REMAINING_GAP
    capability: CapabilityRef
    person: PersonRef
    understanding: list[str]  # what the learner can explain
    not_demonstrated: list[str]  # what is still unproven
    instruction: str  # e.g. "Do not advance <capability>."


class NextActivityFinding(FindingBase):
    kind: Literal[FindingKind.NEXT_ACTIVITY] = FindingKind.NEXT_ACTIVITY
    objective: CapabilityRef
    recommended_experience: str
    responsibilities: list[str]
    target_date: date | None = None
    backup_experience: str | None = None


Finding = Annotated[
    Union[
        CapabilityEvidenceFinding,
        TacitKnowledgeFinding,
        RemainingGapFinding,
        NextActivityFinding,
    ],
    Field(discriminator="kind"),
]


class SynthesisVM(VM):
    """SYNTHESIS and VALIDATION stages (validation = same findings, actions live)."""

    shell: Shell
    session: SessionHeader
    findings: list[Finding]
    inputs_used: list[str]  # "Session transcript", "Expert debrief", ...
    ai_error: AIError | None = None
    can_validate: bool  # current persona is the expert
    complete_href: str  # POST → next action; enabled when no finding is pending


class FindingCardVM(VM):
    """Partial: POST /sessions/<id>/findings/<fid>/<action>, and GET …/edit."""

    session_id: str
    finding: Finding
    editing: bool = False
    can_validate: bool


class ChangeItem(VM):
    """'What changed' after validation — the visible proof the loop worked."""

    surface: Literal["passport", "knowledge", "blueprint", "readiness", "brief"]
    label: str
    before: str
    after: str
    href: str


class NextActionVM(VM):
    shell: Shell
    session: SessionHeader
    changes: list[ChangeItem]
    next_brief: SessionBrief | None
    ai_error: AIError | None = None
    schedule_href: str  # POST: create the next session from this brief


# ───────────────────────── registry (fixtures + preview) ─────────────────────────

VIEWMODELS: dict[str, type[VM]] = {
    "overview": OverviewVM,
    "operating_model": OperatingModelVM,
    "area_drawer": AreaDrawerVM,
    "blueprint": BlueprintVM,
    "people": PeopleVM,
    "passport": PassportVM,
    "knowledge": KnowledgeVM,
    "knowledge_results": KnowledgeResultsVM,
    "readiness": ReadinessVM,
    "propagation": PropagationVM,
    "sessions": SessionsVM,
    "session_prepare": PrepareVM,
    "session_capture": CaptureVM,
    "session_expert_debrief": DebriefVM,
    "session_learner_debrief": DebriefVM,
    "session_synthesis": SynthesisVM,
    "session_validation": SynthesisVM,
    "finding_card": FindingCardVM,
    "session_next_action": NextActionVM,
}
