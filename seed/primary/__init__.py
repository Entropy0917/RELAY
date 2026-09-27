"""Assembles the primary engagement, in the one order the database permits.

Ordering here is not tidiness. Foreign keys are on (`PRAGMA foreign_keys=ON`,
db.py), so areas cannot precede their owners and evidence cannot precede the
person_capability it hangs off. Two orderings are load-bearing beyond that:

  * **Levels before validations.** Four rows are inserted at their previous
    level and then moved by `apply_validation`. The trigger refuses a level
    change that does not cite an approved validation, so the finding, the
    validation and the evidence all have to exist first -- which is exactly
    what `app.db.writes` enforces, and the reason the seed goes through it
    rather than writing the four numbers directly.
  * **Sessions before knowledge.** Roughly a third of the library was captured
    out of a session and names it.

`level_at_time` on standing evidence is derived rather than stated: the most
recent observation records the person's present level and each older one steps
down, floored two levels below, so a passport read top to bottom shows
somebody arriving rather than somebody who was always this good. The
alternative -- stamping today's level on an observation from seven months ago
-- is the kind of detail that is invisible until somebody scrolls.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import Connection

# Aliased on import: `seed.primary` has submodules named `people`,
# `capabilities`, `areas`, `knowledge` and `sessions`, and importing a
# submodule binds its name on the package -- which would silently shadow a
# same-named table here. The `t_` prefix makes the two kinds of thing
# distinguishable at every use site rather than only at the import.
from app.db.schema import (
    capabilities as t_capabilities,
    capability_evidence as t_evidence,
    debriefs as t_debriefs,
    engagements as t_engagements,
    findings as t_findings,
    knowledge_items as t_knowledge,
    operating_model_areas as t_areas,
    people as t_people,
    person_capabilities as t_person_capabilities,
    recommendations as t_recommendations,
    sessions as t_sessions,
    transfer_requirements as t_requirements,
)
from app.db.writes import append_evidence, apply_validation

from seed.loader import SeedScope
from seed.primary.areas import AREAS, REQUIREMENTS, is_validated
from seed.primary.capabilities import (
    CAPABILITIES,
    EVIDENCE,
    LEVELS,
    PROMOTIONS,
    pc_id,
)
from seed.primary.knowledge import EXPERT_ID, KNOWLEDGE
from seed.primary.people import ENGAGEMENT, ENGAGEMENT_ID, PEOPLE
from seed.primary.sessions import (
    DEBRIEFS,
    FINDINGS,
    RECOMMENDATIONS,
    SESSION_DAYS,
    SESSION_EVIDENCE,
    SESSIONS,
)
from seed.timeline import days_ago, timestamp

# How far below a person's current level the oldest evidence record may sit.
# Two steps: enough to read as progress, not so much that a level-6 holder's
# first record makes them look like a novice.
_EVIDENCE_DESCENT = 2


def _standing_evidence(scope: SeedScope, level_of: dict[str, int]) -> None:
    """Insert the non-session evidence, newest first, with a level ladder.

    Written straight to the table rather than through `append_evidence`,
    because that helper stamps the person's *current* level and bumps
    `exposure_count`. Both are right for a live exposure and wrong for
    backfilled history: these rows are the record of how somebody got to the
    level they are at, and the exposure counts are seeded deliberately (they
    are higher than the number of write-ups, because most exposures never get
    written up).
    """
    by_pc: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for person_id, capability_id, offset, summary, source in EVIDENCE:
        by_pc[pc_id(person_id, capability_id)].append((offset, summary, source))

    for pc, rows in by_pc.items():
        current = level_of[pc]
        floor = max(1, current - _EVIDENCE_DESCENT)
        # Newest first, so index 0 is the present level.
        for step, (offset, summary, source) in enumerate(sorted(rows)):
            scope.insert(
                t_evidence,
                id=f"ev-{pc.removeprefix('pc-')}-{offset}",
                person_capability_id=pc,
                session_id=None,
                observed_on=days_ago(offset),
                level_at_time=max(floor, current - step),
                summary=summary,
                source=source,
                created_at=timestamp(offset),
            )


def load(conn: Connection) -> int:
    """Insert the whole primary corpus. Returns the number of rows written."""
    scope = SeedScope(conn, ENGAGEMENT_ID)

    scope.insert(t_engagements, **ENGAGEMENT)

    for person in PEOPLE:
        scope.insert(t_people, **person)

    for area in AREAS:
        scope.insert(t_areas, **area)

    for req_id, area_id, kind, label, description, state in REQUIREMENTS:
        scope.insert(
            t_requirements,
            id=f"req-{req_id}",
            area_id=area_id,
            kind=kind,
            label=label,
            description=description,
            state=state,
            validated=is_validated(req_id, state),
        )

    for capability in CAPABILITIES:
        scope.insert(t_capabilities, **capability)

    # Levels are INSERTed at their seeded value. The trigger fires on UPDATE
    # only, so this is the one moment a level may be stated rather than earned;
    # the four in PROMOTIONS are stated one step low and earned below.
    level_of: dict[str, int] = {}
    for person_id, capability_id, level, exposures, demonstrated in LEVELS:
        row_id = pc_id(person_id, capability_id)
        seeded = PROMOTIONS.get((person_id, capability_id), level)
        level_of[row_id] = seeded
        scope.insert(
            t_person_capabilities,
            id=row_id,
            person_id=person_id,
            capability_id=capability_id,
            level=seeded,
            exposure_count=exposures,
            last_demonstrated=None if demonstrated is None else days_ago(demonstrated),
            last_validation_id=None,
        )

    _standing_evidence(scope, level_of)

    for session in SESSIONS:
        scope.insert(
            t_sessions,
            id=session["id"],
            title=session["title"],
            held_on=days_ago(session["days_ago"]),
            stage=session["stage"],
            expert_id=session["expert_id"],
            learner_ids=session["learner_ids"],
            area_id=session["area_id"],
            capability_id=session["capability_id"],
            brief=session["brief"],
            transcript=session["transcript"],
            notes=session["notes"],
        )

    for item in KNOWLEDGE:
        scope.insert(
            t_knowledge,
            id=item["id"],
            title=item["title"],
            type=item["type"],
            summary=item["summary"],
            body=item["body"],
            area_id=item["area_id"],
            capability_id=item["capability_id"],
            session_id=item["session_id"],
            expert_id=EXPERT_ID,
            validated=item["validated"],
            people_exposed=item["exposed"],
            captured_on=days_ago(item["days_ago"]),
        )

    for session_id, role, person_id, questions, offset in DEBRIEFS:
        scope.insert(
            t_debriefs,
            id=f"dbf-{session_id.removeprefix('ses-')}-{role}",
            session_id=session_id,
            role=role,
            person_id=person_id,
            questions=[
                {"id": f"q{n + 1}", "question": question, "answer": answer}
                for n, (question, answer) in enumerate(questions)
            ],
            completed_at=timestamp(offset),
        )

    # Findings are AI output and land `pending`. The validation immediately
    # after each is the human decision -- and, for four of them, the only thing
    # in the system capable of moving a level.
    for finding in FINDINGS:
        scope.insert(
            t_findings,
            id=finding["id"],
            session_id=finding["session_id"],
            kind=finding["kind"],
            title=finding["title"],
            body=finding["body"],
            confidence=finding["confidence"],
            evidence_sources=finding["evidence_sources"],
            rationale=finding["rationale"],
            impact=finding["impact"],
            risk_if_untransferred=finding["risk_if_untransferred"],
            status="pending",
        )

    for finding in FINDINGS:
        decision = finding["validation"]
        pair = decision.get("person_capability")
        held_on = days_ago(SESSION_DAYS[finding["session_id"]])
        apply_validation(
            scope,
            finding_id=finding["id"],
            validated_by_id=decision["by"],
            action=decision["action"],
            person_capability_id=pc_id(*pair) if pair else None,
            new_level=decision.get("new_level"),
            evidence_summary=decision.get("evidence_summary"),
            evidence_source=decision.get("evidence_source"),
            observed_on=held_on,
            edited_body=decision.get("edited_body"),
            note=decision.get("note"),
        )

    # Exposures that came out of a session and changed nobody's level. Routed
    # through `append_evidence` precisely because it stamps the current level:
    # these happened at the level the person holds now.
    for session_id, person_id, capability_id, offset, summary, source in SESSION_EVIDENCE:
        append_evidence(
            scope,
            person_capability_id=pc_id(person_id, capability_id),
            summary=summary,
            source=source,
            session_id=session_id,
            observed_on=days_ago(offset),
        )

    for recommendation in RECOMMENDATIONS:
        scope.insert(t_recommendations, **recommendation)

    return scope.written
