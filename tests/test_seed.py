"""The seed corpus, checked structurally -- never by quoting it.

Two rules shape this file.

**It asserts shape, not content.** `test_no_baked_data.py` scans `tests/` for
demo engagement content, and exempts only `seed/`. That is not an obstacle to
route around; it is the same discipline applied one level up. A test that
hard-codes a name is a test that has to be rewritten the day the demo
engagement changes, and the thing actually worth guarding is that the corpus
has the right *structure* -- every foreign key resolving, every enum value
drawn from the frozen vocabulary, the readiness figures the demo script
depends on. So every value here is read back out of the database, and the
expected numbers are counts, ratios and enum memberships.

**It builds its own database.** The corpus loads into a temporary file per
test session rather than against `relay.db`, so running the suite never
disturbs a rehearsed demo and a failure here cannot be explained away by
something somebody did by hand at a prompt.

The anchor date is pinned before the seed is imported (`RELAY_SEED_TODAY`), so
the date assertions are not time bombs -- `seed/timeline.py` resolves the
anchor once, at import.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
from sqlalchemy import func, inspect, select, text

from app.db.connection import connect, get_engine
from app.db.schema import (
    CONTENT_TABLES,
    capabilities,
    capability_evidence,
    debriefs,
    engagements,
    findings,
    knowledge_items,
    metadata,
    operating_model_areas,
    people,
    person_capabilities,
    recommendations,
    sessions,
    transfer_requirements,
    validations,
)
from app.db.scoped import Scope, list_engagements, primary_engagement
from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    LEVEL_INDEPENDENT,
    LEVEL_TEACHER,
    OM_DIMENSIONS,
    FindingKind,
    KnowledgeType,
    RequirementKind,
    Role,
    SessionStage,
    TransferState,
    ValidationAction,
)

# Pinned before `seed` is imported anywhere in this module, because
# seed/timeline.py resolves its anchor at import time.
ANCHOR = date(2026, 3, 2)
os.environ.setdefault("RELAY_SEED_TODAY", ANCHOR.isoformat())

from app.db.adapters import readiness_snapshot  # noqa: E402
from app.readiness import all_metrics, percent  # noqa: E402
from seed import AlreadySeeded, load_all  # noqa: E402

# What the demo script promises the audience in its first ten seconds
# (planv0.2.md section 4 B3, acceptance).
TARGET_READINESS_PCT = "68%"
TARGET_LOCALIZATION_PCT = "70%"
TARGET_TEACHABLE = 4
TARGET_EXPERT_DEPENDENT = 3
TARGET_DAYS_TO_DEPARTURE = 28

# The seven knowledge types and the four finding kinds are frozen vocabulary;
# the corpus is required to exercise all of the former.
ALL_KNOWLEDGE_TYPES = {k.value for k in KnowledgeType}


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    """One loaded corpus, shared. Loading is ~200ms; doing it per test is waste."""
    engine = get_engine(str(tmp_path_factory.mktemp("seed") / "corpus.db"))
    metadata.create_all(engine)
    total = load_all(engine)
    return engine, total


@pytest.fixture(scope="module")
def conn(seeded):
    engine, _ = seeded
    with connect(engine) as connection:
        yield connection


@pytest.fixture(scope="module")
def engagement_ids(conn) -> list[str]:
    return [row.id for row in list_engagements(conn)]


@pytest.fixture(scope="module")
def primary_id(conn) -> str:
    return primary_engagement(conn).id


def _count(conn, table, engagement_id: str) -> int:
    return conn.execute(
        select(func.count())
        .select_from(table)
        .where(table.c.engagement_id == engagement_id)
    ).scalar_one()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def test_load_all_reports_the_rows_it_wrote(seeded, conn, engagement_ids) -> None:
    """`scripts/reset.py` prints this number; it has to be the real one."""
    _, reported = seeded
    actual = conn.execute(
        select(func.count()).select_from(engagements)
    ).scalar_one()
    for table in CONTENT_TABLES:
        actual += conn.execute(select(func.count()).select_from(table)).scalar_one()
    assert reported == actual


def test_load_all_refuses_to_layer_a_second_corpus(seeded) -> None:
    """Evidence is append-only, so a second load cannot clean up after itself."""
    engine, _ = seeded
    with pytest.raises(AlreadySeeded):
        load_all(engine)


def test_every_content_table_has_rows(conn) -> None:
    empty = [
        table.name
        for table in CONTENT_TABLES
        if conn.execute(select(func.count()).select_from(table)).scalar_one() == 0
    ]
    assert not empty, f"seeded nothing into {empty}; those pages render blank"


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------


def test_two_engagements_one_of_them_primary(conn, engagement_ids) -> None:
    assert len(engagement_ids) == 2
    primaries = [
        row.id for row in list_engagements(conn) if row.is_primary
    ]
    assert len(primaries) == 1


def test_the_two_engagements_are_different_kinds_of_work(conn) -> None:
    """section 0.5's claim is only demonstrated if the switch is obvious."""
    rows = list_engagements(conn)
    assert len({row.sector for row in rows}) == 2
    assert len({row.location for row in rows}) == 2
    assert len({row.org for row in rows}) == 2


def test_no_row_carries_another_engagements_id(conn, engagement_ids) -> None:
    known = set(engagement_ids)
    for table in CONTENT_TABLES:
        found = {
            row[0]
            for row in conn.execute(select(table.c.engagement_id).distinct())
        }
        assert found <= known, f"{table.name} references an unknown engagement"
        assert found, f"{table.name} is empty"


def test_scope_sees_only_its_own_engagement(conn, engagement_ids) -> None:
    first, second = engagement_ids
    a = {row.id for row in Scope(conn, first).rows(people)}
    b = {row.id for row in Scope(conn, second).rows(people)}
    assert a and b
    assert not a & b


def test_every_engagement_renders_every_page(conn, engagement_ids) -> None:
    """The switcher is useless if half the pages come up empty."""
    must_have = (
        people,
        operating_model_areas,
        transfer_requirements,
        capabilities,
        person_capabilities,
        capability_evidence,
        sessions,
        findings,
        validations,
        knowledge_items,
        recommendations,
    )
    for engagement_id in engagement_ids:
        for table in must_have:
            assert _count(conn, table, engagement_id) > 0, (
                f"{table.name} is empty for {engagement_id}"
            )


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------


def test_sqlite_finds_no_foreign_key_violations(conn) -> None:
    assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []


def test_foreign_keys_stay_inside_their_own_engagement(conn, engagement_ids) -> None:
    """A FK that resolves is not enough: it must resolve within the scope.

    SQLite enforces the reference, not the scope, so a content row could point
    at a perfectly valid row belonging to the *other* engagement and the
    database would accept it. Nothing but this check would notice.
    """
    inspector = inspect(conn.engine)
    for table in CONTENT_TABLES:
        for fk in inspector.get_foreign_keys(table.name):
            target = fk["referred_table"]
            if target == "engagements":
                continue
            column = fk["constrained_columns"][0]
            referred = fk["referred_columns"][0]
            other = metadata.tables[target]
            mismatched = conn.execute(
                select(func.count())
                .select_from(
                    table.join(
                        other,
                        table.c[column] == other.c[referred],
                        isouter=False,
                    )
                )
                .where(table.c.engagement_id != other.c.engagement_id)
            ).scalar_one()
            assert mismatched == 0, (
                f"{table.name}.{column} crosses into another engagement"
            )


def test_no_orphaned_evidence_or_validations(conn) -> None:
    known_pc = {row.id for row in conn.execute(select(person_capabilities.c.id))}
    for row in conn.execute(select(capability_evidence.c.person_capability_id)):
        assert row[0] in known_pc

    known_findings = {row.id for row in conn.execute(select(findings.c.id))}
    for row in conn.execute(select(validations.c.finding_id)):
        assert row[0] in known_findings


def test_every_debrief_belongs_to_a_session_it_names(conn) -> None:
    session_ids = {row.id for row in conn.execute(select(sessions.c.id))}
    rows = list(conn.execute(select(debriefs)))
    assert rows
    for row in rows:
        assert row.session_id in session_ids
        assert row.role in {"expert", "learner"}
        assert row.questions, "a debrief with no questions is not a debrief"
        for item in row.questions:
            assert item["question"] and item["answer"]


def test_session_participants_are_people_in_the_same_engagement(conn, engagement_ids) -> None:
    for engagement_id in engagement_ids:
        scope = Scope(conn, engagement_id)
        known = {row.id for row in scope.rows(people)}
        for row in scope.rows(sessions):
            assert row.expert_id in known
            assert row.learner_ids
            assert set(row.learner_ids) <= known


def test_knowledge_exposure_lists_name_real_people(conn, engagement_ids) -> None:
    for engagement_id in engagement_ids:
        scope = Scope(conn, engagement_id)
        known = {row.id for row in scope.rows(people)}
        for row in scope.rows(knowledge_items):
            assert set(row.people_exposed) <= known


def test_area_owners_are_local(conn, engagement_ids) -> None:
    """An expert cannot be the local owner of an area. That is the whole problem."""
    for engagement_id in engagement_ids:
        scope = Scope(conn, engagement_id)
        role_of = {row.id: row.role for row in scope.rows(people)}
        for row in scope.rows(operating_model_areas):
            if row.local_owner_id is None:
                assert not row.owner_validated
                continue
            assert role_of[row.local_owner_id] != Role.EXPERT.value


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("table_name", "column", "enum"),
    [
        ("people", "role", Role),
        ("transfer_requirements", "kind", RequirementKind),
        ("transfer_requirements", "state", TransferState),
        ("sessions", "stage", SessionStage),
        ("findings", "kind", FindingKind),
        ("validations", "action", ValidationAction),
        ("knowledge_items", "type", KnowledgeType),
    ],
)
def test_every_enum_column_holds_only_frozen_values(conn, table_name, column, enum) -> None:
    permitted = {member.value for member in enum}
    table = metadata.tables[table_name]
    found = {row[0] for row in conn.execute(select(table.c[column]).distinct())}
    assert found, f"{table_name}.{column} is empty"
    assert found <= permitted, f"{found - permitted} is not in {enum.__name__}"


def test_levels_are_inside_the_scale(conn) -> None:
    rows = list(conn.execute(select(person_capabilities)))
    assert rows
    for row in rows:
        assert 0 <= row.level < len(CAPABILITY_LEVELS)
    for row in conn.execute(select(capability_evidence)):
        assert 0 <= row.level_at_time < len(CAPABILITY_LEVELS)


def test_criticality_is_on_its_stated_scale(conn) -> None:
    for row in conn.execute(select(capabilities)):
        assert 1 <= row.criticality <= 5


def test_finding_status_reflects_a_recorded_decision(conn) -> None:
    """Findings are AI output. Nothing may be `approved` without a validation."""
    decided = {
        row.finding_id: row.action for row in conn.execute(select(validations))
    }
    for row in conn.execute(select(findings)):
        if row.status == "pending":
            assert row.id not in decided
            continue
        action = decided[row.id]
        expected = "approved" if action == ValidationAction.APPROVE else action
        assert row.status == expected


def test_the_corpus_exercises_every_validation_action(conn) -> None:
    """A corpus where every finding was approved does not show the product."""
    found = {row[0] for row in conn.execute(select(validations.c.action).distinct())}
    assert found == {member.value for member in ValidationAction}


# ---------------------------------------------------------------------------
# Depth -- the primary engagement carries the demo
# ---------------------------------------------------------------------------


def test_primary_engagement_has_the_depth_the_demo_needs(conn, primary_id) -> None:
    assert _count(conn, people, primary_id) >= 4
    assert _count(conn, operating_model_areas, primary_id) == 9
    assert _count(conn, capabilities, primary_id) == 10
    assert _count(conn, sessions, primary_id) >= 4
    assert _count(conn, knowledge_items, primary_id) >= 18
    assert _count(conn, findings, primary_id) >= 8
    assert _count(conn, capability_evidence, primary_id) >= 40


def test_every_area_fills_all_eight_dimensions(conn, primary_id) -> None:
    """The operating-model page renders eight columns whether or not they are filled."""
    scope = Scope(conn, primary_id)
    rows = scope.rows(operating_model_areas)
    assert rows
    for row in rows:
        for column, _label in OM_DIMENSIONS:
            attribute = "capabilities_list" if column == "capabilities" else column
            value = getattr(row, attribute)
            assert isinstance(value, list) and value, (
                f"{row.id} has nothing under '{column}'"
            )


def test_every_capability_has_a_level_for_every_person_who_should_have_one(
    conn, primary_id
) -> None:
    """A passport with holes in it reads as unfinished, not as honest."""
    scope = Scope(conn, primary_id)
    capability_ids = {row.id for row in scope.rows(capabilities)}
    held: dict[str, set[str]] = {}
    for row in scope.rows(person_capabilities):
        held.setdefault(row.person_id, set()).add(row.capability_id)
    complete = [p for p, caps in held.items() if caps == capability_ids]
    assert len(complete) >= 4, "fewer than four people are scored on every capability"


def test_the_library_spans_every_knowledge_type(conn, primary_id) -> None:
    scope = Scope(conn, primary_id)
    found = {row.type for row in scope.rows(knowledge_items)}
    assert found == ALL_KNOWLEDGE_TYPES


def test_most_of_the_library_is_validated_but_not_all_of_it(conn, primary_id) -> None:
    scope = Scope(conn, primary_id)
    rows = scope.rows(knowledge_items)
    validated = [row for row in rows if row.validated]
    assert len(validated) >= 18
    assert len(validated) < len(rows), (
        "nothing is awaiting validation, which makes validation look automatic"
    )


def test_requirements_cover_every_kind_and_every_state(conn, primary_id) -> None:
    scope = Scope(conn, primary_id)
    rows = scope.rows(transfer_requirements)
    assert {row.kind for row in rows} == {member.value for member in RequirementKind}
    assert {row.state for row in rows} == {member.value for member in TransferState}


def test_the_flagship_session_is_ready_to_run(conn, primary_id) -> None:
    """One session sits at PREPARE with a brief and a transcript already loaded.

    The demo opens on it. Its debriefs and findings are deliberately absent --
    producing those live is the thing being demonstrated.
    """
    scope = Scope(conn, primary_id)
    pending = [
        row for row in scope.rows(sessions) if row.stage == SessionStage.PREPARE
    ]
    assert len(pending) == 1
    session = pending[0]

    assert session.transcript and len(session.transcript) > 2000
    assert session.notes
    assert session.brief
    for key in (
        "primary_target",
        "current_level",
        "todays_objective",
        "your_role",
        "ask_before_explaining",
        "watch_for",
        "knowledge_gap_to_explore",
    ):
        assert session.brief.get(key), f"brief is missing '{key}'"
    assert 1 <= len(session.brief["watch_for"]) <= 4

    assert not scope.rows(debriefs, debriefs.c.session_id == session.id)
    assert not scope.rows(findings, findings.c.session_id == session.id)


def test_past_sessions_produced_something(conn, primary_id) -> None:
    """A session list with no outcomes attached is worse than no session list."""
    scope = Scope(conn, primary_id)
    past = [row for row in scope.rows(sessions) if row.stage != SessionStage.PREPARE]
    assert len(past) >= 3
    for session in past:
        assert session.transcript and session.notes
        roles = {
            row.role for row in scope.rows(debriefs, debriefs.c.session_id == session.id)
        }
        assert roles == {"expert", "learner"}, f"{session.id} has {roles}"
        assert scope.rows(findings, findings.c.session_id == session.id)


# ---------------------------------------------------------------------------
# Provenance -- the product's central claim
# ---------------------------------------------------------------------------


def test_every_level_that_moved_cites_the_validation_that_moved_it(conn) -> None:
    validation_ids = {row.id for row in conn.execute(select(validations))}
    moved = [
        row
        for row in conn.execute(select(person_capabilities))
        if row.last_validation_id is not None
    ]
    assert moved, "no level in the corpus was earned; all of them were typed"
    for row in moved:
        assert row.last_validation_id in validation_ids


def test_a_promotion_leaves_evidence_behind(conn) -> None:
    """The trigger enforces the citation. Nothing enforces that it is genuine."""
    by_validation = {
        row.id: row
        for row in conn.execute(select(validations))
        if row.person_capability_id is not None
    }
    assert by_validation
    for row in conn.execute(select(person_capabilities)):
        if row.last_validation_id is None:
            continue
        validation = by_validation[row.last_validation_id]
        assert validation.person_capability_id == row.id
        evidence = conn.execute(
            select(func.count())
            .select_from(capability_evidence)
            .where(capability_evidence.c.person_capability_id == row.id)
        ).scalar_one()
        assert evidence > 0


def test_evidence_never_claims_a_level_above_the_one_held(conn) -> None:
    level_of = {row.id: row.level for row in conn.execute(select(person_capabilities))}
    for row in conn.execute(select(capability_evidence)):
        assert row.level_at_time <= level_of[row.person_capability_id]


def test_exposure_counts_are_at_least_the_evidence_on_file(conn) -> None:
    """Most exposures never get written up; none of them get written up twice."""
    counted: dict[str, int] = {}
    for row in conn.execute(select(capability_evidence)):
        counted[row.person_capability_id] = counted.get(row.person_capability_id, 0) + 1
    for row in conn.execute(select(person_capabilities)):
        assert row.exposure_count >= counted.get(row.id, 0)


def test_recommendations_name_someone_who_can_act_on_them(conn, engagement_ids) -> None:
    for engagement_id in engagement_ids:
        scope = Scope(conn, engagement_id)
        local = {
            row.id
            for row in scope.rows(people)
            if row.role != Role.EXPERT.value
        }
        rows = scope.rows(recommendations)
        assert rows
        for row in rows:
            assert row.person_id in local
            assert row.objective and row.recommended_experience
            assert row.learner_responsibilities


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------


def test_the_departing_expert_leaves_on_schedule(conn, primary_id) -> None:
    scope = Scope(conn, primary_id)
    experts = [row for row in scope.rows(people) if row.role == Role.EXPERT.value]
    assert len(experts) == 1
    assert (experts[0].departure_date - ANCHOR).days == TARGET_DAYS_TO_DEPARTURE


def test_the_assignment_runs_about_nine_months(conn, primary_id) -> None:
    row = conn.execute(
        select(engagements).where(engagements.c.id == primary_id)
    ).one()
    span = (row.ends_on - row.started_on).days
    assert 250 <= span <= 300
    assert row.ends_on == ANCHOR + timedelta(days=TARGET_DAYS_TO_DEPARTURE)


def test_nothing_happened_after_today_or_before_the_assignment_began(
    conn, primary_id
) -> None:
    row = conn.execute(
        select(engagements).where(engagements.c.id == primary_id)
    ).one()
    scope = Scope(conn, primary_id)
    dated = (
        [s.held_on for s in scope.rows(sessions)]
        + [e.observed_on for e in scope.rows(capability_evidence)]
        + [k.captured_on for k in scope.rows(knowledge_items)]
        + [
            pc.last_demonstrated
            for pc in scope.rows(person_capabilities)
            if pc.last_demonstrated is not None
        ]
    )
    assert dated
    for when in dated:
        assert row.started_on <= when <= ANCHOR, when


def test_the_history_is_uneven(conn, primary_id) -> None:
    """Evenly spaced dates read as generated, because they are."""
    scope = Scope(conn, primary_id)
    days = sorted({(ANCHOR - row.observed_on).days for row in scope.rows(capability_evidence)})
    gaps = {b - a for a, b in zip(days, days[1:])}
    assert len(gaps) > 6, "evidence dates fall on a regular interval"


# ---------------------------------------------------------------------------
# The acceptance numbers, computed by the engine that will render them
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def primary_metrics(conn, primary_id):
    snapshot = readiness_snapshot(Scope(conn, primary_id), as_of=ANCHOR)
    return all_metrics(snapshot), snapshot


def test_readiness_lands_on_the_number_the_demo_opens_with(primary_metrics) -> None:
    metrics, _ = primary_metrics
    assert percent(metrics["operating_model_readiness"].value) == TARGET_READINESS_PCT


def test_capability_localization_hits_its_target(primary_metrics) -> None:
    metrics, _ = primary_metrics
    assert percent(metrics["capability_localization"].value) == TARGET_LOCALIZATION_PCT


def test_teachable_and_expert_dependent_counts(primary_metrics) -> None:
    metrics, _ = primary_metrics
    assert metrics["locally_teachable"].value == TARGET_TEACHABLE
    assert metrics["expert_dependent"].value == TARGET_EXPERT_DEPENDENT


def test_days_until_departure_is_read_from_the_corpus(primary_metrics) -> None:
    metrics, _ = primary_metrics
    assert metrics["days_until_departure"].value == TARGET_DAYS_TO_DEPARTURE


def test_no_component_is_saturated_or_empty(primary_metrics) -> None:
    """A component at 0% or 100% tells the audience nothing and hides a bug."""
    metrics, _ = primary_metrics
    for key in (
        "local_ownership",
        "capability_localization",
        "formal_transfer",
        "informal_transfer",
        "trainer_coverage",
    ):
        value = metrics[key].value
        assert 0.0 < value < 1.0, f"{key} is {value}"


def test_the_informal_half_scores_below_the_formal_half(primary_metrics) -> None:
    """The product's argument in one inequality. If it inverts, the corpus is lying."""
    metrics, _ = primary_metrics
    assert metrics["informal_transfer"].value < metrics["formal_transfer"].value


def test_one_validation_still_moves_the_number(primary_metrics) -> None:
    """The demo's closing beat: approving one finding visibly moves readiness.

    Simulated against the snapshot rather than written to the database, so this
    asserts the corpus is *tuned* for the moment without consuming it.
    """
    from dataclasses import replace

    metrics, snapshot = primary_metrics
    before = percent(metrics["operating_model_readiness"].value)

    # The capability the flagship session is about: critical, not yet
    # localized, and with a local person one step below the threshold.
    localized = set(
        metrics["capability_localization"].inputs["localized_capabilities"].split(", ")
    )
    local_ids = {p.id for p in snapshot.people if p.is_local}
    candidates = [
        level
        for level in snapshot.levels
        if level.person_id in local_ids
        and level.level == LEVEL_INDEPENDENT - 1
        and level.capability_id not in localized
    ]
    assert candidates, "no capability is one validation away from localizing"

    promoted = candidates[0]
    after_levels = tuple(
        replace(level, level=LEVEL_INDEPENDENT) if level is promoted else level
        for level in snapshot.levels
    )
    after = percent(
        all_metrics(replace(snapshot, levels=after_levels))[
            "operating_model_readiness"
        ].value
    )
    assert after > before, "approving a finding leaves the headline unchanged"


def test_the_teachers_are_local_and_there_is_more_than_one(primary_metrics) -> None:
    metrics, snapshot = primary_metrics
    trainer_ids = set(metrics["local_trainers"].inputs["trainers"].split(", "))
    assert len(trainer_ids) >= 2, "a single teacher is a single point of failure"
    for person_id in trainer_ids:
        person = snapshot.person(person_id)
        assert person is not None and person.is_local


def test_expert_dependent_capabilities_really_are_expert_dependent(
    primary_metrics,
) -> None:
    metrics, snapshot = primary_metrics
    dependent = set(metrics["expert_dependent"].inputs["dependent_capabilities"].split(", "))
    assert len(dependent) == TARGET_EXPERT_DEPENDENT
    local_ids = {p.id for p in snapshot.people if p.is_local}
    expert_ids = {p.id for p in snapshot.people if not p.is_local}
    for capability_id in dependent:
        levels = [lv for lv in snapshot.levels if lv.capability_id == capability_id]
        assert max(
            (lv.level for lv in levels if lv.person_id in expert_ids), default=0
        ) >= LEVEL_INDEPENDENT
        assert max(
            (lv.level for lv in levels if lv.person_id in local_ids), default=0
        ) < LEVEL_INDEPENDENT


def test_nobody_local_is_at_the_top_of_a_capability_nobody_teaches(
    primary_metrics,
) -> None:
    """Teachable and trainer-coverage must agree, or one of them is miscounted."""
    metrics, snapshot = primary_metrics
    teachable = set(
        metrics["locally_teachable"].inputs["teachable_capabilities"].split(", ")
    )
    local_ids = {p.id for p in snapshot.people if p.is_local}
    at_top = {
        lv.capability_id
        for lv in snapshot.levels
        if lv.person_id in local_ids and lv.level >= LEVEL_TEACHER
    }
    assert at_top == teachable


# ---------------------------------------------------------------------------
# The secondary engagement
# ---------------------------------------------------------------------------


def test_the_second_engagement_is_thin_but_complete(conn, primary_id, engagement_ids) -> None:
    other = next(i for i in engagement_ids if i != primary_id)
    assert _count(conn, capabilities, other) < _count(conn, capabilities, primary_id)
    assert _count(conn, knowledge_items, other) < _count(conn, knowledge_items, primary_id)
    snapshot = readiness_snapshot(Scope(conn, other), as_of=ANCHOR)
    metrics = all_metrics(snapshot)
    assert 0 < metrics["operating_model_readiness"].value < 1


def test_the_second_engagement_tunes_its_own_weights(conn, primary_id, engagement_ids) -> None:
    """Weights are per-engagement data. Nothing proves that like two of them."""
    other = next(i for i in engagement_ids if i != primary_id)
    stored = {
        row.id: row.readiness_weights for row in conn.execute(select(engagements))
    }
    assert stored[primary_id] and stored[other]
    assert stored[primary_id] != stored[other]
    for weights in stored.values():
        assert sum(weights.values()) == pytest.approx(1.0)


def test_the_second_expert_is_not_leaving_at_the_same_time(conn, engagement_ids) -> None:
    departures = {
        row.engagement_id: row.departure_date
        for row in conn.execute(select(people))
        if row.role == Role.EXPERT.value
    }
    assert len(set(departures.values())) == len(engagement_ids)
