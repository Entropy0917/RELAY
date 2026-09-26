"""The invariants either bite or they are decoration.

Each test here tries to do the forbidden thing directly against the database,
bypassing the application layer entirely. That is the point: an invariant that
only holds when callers are careful is not an invariant.
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from sqlalchemy import insert, text, update

from app.db.connection import connect, get_engine
from app.db.schema import (
    CONTENT_TABLES,
    capabilities,
    capability_evidence,
    engagements,
    findings,
    metadata,
    people,
    person_capabilities,
    sessions,
)
from app.db.scoped import Scope, UnscopedQuery, list_engagements
from app.db.writes import ValidationRefused, apply_validation, append_evidence

ENG_A = "eng-a"
ENG_B = "eng-b"


@pytest.fixture
def engine(tmp_path):
    eng = get_engine(str(tmp_path / "t.db"))
    metadata.create_all(eng)
    return eng


@pytest.fixture
def scope(engine):
    """Two engagements, so cross-engagement leakage is detectable."""
    with connect(engine) as conn:
        for eid, name in ((ENG_A, "Alpha Transfer"), (ENG_B, "Beta Transfer")):
            conn.execute(
                insert(engagements).values(
                    id=eid, name=name, org=f"{name} Authority", sector="utilities",
                    location="Region One", mission="Operate without external support.",
                    started_on=date(2026, 1, 1), ends_on=date(2026, 12, 31),
                    readiness_weights={}, is_primary=(eid == ENG_A),
                )
            )
        s = Scope(conn, ENG_A)
        s.insert(people, id="p1", name="A Person", title="Operator", role="counterpart")
        s.insert(people, id="p2", name="B Person", title="Lead", role="expert")
        s.insert(capabilities, id="c1", name="A Capability",
                 description="Something the site must be able to do.", criticality=5)
        s.insert(person_capabilities, id="pc1", person_id="p1",
                 capability_id="c1", level=3, exposure_count=2)
        s.insert(sessions, id="s1", title="A Session", held_on=date(2026, 6, 1),
                 stage="synthesis", expert_id="p2", learner_ids=["p1"])
        s.insert(findings, id="f1", session_id="s1", kind="capability_evidence",
                 title="Evidence for a capability", body={"suggested_level": 4},
                 confidence="high", evidence_sources=["transcript"],
                 rationale="Reasoning was volunteered unprompted.",
                 impact="Operations", risk_if_untransferred="Decisions escalate.",
                 status="pending")
        yield s


# --------------------------------------------------------------------------
# Section 0.5 -- engagement scoping
# --------------------------------------------------------------------------


@pytest.mark.parametrize("table", CONTENT_TABLES, ids=lambda t: t.name)
def test_every_content_table_is_engagement_scoped(table) -> None:
    assert "engagement_id" in table.c, (
        f"'{table.name}' has no engagement_id. Every content table needs one "
        f"or two engagements can bleed into each other (section 0.5)."
    )


def test_scope_refuses_to_write_into_another_engagement(scope) -> None:
    with pytest.raises(UnscopedQuery):
        scope.insert(people, id="px", name="X", title="T",
                     role="counterpart", engagement_id=ENG_B)


def test_scope_reads_do_not_cross_engagements(engine, scope) -> None:
    other = Scope(scope.conn, ENG_B)
    other.insert(people, id="p9", name="Elsewhere", title="T", role="counterpart")

    assert {r.id for r in scope.rows(people)} == {"p1", "p2"}
    assert {r.id for r in other.rows(people)} == {"p9"}
    assert scope.by_id(people, "p9") is None, "read crossed an engagement boundary"


def test_engagement_switcher_sees_every_engagement(scope) -> None:
    assert len(list_engagements(scope.conn)) == 2


# --------------------------------------------------------------------------
# Invariant 1 -- AI never certifies anyone
# --------------------------------------------------------------------------


def test_raw_level_update_is_rejected(scope) -> None:
    """The blunt attack: move the level with a plain UPDATE."""
    with pytest.raises(Exception, match="approved validation"):
        scope.conn.execute(
            update(person_capabilities)
            .where(person_capabilities.c.id == "pc1")
            .values(level=6)
        )


def test_level_update_citing_a_nonexistent_validation_is_rejected(scope) -> None:
    with pytest.raises(Exception, match="approved validation"):
        scope.conn.execute(
            update(person_capabilities)
            .where(person_capabilities.c.id == "pc1")
            .values(level=5, last_validation_id="val-invented")
        )


def test_rejecting_a_finding_never_moves_a_level(scope) -> None:
    apply_validation(scope, finding_id="f1", validated_by_id="p2",
                     action="reject", person_capability_id="pc1")
    assert scope.by_id(person_capabilities, "pc1").level == 3
    assert scope.by_id(findings, "f1").status == "reject"


def test_approved_validation_moves_the_level_and_leaves_evidence(scope) -> None:
    apply_validation(
        scope, finding_id="f1", validated_by_id="p2", action="approve",
        person_capability_id="pc1", new_level=4,
        evidence_summary="Reached the decision independently.",
        evidence_source="transcript 04:12-06:40", observed_on=date(2026, 6, 1),
    )
    pc = scope.by_id(person_capabilities, "pc1")
    assert pc.level == 4
    assert pc.exposure_count == 3
    assert pc.last_validation_id is not None

    evidence = scope.rows(
        capability_evidence, capability_evidence.c.person_capability_id == "pc1"
    )
    assert len(evidence) == 1
    assert evidence[0].level_at_time == 4
    assert scope.by_id(findings, "f1").status == "approved"


def test_a_validation_cannot_be_spent_twice(scope) -> None:
    """Replay protection: one authorisation, one level change."""
    apply_validation(scope, finding_id="f1", validated_by_id="p2",
                     action="approve", person_capability_id="pc1", new_level=4)
    spent = scope.by_id(person_capabilities, "pc1").last_validation_id

    with pytest.raises(Exception, match="approved validation"):
        scope.conn.execute(
            update(person_capabilities)
            .where(person_capabilities.c.id == "pc1")
            .values(level=6, last_validation_id=spent)
        )


def test_a_finding_is_not_decided_twice(scope) -> None:
    apply_validation(scope, finding_id="f1", validated_by_id="p2", action="approve",
                     person_capability_id="pc1", new_level=4)
    with pytest.raises(ValidationRefused, match="already"):
        apply_validation(scope, finding_id="f1", validated_by_id="p2",
                         action="approve", person_capability_id="pc1", new_level=5)


def test_level_outside_the_scale_is_refused(scope) -> None:
    with pytest.raises(ValidationRefused, match="0\\.\\.6"):
        apply_validation(scope, finding_id="f1", validated_by_id="p2",
                         action="approve", person_capability_id="pc1", new_level=7)


# --------------------------------------------------------------------------
# Invariant 2 -- evidence is append-only
# --------------------------------------------------------------------------


def test_evidence_cannot_be_updated(scope) -> None:
    append_evidence(scope, person_capability_id="pc1",
                    summary="Observed a full cycle.", source="session notes")
    with pytest.raises(Exception, match="append-only"):
        scope.conn.execute(
            update(capability_evidence).values(summary="rewritten")
        )


def test_evidence_cannot_be_deleted(scope) -> None:
    append_evidence(scope, person_capability_id="pc1",
                    summary="Observed a full cycle.", source="session notes")
    with pytest.raises(Exception, match="append-only"):
        scope.conn.execute(text("DELETE FROM capability_evidence"))


def test_appending_evidence_does_not_move_the_level(scope) -> None:
    append_evidence(scope, person_capability_id="pc1",
                    summary="Observed a full cycle.", source="session notes")
    pc = scope.by_id(person_capabilities, "pc1")
    assert pc.level == 3
    assert pc.exposure_count == 3


# --------------------------------------------------------------------------
# Invariant 3 -- nothing about readiness is stored
# --------------------------------------------------------------------------


def test_no_readiness_is_ever_persisted() -> None:
    """Every number is derived at read time, so there is nothing to go stale."""
    banned = re.compile(r"readiness|_score|score_|percent_complete", re.IGNORECASE)
    offenders = [
        f"{t.name}.{c.name}"
        for t in metadata.tables.values()
        for c in t.c
        # weights are inputs to the formula, not a stored result
        if banned.search(c.name) and c.name != "readiness_weights"
    ]
    assert not offenders, f"stored readiness columns: {offenders}"


# --------------------------------------------------------------------------
# reset.py
# --------------------------------------------------------------------------


def test_reset_preserves_the_ai_cache(tmp_path, monkeypatch) -> None:
    """A reset must not cost a warm demo (section 9)."""
    monkeypatch.setenv("RELAY_DB", str(tmp_path / "r.db"))
    from app.db import connection
    from scripts.reset import reset

    connection.reset_engine()
    reset(seed=False, verbose=False)

    with connect(connection.get_engine()) as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS ai_cache (k TEXT, v TEXT)"))
        conn.execute(text("INSERT INTO ai_cache VALUES ('warm', '{}')"))
        conn.execute(insert(engagements).values(
            id="tmp", name="Temp", org="Temp", sector="s", location="l",
            mission="m", started_on=date(2026, 1, 1), ends_on=date(2026, 2, 1),
            readiness_weights={}, is_primary=True,
        ))

    reset(seed=False, verbose=False)

    with connect(connection.get_engine()) as conn:
        cached = conn.execute(text("SELECT count(*) FROM ai_cache")).scalar()
        rows = conn.execute(text("SELECT count(*) FROM engagements")).scalar()
    connection.reset_engine()

    assert cached == 1, "reset destroyed the AI cache"
    assert rows == 0, "reset did not clear engagement data"
