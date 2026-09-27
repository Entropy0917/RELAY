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
    sessions,
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


def _cap_row(
    pc,
    cap_map: dict,
    evidence_counts: dict,
    recommendations: dict[tuple[str, str], str] | None = None,
) -> CapabilityRow:
    cap = cap_map.get(pc.capability_id)
    recommendations = recommendations or {}
    return CapabilityRow(
        capability_id=pc.capability_id,
        capability=cap.name if cap else "",
        level=pc.level,
        level_label=CAPABILITY_LEVELS[pc.level],
        exposures=pc.exposure_count,
        last_demonstrated=str(pc.last_demonstrated) if pc.last_demonstrated else None,
        next_experience=recommendations.get((pc.person_id, pc.capability_id)),
        trainer_ready=(pc.level >= 6),
    )


def _next_experiences(scope: Scope) -> dict[tuple[str, str], str]:
    """(person, capability) -> the work RELAY recommends they lead next.

    Sessions store the whole NEXT_ACTION recommendation; this pulls out the one
    line a capability row has room for. The recommendation names its capability
    in prose, because the model that wrote it was reasoning about capabilities
    rather than rows, so it is matched back to an id by name. An unmatched name
    is skipped rather than guessed -- a row saying nothing is better than a row
    attributing work to the wrong capability.
    """
    by_name = {row.name.casefold(): row.id for row in scope.rows(capabilities)}
    out: dict[tuple[str, str], str] = {}
    for session in scope.rows(sessions):
        recommendation = session.next_experience
        if not recommendation:
            continue
        capability_id = by_name.get(str(recommendation.get("capability", "")).casefold())
        if capability_id is None:
            continue
        work = recommendation.get("recommended_experience")
        if not work:
            continue
        for learner_id in session.learner_ids or ():
            out[(learner_id, capability_id)] = work
    return out


def _knowledge_card(row, people_map: dict, names: dict[str, str]) -> KnowledgeCard:
    """One knowledge item as a card.

    `names` resolves every id this card shows. It is passed in rather than
    looked up from module state: an area name belongs to one engagement, and a
    resolver that outlives the request can answer with another engagement's
    names (see `_display_names`).

    `source_session` stays an id on purpose -- the contract fixture holds ids
    there because the frontend links on it, unlike `area` and `capability`,
    which are read.
    """
    expert = people_map.get(row.expert_id)
    capability_id = getattr(row, "capability_id", None)
    return KnowledgeCard(
        id=row.id,
        title=row.title,
        type=KnowledgeType(row.type),
        type_label=KNOWLEDGE_LABEL.get(KnowledgeType(row.type), row.type),
        area=names.get(getattr(row, "area_id", None) or "", ""),
        capability=names.get(capability_id) if capability_id else None,
        expert=expert.name if expert else "",
        source_session=row.session_id if hasattr(row, "session_id") else None,
        validated=bool(row.validated),
        people_exposed=[
            people_map[pid].name if pid in people_map else pid
            for pid in (row.people_exposed or [])
        ],
        summary=row.summary,
    )


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


# Why this row is on the register, in the engagement's own terms. B4 already
# computes the deciding numbers and hands them over on `RiskFinding.inputs`;
# `_risk_item` used to drop them, which is how three different capabilities
# ended up showing the same sentence. Placeholders are `inputs` keys, so a
# template can only cite a number the engine actually produced.
_RISK_EXPLANATIONS: dict[RiskKind, str] = {
    RiskKind.NO_LOCAL_COVERAGE: (
        "Best local level is {best_local_level}; independent practice starts at "
        "level {threshold}."
    ),
    RiskKind.NO_LOCAL_OWNER: "Recorded owner: {owner_id}; validated: {owner_validated}.",
    RiskKind.UNDOCUMENTED_TACIT: (
        "A {kind} requirement, {state} and not yet validated, with no written "
        "capability behind it."
    ),
    RiskKind.OBSERVED_NEVER_PERFORMED: (
        "Best local level is {best_local_level}; nothing above observation is on "
        "record."
    ),
    RiskKind.SINGLE_KNOWLEDGE_HOLDER: (
        "Held by {holders}. Qualified to teach it: {teachers}."
    ),
    RiskKind.EXPERT_DEPENDENT_RELATIONSHIP: "Transfer state is {state}.",
    RiskKind.NO_LOCAL_TRAINER: (
        "Nobody local has reached trainer level on {area_capabilities}."
    ),
}

# `inputs` values are storage identifiers where they name a row. Rendering one
# straight through would put a primary key on screen, so ids are resolved via
# the engagement's own names -- which keeps the code free of engagement content
# (planv0.2.md section 0.5) while the screen stays readable.
_NONE_MARKERS = frozenset({"(none)", "", "none"})


def _display_names(scope: Scope) -> dict[str, str]:
    """id -> human name, across every table a risk can point at."""
    names: dict[str, str] = {}
    for table in (people, capabilities, operating_model_areas):
        for row in scope.rows(table):
            names[row.id] = row.name
    return names


def _humanize(value: str, names: dict[str, str]) -> str:
    """Resolve ids to names inside a comma-separated input value."""
    if value.strip().lower() in _NONE_MARKERS:
        return "nobody"
    parts = [v.strip() for v in value.split(",") if v.strip()]
    return ", ".join(names.get(part, part) for part in parts)


def _risk_problem(rf: RiskFinding, names: dict[str, str]) -> str:
    """`detail` plus the numbers that put this row on the register.

    A missing key means the engine changed its inputs without this dict
    following; the detail alone is still true, so the row degrades to what it
    said before rather than raising in the middle of a demo.
    """
    template = _RISK_EXPLANATIONS.get(rf.kind)
    if not template:
        return rf.detail
    resolved = {k: _humanize(v, names) for k, v in rf.inputs.items()}
    try:
        return f"{rf.detail} {template.format(**resolved)}"
    except KeyError:
        return rf.detail


def _risk_local_trainer(rf: RiskFinding, names: dict[str, str]) -> str | None:
    """Who could already teach this, when the engine knows of anyone."""
    teachers = rf.inputs.get("teachers", "")
    if not teachers or teachers.strip().lower() in _NONE_MARKERS:
        return None
    return _humanize(teachers, names)


def _risk_item(rf: RiskFinding, names: dict[str, str] | None = None) -> RiskItem:
    names = names or {}
    tmpl = _RISK_TITLES.get(rf.kind, "{name} risk flagged")
    title = tmpl.format(name=rf.subject_name)
    action = _RECOMMENDED_ACTIONS.get(
        rf.kind, "Schedule a transfer session to address this risk before departure."
    )
    return RiskItem(
        severity=rf.value,
        title=title,
        problem=_risk_problem(rf, names),
        local_trainer=_risk_local_trainer(rf, names),
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

def _priority_actions(risk_items: list[RiskItem], *, limit: int) -> list[str]:
    """One line per risk, naming what it is about.

    `recommended_action` is written per risk kind, so three risks of one kind
    read as the same sentence three times. The subject comes from the title
    ("<subject> has no ..."), which every register title follows.
    """
    out: list[str] = []
    for r in risk_items:
        subject = r.title.split(" has ", 1)[0] if " has " in r.title else r.title
        line = f"{subject}: {r.recommended_action}"
        if line not in out:
            out.append(line)
        if len(out) == limit:
            break
    return out


def build_overview(scope: Scope, *, as_of: date) -> dict:
    snapshot = readiness_snapshot(scope, as_of=as_of)
    metrics = headline_metrics(snapshot)

    dep = departing_expert(snapshot)
    risk_register = knowledge_at_risk(snapshot)

    people_map = {row.id: row for row in scope.rows(people)}
    dep_ref = _person_ref(people_map[dep.id]) if dep and dep.id in people_map else None
    days_rem = (dep.departure_date - as_of).days if dep and dep.departure_date else None

    # Recent knowledge
    ki_rows = scope.rows(knowledge_items)
    ki_rows_sorted = sorted(ki_rows, key=lambda r: r.captured_on, reverse=True)
    recent_knowledge = [
        _knowledge_card(r, people_map, _display_names(scope))
        for r in ki_rows_sorted[:5]
    ]

    # Trainer progress: counterparts at level >= 5
    cap_map = {r.id: r for r in scope.rows(capabilities)}
    evidence_counts = _count_evidence(scope)
    recommendations = _next_experiences(scope)
    trainer_progress = []
    for pc in scope.rows(person_capabilities):
        if pc.level >= 5:
            p = people_map.get(pc.person_id)
            if p and Role(p.role) != Role.EXPERT:
                trainer_progress.append(
                    _cap_row(pc, cap_map, evidence_counts, recommendations)
                )

    risk_items = [_risk_item(r, _display_names(scope)) for r in risk_register.findings]

    return dict(
        metrics=[_metric_tile(m) for m in metrics],
        departing_expert=dep_ref,
        days_until_departure=days_rem,
        risks=risk_items[:5],
        priority_actions=_priority_actions(risk_items, limit=3),
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
    recommendations = _next_experiences(scope)

    cap_list = []
    for cap in cap_rows:
        # Get the best person_capability for display
        pcs = scope.rows(
            person_capabilities,
            person_capabilities.c.capability_id == cap.id,
        )
        for pc in pcs:
            cap_list.append(
                _cap_row(pc, {cap.id: cap}, evidence_counts, recommendations)
            )

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
    recommendations = _next_experiences(scope)

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
                    local_caps.append(
                        _cap_row(pc, {cap.id: cap}, evidence_counts, recommendations)
                    )

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
    recommendations = _next_experiences(scope)
    people_map = {r.id: r for r in scope.rows(people)}
    names = _display_names(scope)

    pcs = scope.rows(
        person_capabilities, person_capabilities.c.person_id == person_id
    )
    cap_rows = [
        _cap_row(pc, cap_map, evidence_counts, recommendations) for pc in pcs
    ]

    # Total evidence
    total_evidence = sum(evidence_counts.get(pc.id, 0) for pc in pcs)

    # Knowledge this person has been exposed to
    ki_rows = scope.rows(knowledge_items)
    exposed = [
        _knowledge_card(ki, people_map, names) for ki in ki_rows
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
    names = _display_names(scope)

    ki_rows = scope.rows(knowledge_items)

    # Apply filters
    active_filters: dict[str, str] = {}
    if filters:
        if "type" in filters and filters["type"]:
            ki_rows = [r for r in ki_rows if r.type == filters["type"]]
            active_filters["type"] = filters["type"]
        if "area" in filters and filters["area"]:
            # Accept the area id or its display name (the page links by name).
            ki_rows = [
                r for r in ki_rows
                if filters["area"] in (r.area_id, names.get(r.area_id or "", ""))
            ]
            active_filters["area"] = filters["area"]
        if "person" in filters and filters["person"]:
            # Accept the person id or their display name.
            wanted = {
                pid for pid, p in people_map.items()
                if filters["person"] in (pid, p.name)
            } or {filters["person"]}
            ki_rows = [
                r for r in ki_rows
                if wanted & set(r.people_exposed or [])
            ]
            active_filters["person"] = filters["person"]

    items = [_knowledge_card(r, people_map, names) for r in ki_rows]

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

def build_readiness(
    scope: Scope, *, as_of: date, capability_id: str | None = None
) -> dict:
    """The readiness page. `capability_id` narrows the propagation tree.

    `ReadinessVM.propagation_capability` has been in the contract since it was
    frozen; without an argument to drive it the page could only ever show the
    whole engagement. Filtering asks the question the tree exists to answer --
    who can carry *this* capability once the expert is gone.
    """
    snapshot = readiness_snapshot(scope, as_of=as_of)
    metrics = all_metrics(snapshot)
    area_rmap = {ar.area_id: ar for ar in all_area_readiness(snapshot)}

    names = _display_names(scope)
    risk_register = knowledge_at_risk(snapshot)
    risk_items = [_risk_item(r, names) for r in risk_register.findings]

    areas = []
    for row in scope.rows(operating_model_areas):
        areas.append(_area_card(row, scope, snapshot, area_rmap))

    propagation, propagation_capability = _propagation(scope, capability_id)

    return dict(
        metrics=[_metric_tile(m) for m in metrics.values()],
        areas=areas,
        risks=risk_items,
        before_departure=_priority_actions(risk_items, limit=3),
        propagation=propagation,
        propagation_capability=propagation_capability,
    )


def _propagation(
    scope: Scope, capability_id: str | None
) -> tuple[list[PropagationNode], str | None]:
    """Who learned from whom, optionally narrowed to one capability.

    An unknown capability id yields an empty tree rather than silently showing
    everyone: a filter that appears to have been ignored is worse on a demo
    screen than one that visibly matches nothing.
    """
    people_rows = scope.rows(people)
    label: str | None = None
    included: set[str] | None = None

    if capability_id:
        cap = scope.by_id(capabilities, capability_id)
        label = cap.name if cap is not None else capability_id
        included = {
            pc.person_id
            for pc in scope.rows(
                person_capabilities,
                person_capabilities.c.capability_id == capability_id,
            )
        }
        if cap is None:
            included = set()

    def carries(person_id: str) -> bool:
        return included is None or person_id in included

    learners = [
        r.id for r in people_rows
        if Role(r.role) != Role.EXPERT and carries(r.id)
    ]

    return (
        [
            PropagationNode(
                person=_person_ref(r),
                taught_by=None,
                children=learners,
            )
            for r in people_rows
            if Role(r.role) == Role.EXPERT and carries(r.id)
        ],
        label,
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
    recommendations = _next_experiences(scope)
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
        row=_cap_row(
            pc, {capability_id: cap_row}, evidence_counts, _next_experiences(scope)
        ),
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
