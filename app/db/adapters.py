"""Database rows in, engine inputs out.

B2 (AI) and B4 (readiness) were both built without importing `app.db`, which is
why they are pure, fast and testable against literals. The cost of that choice
is this module: something has to turn rows into the shapes they accept, and it
should be exactly one something.

Both engines describe what they need and refuse to fetch it:

  * `app.readiness.inputs.EngagementSnapshot` -- frozen dataclasses, no I/O,
    `as_of` supplied rather than read from a clock.
  * `app.ai.context.SessionContext` -- a pydantic model that doubles as the
    cache key.

Everything here goes through `Scope`, so an adapter cannot accidentally read
across engagements (planv0.2.md section 0.5). That includes the counting
queries: at demo scale it is cheaper to pull a table and count in Python than
to hand-write a GROUP BY that bypasses the scoping guard. Correctness first --
the whole corpus is a few hundred rows.

`as_of` is a parameter in both directions for the same reason B4 made it one:
a demo rehearsed on Tuesday and presented on Wednesday must produce the same
"days until departure", and a test written today must still pass next month.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.ai.context import (
    CapabilityState,
    EngagementContext,
    Person as AIPerson,
    QA,
    SessionContext,
)
from app.db.schema import (
    capabilities,
    capability_evidence,
    debriefs,
    engagements,
    knowledge_items,
    operating_model_areas,
    people,
    person_capabilities,
    sessions,
    transfer_requirements,
)
from app.db.scoped import Scope
from app.readiness.inputs import (
    Area,
    Capability,
    CapabilityLevel,
    EngagementSnapshot,
    KnowledgeItem,
    Person,
    Requirement,
)
from app.readiness.weights import FORMAL_KINDS, ReadinessWeights

from contracts.vocabulary import (
    KnowledgeType,
    RequirementKind,
    Role,
    TransferState,
)

# `capabilities.criticality` is 1..5; readiness (section 4 B4) asks a yes/no
# question. Four is the line: a capability is critical when the engagement
# would be in trouble without it locally. Named rather than inlined so an
# engagement that scores criticality differently has one place to look.
CRITICAL_CRITICALITY = 4


class AdapterError(RuntimeError):
    """The database does not contain what an engine was asked to score."""


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


def readiness_snapshot(scope: Scope, *, as_of: date) -> EngagementSnapshot:
    """Everything the readiness engine reads, for one engagement, at one date."""
    engagement = scope.one(engagements, engagements.c.id == scope.engagement_id)
    if engagement is None:
        raise AdapterError(f"no engagement '{scope.engagement_id}'")

    # Evidence counts, by person_capability. One pass, one query.
    evidence_counts: dict[str, int] = defaultdict(int)
    for row in scope.rows(capability_evidence):
        evidence_counts[row.person_capability_id] += 1

    # Capabilities carry the area link, so the area -> capabilities grouping is
    # built here rather than queried per area.
    caps = scope.rows(capabilities)
    by_area: dict[str, list[str]] = defaultdict(list)
    for cap in caps:
        if cap.area_id:
            by_area[cap.area_id].append(cap.id)

    return EngagementSnapshot(
        engagement_id=scope.engagement_id,
        as_of=as_of,
        people=tuple(
            Person(
                id=row.id,
                name=row.name,
                role=Role(row.role),
                departure_date=row.departure_date,
            )
            for row in scope.rows(people)
        ),
        capabilities=tuple(
            Capability(
                id=row.id,
                name=row.name,
                critical=row.criticality >= CRITICAL_CRITICALITY,
            )
            for row in caps
        ),
        levels=tuple(
            CapabilityLevel(
                person_id=row.person_id,
                capability_id=row.capability_id,
                level=row.level,
                exposures=row.exposure_count,
                evidence_count=evidence_counts[row.id],
                last_demonstrated=row.last_demonstrated,
            )
            for row in scope.rows(person_capabilities)
        ),
        areas=tuple(
            Area(
                id=row.id,
                name=row.name,
                critical=bool(row.critical),
                local_owner_id=row.local_owner_id,
                owner_validated=bool(row.owner_validated),
                capability_ids=tuple(sorted(by_area.get(row.id, ()))),
            )
            for row in scope.rows(operating_model_areas)
        ),
        requirements=tuple(
            Requirement(
                id=row.id,
                area_id=row.area_id,
                kind=RequirementKind(row.kind),
                state=TransferState(row.state),
                validated=bool(row.validated),
                capability_id=row.capability_id,
            )
            for row in scope.rows(transfer_requirements)
        ),
        knowledge=tuple(
            KnowledgeItem(
                id=row.id,
                type=KnowledgeType(row.type),
                validated=bool(row.validated),
                area_id=row.area_id,
                capability_id=row.capability_id,
                exposed_person_ids=tuple(row.people_exposed or ()),
            )
            for row in scope.rows(knowledge_items)
        ),
        weights=_weights(engagement.readiness_weights),
    )


def _weights(stored: dict | None) -> ReadinessWeights | None:
    """Per-engagement weights, or None to mean 'use the default set'.

    An empty JSON object is the normal untuned case, not a configuration error.
    A partial one is filled from the defaults so an engagement can override a
    single component without restating all five -- `ReadinessWeights` still
    rejects the result if it no longer sums to 1.
    """
    if not stored:
        return None
    return ReadinessWeights(**stored)


# ---------------------------------------------------------------------------
# AI session context
# ---------------------------------------------------------------------------


def session_context(scope: Scope, session_id: str, *, as_of: date) -> SessionContext:
    """Build the context object the AI functions take.

    Later stages of the loop simply find more of it filled in: at PREPARE there
    is no transcript and no debriefs, at SYNTHESIS there is everything. The
    caller does not choose what to include -- it passes the session and gets
    whatever exists, which is what keeps the cache key honest.
    """
    session = scope.by_id(sessions, session_id)
    if session is None:
        raise AdapterError(f"no session '{session_id}' in this engagement")

    engagement = scope.one(engagements, engagements.c.id == scope.engagement_id)
    if engagement is None:
        raise AdapterError(f"no engagement '{scope.engagement_id}'")

    by_id = {row.id: row for row in scope.rows(people)}
    expert = by_id.get(session.expert_id)
    if expert is None:
        raise AdapterError(
            f"session '{session_id}' names expert '{session.expert_id}', "
            f"who is not in this engagement"
        )

    learner_ids = list(session.learner_ids or ())
    area = scope.by_id(operating_model_areas, session.area_id) if session.area_id else None

    return SessionContext(
        engagement=EngagementContext(
            name=engagement.name,
            sector=engagement.sector,
            organization=engagement.org,
            mission=engagement.mission,
            days_until_departure=_days_until(expert.departure_date, as_of),
        ),
        area=area.name if area is not None else "",
        objective=session.title,
        expert=_ai_person(expert),
        learners=[_ai_person(by_id[pid]) for pid in learner_ids if pid in by_id],
        capabilities=_capability_states(scope, session, learner_ids, by_id),
        formal_rules=_requirement_labels(scope, session.area_id, formal=True),
        open_gaps=_open_gaps(scope, session.area_id),
        prior_sessions=_prior_sessions(scope, session),
        transcript=session.transcript,
        notes=session.notes,
        expert_debrief=_debrief(scope, session_id, "expert"),
        learner_debrief=_debrief(scope, session_id, "learner"),
    )


def _ai_person(row) -> AIPerson:
    return AIPerson(name=row.name, title=row.title, role=Role(row.role))


def _days_until(departure: date | None, as_of: date) -> int | None:
    """Negative is meaningful: the expert has already left."""
    return None if departure is None else (departure - as_of).days


def _capability_states(
    scope: Scope, session, learner_ids: list[str], by_id: dict
) -> list[CapabilityState]:
    """Where each learner stands on this session's capability, and why.

    Scoped to the session's capability when it names one. A session about
    everything is a session the AI cannot prepare for usefully.
    """
    if not session.capability_id:
        return []

    cap = scope.by_id(capabilities, session.capability_id)
    if cap is None:
        return []

    evidence: dict[str, list[str]] = defaultdict(list)
    for row in scope.rows(capability_evidence):
        evidence[row.person_capability_id].append(row.summary)

    states = []
    for row in scope.rows(
        person_capabilities,
        person_capabilities.c.capability_id == session.capability_id,
    ):
        if row.person_id not in learner_ids:
            continue
        person = by_id.get(row.person_id)
        states.append(
            CapabilityState(
                capability=cap.name,
                level=row.level,
                person=person.name if person else "",
                evidence=evidence.get(row.id, []),
                last_demonstrated=(
                    row.last_demonstrated.isoformat() if row.last_demonstrated else None
                ),
            )
        )
    return states


def _requirement_labels(scope: Scope, area_id: str | None, *, formal: bool) -> list[str]:
    if not area_id:
        return []
    rows = scope.rows(
        transfer_requirements, transfer_requirements.c.area_id == area_id
    )
    return [
        row.label
        for row in rows
        if (RequirementKind(row.kind) in FORMAL_KINDS) is formal
    ]


def _open_gaps(scope: Scope, area_id: str | None) -> list[str]:
    """Requirements on this area that are not yet fully transferred."""
    if not area_id:
        return []
    rows = scope.rows(
        transfer_requirements, transfer_requirements.c.area_id == area_id
    )
    return [
        row.label
        for row in rows
        if TransferState(row.state) is not TransferState.COMPLETE
    ]


def _prior_sessions(scope: Scope, session) -> list[str]:
    """Earlier sessions on the same area, oldest first.

    "Earlier" is by date, so a session added late for a past date still lands
    in the right place in the narrative.
    """
    rows = [
        row
        for row in scope.rows(sessions)
        if row.id != session.id
        and row.held_on < session.held_on
        and (session.area_id is None or row.area_id == session.area_id)
    ]
    return [row.title for row in sorted(rows, key=lambda r: r.held_on)]


def _debrief(scope: Scope, session_id: str, role: str) -> list[QA]:
    """Flatten every debrief of one role on this session into question/answer.

    Unanswered questions are kept with `answer=None` on purpose: "the learner
    was asked this and has not replied" is different from "nobody asked", and
    the synthesis prompt can tell the difference.
    """
    out: list[QA] = []
    for row in scope.rows(debriefs, debriefs.c.session_id == session_id):
        if row.role != role:
            continue
        for item in row.questions or ():
            out.append(
                QA(question=item.get("question", ""), answer=item.get("answer"))
            )
    return out
