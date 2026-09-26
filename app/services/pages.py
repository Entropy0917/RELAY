"""Read-surface services — B5 (planv0.2.md section 4).

Services that produce the frozen view models for the eight GET routes.
Each function takes a Scope and returns kwargs for its view model's
constructor.  The routes add `shell` and call the constructor.

Rules this module follows:
  - Never hand-write a query. Everything goes through Scope.
  - Readiness comes from `app.readiness` via `app.db.adapters.readiness_snapshot`.
  - MetricTile.delta is left as None (HANDOFF.md item 5.2 undecided).
  - No engagement content — no names, no places, no domain nouns.
"""

from __future__ import annotations

from datetime import date

from app.db.adapters import readiness_snapshot
from app.db.schema import (
    capabilities,
    capability_evidence,
    knowledge_items,
    operating_model_areas,
    people,
    person_capabilities,
    transfer_requirements,
)
from app.db.scoped import Scope
from app.readiness import (
    AreaReadiness,
    Metric,
    RiskFinding,
    RiskKind,
    all_area_readiness,
    all_metrics,
    departing_expert,
    departure_readiness,
    headline_metrics,
    knowledge_at_risk,
)
from contracts.viewmodels import (
    AreaCard,
    AreaDetailVM,
    BlueprintAreaVM,
    BlueprintVM,
    CapabilityRow,
    KnowledgeCard,
    MetricTile,
    OperatingModelVM,
    OverviewVM,
    PassportVM,
    PeopleVM,
    PersonRef,
    PropagationNode,
    ReadinessVM,
    RequirementRow,
    RiskItem,
    KnowledgeVM,
)
from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    KNOWLEDGE_LABEL,
    KnowledgeType,
    OM_DIMENSIONS,
    REQUIREMENT_LABEL,
    RequirementKind,
    Role,
    STATUS_LABEL,
    Status,
    TRANSFER_GLYPH,
    TransferState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _person_ref(row) -> PersonRef:
    name = row.name
    parts = name.split()
    initials = "".join(p[0].upper() for p in parts if p) or "?"
    return PersonRef(
        id=row.id, name=row.name, title=row.title,
        role=Role(row.role), initials=initials,
    )


def _metric_tile(m: Metric) -> MetricTile:
    return MetricTile(**m.as_tile())


def _cap_row(pc, cap_map: dict, evidence_counts: dict) -> CapabilityRow:
    cap = cap_map.get(pc.capability_id)
    return CapabilityRow(
        capability_id=pc.capability_id,
        capability=cap.name if cap else "",
        level=pc.level,
        level_label=CAPABILITY_LEVELS[pc.level],
        exposures=pc.exposure_count,
        last_demonstrated=str(pc.last_demonstrated) if pc.last_demonstrated else None,
        trainer_ready=(pc.level >= 6),
    )


def _knowledge_card(row, people_map: dict) -> KnowledgeCard:
    expert = people_map.get(row.expert_id)
    return KnowledgeCard(
        id=row.id,
        title=row.title,
        type=KnowledgeType(row.type),
        type_label=KNOWLEDGE_LABEL.get(KnowledgeType(row.type), row.type),
        area=_area_name(row.area_id) if hasattr(row, "area_id") else "",
        capability=None,
        expert=expert.name if expert else "",
        source_session=row.session_id if hasattr(row, "session_id") else None,
        validated=bool(row.validated),
        people_exposed=list(row.people_exposed or []),
        summary=row.summary,
    )


# Cache-friendly area name resolver
_area_cache: dict[str, str] = {}


def _area_name(area_id: str | None) -> str:
    return _area_cache.get(area_id or "", "")


def _load_area_cache(scope: Scope) -> None:
    global _area_cache
    _area_cache = {row.id: row.name for row in scope.rows(operating_model_areas)}


_RECOMMENDED_ACTIONS: dict[RiskKind, str] = {
    RiskKind.NO_LOCAL_COVERAGE: "Pair counterpart with expert for hands-on sessions before departure.",
    RiskKind.NO_LOCAL_OWNER: "Designate and validate a local owner for this operating area.",
    RiskKind.UNDOCUMENTED_TACIT: "Run debrief session to capture and validate tacit heuristics.",
    RiskKind.OBSERVED_NEVER_PERFORMED: "Schedule supervised practice session for local counterpart.",
    RiskKind.SINGLE_KNOWLEDGE_HOLDER: "Cross-train a second counterpart to eliminate single-point risk.",
    RiskKind.EXPERT_DEPENDENT_RELATIONSHIP: "Conduct joint relationship-transfer meetings with key contacts.",
    RiskKind.NO_LOCAL_TRAINER: "Advance qualified counterpart to Level 6 (Trainer).",
}

_RISK_TITLES: dict[RiskKind, str] = {
    RiskKind.NO_LOCAL_COVERAGE: "{name} has no independent local coverage",
    RiskKind.NO_LOCAL_OWNER: "{name} has no validated local owner",
    RiskKind.UNDOCUMENTED_TACIT: "Tacit knowledge in {name} is undocumented",
    RiskKind.OBSERVED_NEVER_PERFORMED: "{name} observed but never performed",
    RiskKind.SINGLE_KNOWLEDGE_HOLDER: "{name} relies on a single knowledge holder",
    RiskKind.EXPERT_DEPENDENT_RELATIONSHIP: "Expert-dependent relationship in {name}",
    RiskKind.NO_LOCAL_TRAINER: "{name} has no qualified local trainer",
}


def _risk_item(rf: RiskFinding) -> RiskItem:
    tmpl = _RISK_TITLES.get(rf.kind, "{name} risk flagged")
    title = tmpl.format(name=rf.subject_name)
    action = _RECOMMENDED_ACTIONS.get(
        rf.kind, "Schedule a transfer session to address this risk before departure."
    )
    return RiskItem(
        severity=rf.value,
        title=title,
        problem=rf.detail,
        local_trainer=None,
        recommended_action=action,
    )


def _area_card(
    area_row, scope: Scope, snapshot, area_readiness_map: dict[str, AreaReadiness]
) -> AreaCard:
    local_owner = None
    if area_row.local_owner_id:
        owner_row = scope.by_id(people, area_row.local_owner_id)
        if owner_row:
            local_owner = _person_ref(owner_row)

    ar = area_readiness_map.get(area_row.id)
    if ar is not None:
        card_data = ar.as_card()
        return AreaCard(local_owner=local_owner, **card_data)

    return AreaCard(
        id=area_row.id,
        name=area_row.name,
        local_owner=local_owner,
        formal_pct=area_row.formal_pct,
        informal_pct=100 - area_row.formal_pct,
        local_capability="Limited",
        trainer_coverage=False,
        status=Status.IN_PROGRESS,
        status_label=STATUS_LABEL.get(Status.IN_PROGRESS, "Transfer in Progress"),
    )


def _requirement_row(row) -> RequirementRow:
    kind = RequirementKind(row.kind)
    state = TransferState(row.state)
    return RequirementRow(
        id=row.id,
        kind=kind,
        label=row.label,
        description=row.description,
        state=state,
        glyph=TRANSFER_GLYPH.get(state, "○"),
    )


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def build_overview(scope: Scope, *, as_of: date) -> dict:
    snapshot = readiness_snapshot(scope, as_of=as_of)
    metrics = headline_metrics(snapshot)

    dep = departing_expert(snapshot)
    risk_register = knowledge_at_risk(snapshot)

    _load_area_cache(scope)
    people_map = {row.id: row for row in scope.rows(people)}
    dep_ref = _person_ref(people_map[dep.id]) if dep and dep.id in people_map else None
    days_rem = (dep.departure_date - as_of).days if dep and dep.departure_date else None

    # Recent knowledge
    ki_rows = scope.rows(knowledge_items)
    ki_rows_sorted = sorted(ki_rows, key=lambda r: r.captured_on, reverse=True)
    recent_knowledge = [_knowledge_card(r, people_map) for r in ki_rows_sorted[:5]]

    # Trainer progress: counterparts at level >= 5
    cap_map = {r.id: r for r in scope.rows(capabilities)}
    evidence_counts = _count_evidence(scope)
    trainer_progress = []
    for pc in scope.rows(person_capabilities):
        if pc.level >= 5:
            p = people_map.get(pc.person_id)
            if p and Role(p.role) != Role.EXPERT:
                trainer_progress.append(_cap_row(pc, cap_map, evidence_counts))

    risk_items = [_risk_item(r) for r in risk_register.findings]

    return dict(
        metrics=[_metric_tile(m) for m in metrics],
        departing_expert=dep_ref,
        days_until_departure=days_rem,
        risks=risk_items[:5],
        priority_actions=[r.recommended_action for r in risk_items[:3]],
        recent_knowledge=recent_knowledge,
        trainer_progress=trainer_progress,
    )


# ---------------------------------------------------------------------------
# Operating Model
# ---------------------------------------------------------------------------

def build_operating_model(scope: Scope, *, as_of: date) -> dict:
    snapshot = readiness_snapshot(scope, as_of=as_of)
    area_map = {ar.area_id: ar for ar in all_area_readiness(snapshot)}

    from app.db.schema import engagements
    eng = scope.one(engagements, engagements.c.id == scope.engagement_id)

    areas = []
    for row in scope.rows(operating_model_areas):
        areas.append(_area_card(row, scope, snapshot, area_map))

    return dict(
        mission=eng.mission if eng else "",
        areas=areas,
    )


# ---------------------------------------------------------------------------
# Area Detail
# ---------------------------------------------------------------------------

def build_area_detail(scope: Scope, area_id: str, *, as_of: date) -> dict:
    area_row = scope.by_id(operating_model_areas, area_id)
    if area_row is None:
        raise ValueError(f"no operating model area '{area_id}'")

    snapshot = readiness_snapshot(scope, as_of=as_of)
    area_map = {ar.area_id: ar for ar in all_area_readiness(snapshot)}

    card = _area_card(area_row, scope, snapshot, area_map)

    # Dimensions
    dimensions: dict[str, list[str]] = {}
    for dim_key, dim_label in OM_DIMENSIONS:
        val = getattr(area_row, dim_key, None) or []
        dimensions[dim_key] = list(val) if isinstance(val, list) else [str(val)]

    # Requirements for this area
    req_rows = scope.rows(
        transfer_requirements, transfer_requirements.c.area_id == area_id
    )
    requirements = [_requirement_row(r) for r in req_rows]

    # Capabilities linked to this area
    cap_rows = scope.rows(capabilities, capabilities.c.area_id == area_id)
    cap_map = {r.id: r for r in cap_rows}
    evidence_counts = _count_evidence(scope)

    cap_list = []
    for cap in cap_rows:
        # Get the best person_capability for display
        pcs = scope.rows(
            person_capabilities,
            person_capabilities.c.capability_id == cap.id,
        )
        for pc in pcs:
            cap_list.append(_cap_row(pc, {cap.id: cap}, evidence_counts))

    return dict(
        area=card,
        dimensions=dimensions,
        requirements=requirements,
        capabilities=cap_list,
    )


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

def build_blueprint(scope: Scope, *, as_of: date) -> dict:
    snapshot = readiness_snapshot(scope, as_of=as_of)
    area_rmap = {ar.area_id: ar for ar in all_area_readiness(snapshot)}
    cap_map = {r.id: r for r in scope.rows(capabilities)}
    evidence_counts = _count_evidence(scope)

    areas = []
    for area_row in scope.rows(operating_model_areas):
        card = _area_card(area_row, scope, snapshot, area_rmap)

        # Requirements grouped by kind
        req_rows = scope.rows(
            transfer_requirements,
            transfer_requirements.c.area_id == area_row.id,
        )
        groups: dict[RequirementKind, list[RequirementRow]] = {}
        for r in req_rows:
            kind = RequirementKind(r.kind)
            groups.setdefault(kind, []).append(_requirement_row(r))

        # Local capabilities
        cap_rows = scope.rows(
            capabilities, capabilities.c.area_id == area_row.id,
        )
        local_caps = []
        for cap in cap_rows:
            pcs = scope.rows(
                person_capabilities,
                person_capabilities.c.capability_id == cap.id,
            )
            for pc in pcs:
                p = scope.by_id(people, pc.person_id)
                if p and Role(p.role) != Role.EXPERT:
                    local_caps.append(_cap_row(pc, {cap.id: cap}, evidence_counts))

        areas.append(BlueprintAreaVM(
            area=card,
            groups=groups,
            local_capability=local_caps,
            transfer_risk=card.status,
        ))

    return dict(areas=areas)


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------

def build_people(scope: Scope) -> dict:
    rows = scope.rows(people)
    experts = [_person_ref(r) for r in rows if Role(r.role) == Role.EXPERT]
    counterparts = [_person_ref(r) for r in rows if Role(r.role) == Role.COUNTERPART]
    trainers = []
    # Trainers are counterparts who can teach at least one capability
    cap_map = {r.id: r for r in scope.rows(capabilities)}
    for r in rows:
        if Role(r.role) == Role.EXPERT:
            continue
        pcs = scope.rows(
            person_capabilities, person_capabilities.c.person_id == r.id
        )
        if any(pc.level >= 6 for pc in pcs):
            trainers.append(_person_ref(r))

    return dict(experts=experts, counterparts=counterparts, trainers=trainers)


# ---------------------------------------------------------------------------
# Passport
# ---------------------------------------------------------------------------

def build_passport(scope: Scope, person_id: str, *, as_of: date) -> dict:
    person_row = scope.by_id(people, person_id)
    if person_row is None:
        raise ValueError(f"no person '{person_id}'")

    cap_map = {r.id: r for r in scope.rows(capabilities)}
    evidence_counts = _count_evidence(scope)
    people_map = {r.id: r for r in scope.rows(people)}

    pcs = scope.rows(
        person_capabilities, person_capabilities.c.person_id == person_id
    )
    cap_rows = [_cap_row(pc, cap_map, evidence_counts) for pc in pcs]

    # Total evidence
    total_evidence = sum(evidence_counts.get(pc.id, 0) for pc in pcs)

    # Knowledge this person has been exposed to
    ki_rows = scope.rows(knowledge_items)
    exposed = [
        _knowledge_card(ki, people_map) for ki in ki_rows
        if person_id in (ki.people_exposed or [])
    ]

    return dict(
        person=_person_ref(person_row),
        capabilities=cap_rows,
        evidence_count=total_evidence,
        knowledge_exposed=exposed,
    )


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------

def build_knowledge(scope: Scope, *, filters: dict | None = None) -> dict:
    people_map = {r.id: r for r in scope.rows(people)}
    _load_area_cache(scope)

    ki_rows = scope.rows(knowledge_items)

    # Apply filters
    active_filters: dict[str, str] = {}
    if filters:
        if "type" in filters and filters["type"]:
            ki_rows = [r for r in ki_rows if r.type == filters["type"]]
            active_filters["type"] = filters["type"]
        if "area" in filters and filters["area"]:
            ki_rows = [r for r in ki_rows if r.area_id == filters["area"]]
            active_filters["area"] = filters["area"]
        if "person" in filters and filters["person"]:
            ki_rows = [
                r for r in ki_rows
                if filters["person"] in (r.people_exposed or [])
            ]
            active_filters["person"] = filters["person"]

    items = [_knowledge_card(r, people_map) for r in ki_rows]

    # Counts by type (over unfiltered data)
    all_ki = scope.rows(knowledge_items)
    counts: dict[KnowledgeType, int] = {}
    for kt in KnowledgeType:
        counts[kt] = sum(1 for r in all_ki if r.type == kt.value)

    return dict(
        items=items,
        counts_by_type=counts,
        active_filters=active_filters,
    )


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------

def build_readiness(scope: Scope, *, as_of: date) -> dict:
    snapshot = readiness_snapshot(scope, as_of=as_of)
    metrics = all_metrics(snapshot)
    area_rmap = {ar.area_id: ar for ar in all_area_readiness(snapshot)}

    risk_register = knowledge_at_risk(snapshot)
    risk_items = [_risk_item(r) for r in risk_register.findings]

    areas = []
    for row in scope.rows(operating_model_areas):
        areas.append(_area_card(row, scope, snapshot, area_rmap))

    # Propagation — build a simple tree
    people_map = {r.id: r for r in scope.rows(people)}
    propagation: list[PropagationNode] = []
    for p_row in scope.rows(people):
        if Role(p_row.role) == Role.EXPERT:
            propagation.append(PropagationNode(
                person=_person_ref(p_row),
                taught_by=None,
                children=[
                    pid for pid in people_map
                    if Role(people_map[pid].role) != Role.EXPERT
                ],
            ))

    return dict(
        metrics=[_metric_tile(m) for m in metrics.values()],
        areas=areas,
        risks=risk_items,
        before_departure=[r.recommended_action for r in risk_items[:3]],
        propagation=propagation,
        propagation_capability=None,
    )


# ---------------------------------------------------------------------------
# Capability row partial
# ---------------------------------------------------------------------------

def build_capability_row(scope: Scope, person_id: str, capability_id: str) -> dict:
    person_row = scope.by_id(people, person_id)
    if person_row is None:
        raise ValueError(f"no person '{person_id}'")

    cap_row = scope.by_id(capabilities, capability_id)
    if cap_row is None:
        raise ValueError(f"no capability '{capability_id}'")

    evidence_counts = _count_evidence(scope)
    pc = None
    for row in scope.rows(
        person_capabilities,
        person_capabilities.c.person_id == person_id,
        person_capabilities.c.capability_id == capability_id,
    ):
        pc = row
        break

    if pc is None:
        raise ValueError(f"no person_capability for {person_id}/{capability_id}")

    return dict(
        row=_cap_row(pc, {capability_id: cap_row}, evidence_counts),
        person=_person_ref(person_row),
    )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _count_evidence(scope: Scope) -> dict[str, int]:
    """Count evidence rows per person_capability_id."""
    counts: dict[str, int] = {}
    for row in scope.rows(capability_evidence):
        counts[row.person_capability_id] = counts.get(row.person_capability_id, 0) + 1
    return counts
