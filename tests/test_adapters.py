"""The seam between the database and the two pure engines.

B2 and B4 are tested against literals, which is what makes them fast and
trustworthy -- and also means neither suite would notice if the adapter handed
them the wrong column. These tests close that gap: they build real rows, run
them through `app.db.adapters`, and assert on what the engines produce.

The end-to-end cases matter more than the field-by-field ones. A snapshot that
merely has the right shape can still be scored wrong.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import insert

from app.ai.context import SessionContext
from app.db.adapters import (
    CRITICAL_CRITICALITY,
    AdapterError,
    readiness_snapshot,
    session_context,
)
from app.db.connection import connect, get_engine
from app.db.schema import (
    capabilities,
    debriefs,
    engagements,
    findings,
    knowledge_items,
    metadata,
    operating_model_areas,
    people,
    person_capabilities,
    sessions,
    transfer_requirements,
)
from app.db.scoped import Scope
from app.db.writes import apply_validation
from app.readiness import operating_model_readiness
from app.readiness.weights import DEFAULT_WEIGHTS

from contracts.vocabulary import Role

ENG_A = "eng-a"
ENG_B = "eng-b"
AS_OF = date(2026, 6, 1)


@pytest.fixture
def scope(tmp_path):
    """One engagement with enough shape to score, plus a second to leak from."""
    engine = get_engine(str(tmp_path / "a.db"))
    metadata.create_all(engine)

    with connect(engine) as conn:
        for eid, name in ((ENG_A, "Alpha Transfer"), (ENG_B, "Beta Transfer")):
            conn.execute(
                insert(engagements).values(
                    id=eid, name=name, org=f"{name} Authority",
                    sector="utilities", location="Region One",
                    mission="Operate without external support.",
                    started_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
                    readiness_weights={}, is_primary=(eid == ENG_A),
                )
            )

        s = Scope(conn, ENG_A)
        s.insert(people, id="ex", name="An Expert", title="Lead",
                 role=Role.EXPERT.value, departure_date=date(2026, 9, 1))
        s.insert(people, id="lo", name="A Counterpart", title="Operator",
                 role=Role.COUNTERPART.value)

        s.insert(operating_model_areas, id="ar1", name="An Area",
                 summary="Something the site runs.", local_owner_id="lo",
                 owner_validated=True, critical=True, formal_pct=60)

        s.insert(capabilities, id="c1", name="A Critical Capability",
                 description="Needed locally.", criticality=5, area_id="ar1")
        s.insert(capabilities, id="c2", name="A Minor Capability",
                 description="Nice to have.", criticality=1, area_id="ar1")

        s.insert(person_capabilities, id="pc1", person_id="lo",
                 capability_id="c1", level=3, exposure_count=2,
                 last_demonstrated=date(2026, 5, 1))

        s.insert(transfer_requirements, id="r1", area_id="ar1", kind="formal",
                 label="A written procedure", description="Write it down.",
                 state="complete", validated=True, capability_id="c1")
        s.insert(transfer_requirements, id="r2", area_id="ar1", kind="tacit",
                 label="The judgment call", description="Hard to write down.",
                 state="partial", validated=False, capability_id="c1")

        s.insert(knowledge_items, id="k1", title="A Heuristic",
                 type="heuristic", summary="A rule of thumb.", body={},
                 area_id="ar1", capability_id="c1", expert_id="ex",
                 validated=True, people_exposed=["lo"],
                 captured_on=date(2026, 4, 1))

        s.insert(sessions, id="s1", title="An Earlier Session",
                 held_on=date(2026, 5, 1), stage="synthesis", expert_id="ex",
                 learner_ids=["lo"], area_id="ar1", capability_id="c1")
        s.insert(sessions, id="s2", title="The Session Under Test",
                 held_on=date(2026, 6, 1), stage="synthesis", expert_id="ex",
                 learner_ids=["lo"], area_id="ar1", capability_id="c1",
                 transcript="A transcript.", notes="Some notes.")

        yield s


# ---------------------------------------------------------------------------
# Readiness snapshot
# ---------------------------------------------------------------------------


def test_snapshot_feeds_the_readiness_engine(scope) -> None:
    """The case that actually matters: rows in, a scored number out."""
    metric = operating_model_readiness(readiness_snapshot(scope, as_of=AS_OF))

    assert 0.0 <= metric.value <= 1.0
    assert metric.formula, "a score with no formula is the unexplained number"
    assert metric.inputs, "the popover has nothing to show"


def test_criticality_becomes_a_boolean_at_the_documented_line(scope) -> None:
    snap = readiness_snapshot(scope, as_of=AS_OF)
    critical = {c.id for c in snap.capabilities if c.critical}

    assert critical == {"c1"}, (
        f"criticality >= {CRITICAL_CRITICALITY} is the line; c2 scores 1"
    )


def test_areas_collect_their_capabilities(scope) -> None:
    area = readiness_snapshot(scope, as_of=AS_OF).area("ar1")
    assert area is not None
    assert area.capability_ids == ("c1", "c2")
    assert area.owner_validated is True


def test_requirement_validation_is_carried_not_inferred(scope) -> None:
    reqs = {r.id: r for r in readiness_snapshot(scope, as_of=AS_OF).requirements}
    assert reqs["r1"].validated is True
    assert reqs["r2"].validated is False, (
        "a partial informal requirement must not arrive pre-validated"
    )


def test_evidence_count_comes_from_rows_not_the_exposure_counter(scope) -> None:
    """`exposures` and `evidence_count` are different numbers and must stay so."""
    snap = readiness_snapshot(scope, as_of=AS_OF)
    level = next(lv for lv in snap.levels if lv.person_id == "lo")

    assert level.exposures == 2
    assert level.evidence_count == 0, "no evidence rows were written"


def test_weights_default_when_the_engagement_has_not_tuned_them(scope) -> None:
    assert readiness_snapshot(scope, as_of=AS_OF).weights is None


def test_stored_weights_are_read_back(scope) -> None:
    tuned = {"local_ownership": 0.20, "capability_localization": 0.35,
             "formal_transfer": 0.15, "informal_transfer": 0.20,
             "trainer_coverage": 0.10}
    scope.conn.execute(
        engagements.update()
        .where(engagements.c.id == ENG_A)
        .values(readiness_weights=tuned)
    )
    weights = readiness_snapshot(scope, as_of=AS_OF).weights

    assert weights is not None
    assert weights.capability_localization == 0.35
    assert weights != DEFAULT_WEIGHTS


def test_weights_that_do_not_sum_to_one_fail_at_the_adapter(scope) -> None:
    """Better here than three screens later as a score that cannot reach 100%."""
    scope.conn.execute(
        engagements.update()
        .where(engagements.c.id == ENG_A)
        .values(readiness_weights={"local_ownership": 0.9,
                                   "capability_localization": 0.9,
                                   "formal_transfer": 0.15,
                                   "informal_transfer": 0.20,
                                   "trainer_coverage": 0.10})
    )
    with pytest.raises(ValueError, match="sum to 1.0"):
        readiness_snapshot(scope, as_of=AS_OF)


def test_snapshot_never_crosses_engagements(scope) -> None:
    """Section 0.5, asserted through the adapter rather than trusted."""
    other = Scope(scope.conn, ENG_B)
    other.insert(people, id="elsewhere", name="Someone Else", title="T",
                 role=Role.COUNTERPART.value)
    other.insert(capabilities, id="c-else", name="Another Capability",
                 description="Not ours.", criticality=5)

    snap = readiness_snapshot(scope, as_of=AS_OF)

    assert "elsewhere" not in {p.id for p in snap.people}
    assert "c-else" not in {c.id for c in snap.capabilities}
    assert snap.engagement_id == ENG_A


def test_snapshot_refuses_an_engagement_that_does_not_exist(scope) -> None:
    with pytest.raises(AdapterError, match="no engagement"):
        readiness_snapshot(Scope(scope.conn, "eng-nope"), as_of=AS_OF)


# ---------------------------------------------------------------------------
# Session context
# ---------------------------------------------------------------------------


def test_session_context_is_a_valid_ai_input(scope) -> None:
    ctx = session_context(scope, "s2", as_of=AS_OF)

    assert isinstance(ctx, SessionContext)
    assert ctx.engagement.name == "Alpha Transfer"
    assert ctx.expert.name == "An Expert"
    assert [p.name for p in ctx.learners] == ["A Counterpart"]
    assert ctx.area == "An Area"
    assert ctx.transcript == "A transcript."


def test_days_until_departure_is_derived_from_as_of_not_the_clock(scope) -> None:
    """A rehearsal on Tuesday and a demo on Wednesday must agree."""
    early = session_context(scope, "s2", as_of=date(2026, 6, 1))
    late = session_context(scope, "s2", as_of=date(2026, 8, 1))

    assert early.engagement.days_until_departure == 92
    assert late.engagement.days_until_departure == 31


def test_capability_states_cover_the_learners(scope) -> None:
    states = session_context(scope, "s2", as_of=AS_OF).capabilities

    assert len(states) == 1
    assert states[0].person == "A Counterpart"
    assert states[0].level == 3
    assert states[0].capability == "A Critical Capability"
    assert states[0].last_demonstrated == "2026-05-01"


def test_formal_rules_and_open_gaps_split_the_requirements(scope) -> None:
    ctx = session_context(scope, "s2", as_of=AS_OF)

    assert ctx.formal_rules == ["A written procedure"]
    assert ctx.open_gaps == ["The judgment call"], (
        "only the incomplete requirement is an open gap"
    )


def test_prior_sessions_are_earlier_ones_on_the_same_area(scope) -> None:
    ctx = session_context(scope, "s2", as_of=AS_OF)
    assert ctx.prior_sessions == ["An Earlier Session"]
    assert "The Session Under Test" not in ctx.prior_sessions


def test_debriefs_keep_unanswered_questions(scope) -> None:
    """'Asked and unanswered' is not the same as 'never asked'."""
    scope.insert(debriefs, id="d1", session_id="s2", role="expert",
                 person_id="ex", questions=[
                     {"id": "q1", "question": "What did you notice?",
                      "answer": "They hesitated."},
                     {"id": "q2", "question": "What would you change?"},
                 ])
    ctx = session_context(scope, "s2", as_of=AS_OF)

    assert len(ctx.expert_debrief) == 2
    assert ctx.expert_debrief[0].answer == "They hesitated."
    assert ctx.expert_debrief[1].answer is None
    assert ctx.learner_debrief == []


def test_session_context_refuses_a_session_from_another_engagement(scope) -> None:
    other = Scope(scope.conn, ENG_B)
    other.insert(people, id="ex-b", name="Another Expert", title="Lead",
                 role=Role.EXPERT.value)
    other.insert(sessions, id="s-b", title="Not Ours", held_on=date(2026, 6, 1),
                 stage="prepare", expert_id="ex-b", learner_ids=[])

    with pytest.raises(AdapterError, match="no session"):
        session_context(scope, "s-b", as_of=AS_OF)


# ---------------------------------------------------------------------------
# The claim the demo makes
# ---------------------------------------------------------------------------


def test_readiness_moves_when_a_finding_is_validated(scope) -> None:
    """SYNC-3's gate, exercised through the adapter.

    This is the whole product in one test: the AI proposes, a human approves,
    the level moves, and the number on screen changes *because* the rows did.
    If this passes, the demo's closing claim is earned rather than asserted.
    """
    before = operating_model_readiness(readiness_snapshot(scope, as_of=AS_OF)).value

    scope.insert(findings, id="f1", session_id="s2", kind="capability_evidence",
                 title="Ran the decision unaided", body={"suggested_level": 4},
                 confidence="high", evidence_sources=["transcript"],
                 rationale="Reasoning was volunteered unprompted.",
                 impact="Operations", risk_if_untransferred="Decisions escalate.",
                 status="pending")
    apply_validation(scope, finding_id="f1", validated_by_id="ex",
                     action="approve", person_capability_id="pc1", new_level=4,
                     evidence_summary="Reached the decision independently.",
                     evidence_source="transcript 04:12-06:40",
                     observed_on=date(2026, 6, 1))

    after_snap = readiness_snapshot(scope, as_of=AS_OF)
    after = operating_model_readiness(after_snap).value

    assert after > before, "approving a level change must move the score"
    level = next(lv for lv in after_snap.levels if lv.person_id == "lo")
    assert level.level == 4
    assert level.evidence_count == 1, "the evidence row must reach the engine"
