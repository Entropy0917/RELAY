"""Tests for the session loop — B6.

These test the service layer directly against a seeded database, not against
literals the test chose.  Asserts shape and behavior, not content.

Does not reference any demo engagement content (section 0.5).  Session IDs
are read back from the database rather than hardcoded.
"""

from __future__ import annotations

import os
from datetime import date
from unittest.mock import patch

import pytest

from app.db.connection import connect, get_engine
from app.db.schema import (
    capabilities,
    debriefs,
    findings,
    metadata,
    people,
    person_capabilities,
    sessions,
    validations,
)
from app.db.scoped import Scope, primary_engagement
from app.services.session import (
    StageError,
    advance_stage,
    get_stage_vm,
    list_sessions,
    synthesize,
    validate_finding,
)
from contracts.vocabulary import (
    FindingKind,
    SessionStage,
    STAGE_ORDER,
    ValidationAction,
)

ANCHOR = date(2026, 3, 2)
os.environ.setdefault("RELAY_SEED_TODAY", ANCHOR.isoformat())

from seed import load_all  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    """One loaded corpus, shared. Loading is ~200ms; doing it per test is waste."""
    engine = get_engine(str(tmp_path_factory.mktemp("session") / "loop.db"))
    metadata.create_all(engine)
    load_all(engine)
    return engine


@pytest.fixture(scope="module")
def conn(seeded):
    with connect(seeded) as connection:
        yield connection


@pytest.fixture(scope="module")
def primary_id(conn) -> str:
    return primary_engagement(conn).id


@pytest.fixture(scope="module")
def prepare_session_id(conn, primary_id) -> str:
    """Find a session at PREPARE stage with a transcript (the demo session)."""
    scope = Scope(conn, primary_id)
    for row in scope.rows(sessions):
        if row.stage == "prepare" and row.transcript:
            return row.id
    pytest.skip("no session at prepare with transcript in seed")


def _make_shell():
    """Minimal shell for tests that need a ShellVM."""
    from contracts.viewmodels import ShellVM, NavItem, EngagementRef, PersonRef
    from contracts.vocabulary import Role
    return ShellVM(
        nav=[NavItem(key="overview", label="Overview", href="/", active=False)],
        engagements=[EngagementRef(id="e", name="Test", org="Org")],
        current_engagement=EngagementRef(id="e", name="Test", org="Org"),
        personas=[PersonRef(id="p", name="T", title="T", role=Role.EXPERT, initials="T")],
        current_persona=PersonRef(id="p", name="T", title="T", role=Role.EXPERT, initials="T"),
    )


# ---------------------------------------------------------------------------
# Session list
# ---------------------------------------------------------------------------

class TestSessionList:

    def test_list_returns_sessions(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = list_sessions(scope)
        total = len(data["upcoming"]) + len(data["past"])
        assert total > 0, "seeded database must have sessions"

    def test_prepare_session_is_upcoming(self, conn, primary_id, prepare_session_id):
        scope = Scope(conn, primary_id)
        data = list_sessions(scope)
        ids = [s.id for s in data["upcoming"]]
        assert prepare_session_id in ids


# ---------------------------------------------------------------------------
# State machine — order enforcement
# ---------------------------------------------------------------------------

class TestStageOrder:

    def test_advance_from_wrong_stage_raises(self, conn, primary_id, prepare_session_id):
        """Cannot advance from CAPTURE when session is at PREPARE."""
        scope = Scope(conn, primary_id)
        session = scope.by_id(sessions, prepare_session_id)
        assert session is not None
        assert session.stage == "prepare"

        with pytest.raises(StageError, match="cannot advance"):
            advance_stage(
                scope, prepare_session_id, SessionStage.CAPTURE,
                as_of=ANCHOR,
            )


# ---------------------------------------------------------------------------
# Persona gating
# ---------------------------------------------------------------------------

class TestPersonaGating:

    def test_expert_debrief_blocks_learner(self, seeded, primary_id, prepare_session_id):
        """A learner viewing the expert debrief has can_act=False."""
        with connect(seeded) as conn:
            scope = Scope(conn, primary_id)
            session = scope.by_id(sessions, prepare_session_id)
            learner_ids = list(session.learner_ids or ())
            if not learner_ids:
                pytest.skip("no learners on this session")

            # Temporarily move to expert_debrief
            scope.update(sessions, prepare_session_id, stage="expert_debrief")

            shell = _make_shell()
            vm = get_stage_vm(
                scope, prepare_session_id, SessionStage.EXPERT_DEBRIEF, shell,
                persona_id=learner_ids[0],
            )
            assert not vm.can_act
            assert vm.blocked_reason is not None

            # Restore
            scope.update(sessions, prepare_session_id, stage="prepare")

    def test_learner_debrief_blocks_expert(self, seeded, primary_id, prepare_session_id):
        """The expert viewing the learner debrief has can_act=False."""
        with connect(seeded) as conn:
            scope = Scope(conn, primary_id)
            session = scope.by_id(sessions, prepare_session_id)
            expert_id = session.expert_id

            scope.update(sessions, prepare_session_id, stage="learner_debrief")

            shell = _make_shell()
            vm = get_stage_vm(
                scope, prepare_session_id, SessionStage.LEARNER_DEBRIEF, shell,
                persona_id=expert_id,
            )
            assert not vm.can_act

            scope.update(sessions, prepare_session_id, stage="prepare")


# ---------------------------------------------------------------------------
# Synthesis guard
# ---------------------------------------------------------------------------

class TestSynthesis:

    def test_synthesize_wrong_stage_raises(self, conn, primary_id, prepare_session_id):
        """Synthesis refuses to run unless session is at SYNTHESIS stage."""
        scope = Scope(conn, primary_id)
        with pytest.raises(StageError, match="synthesis requires"):
            synthesize(scope, prepare_session_id, as_of=ANCHOR)


# ---------------------------------------------------------------------------
# Validation — the central safety claim
# ---------------------------------------------------------------------------

class TestValidation:

    def test_rejected_finding_never_moves_level(self, seeded, primary_id, prepare_session_id):
        """A rejected finding leaves person_capabilities.level untouched."""
        with connect(seeded) as conn:
            scope = Scope(conn, primary_id)
            session = scope.by_id(sessions, prepare_session_id)
            expert_id = session.expert_id

            # Record levels before
            pc_before = {
                (r.person_id, r.capability_id): r.level
                for r in scope.rows(person_capabilities)
            }

            # Insert a fake pending finding
            scope.insert(
                findings,
                id="fnd-test-reject",
                session_id=prepare_session_id,
                kind="capability_evidence",
                title="Test Rejection",
                body={
                    "person": "nobody",
                    "capability": "nothing",
                    "current_level": 3,
                    "suggested_level": 4,
                },
                confidence="medium",
                evidence_sources=["test"],
                rationale="test",
                impact="test",
                risk_if_untransferred="test",
                status="pending",
            )

            vm = validate_finding(
                scope, prepare_session_id, "fnd-test-reject",
                ValidationAction.REJECT, expert_id,
                as_of=ANCHOR,
            )

            # Finding is rejected
            rejected = scope.by_id(findings, "fnd-test-reject")
            assert rejected.status == "reject"

            # No level changed
            pc_after = {
                (r.person_id, r.capability_id): r.level
                for r in scope.rows(person_capabilities)
            }
            assert pc_before == pc_after


# ---------------------------------------------------------------------------
# AI error → 502, nothing saved
# ---------------------------------------------------------------------------

class TestAIErrorWrites:

    def test_ai_error_saves_nothing(self, tmp_path, primary_id, prepare_session_id):
        """An AIError during synthesis saves nothing to the database."""
        # Fresh engine so there are no leftover findings from other tests
        engine = get_engine(str(tmp_path / "ai_error.db"))
        metadata.create_all(engine)
        load_all(engine)

        with connect(engine) as conn:
            scope = Scope(conn, primary_id)
            scope.update(sessions, prepare_session_id, stage="synthesis")

            before = len(scope.rows(
                findings, findings.c.session_id == prepare_session_id
            ))

            from app.ai.errors import ProviderUnreachable
            with patch("app.services.session.analyze_session") as mock_ai:
                mock_ai.side_effect = ProviderUnreachable(
                    "ollama", "connection refused", fn_name="analyze_session"
                )
                with pytest.raises(ProviderUnreachable):
                    synthesize(scope, prepare_session_id, as_of=ANCHOR)

            after = len(scope.rows(
                findings, findings.c.session_id == prepare_session_id
            ))
            assert after == before


# ---------------------------------------------------------------------------
# Stage view
# ---------------------------------------------------------------------------

class TestStageView:

    def test_cannot_view_future_stage(self, conn, primary_id, prepare_session_id):
        """Viewing a stage beyond the session's current stage raises."""
        scope = Scope(conn, primary_id)
        shell = _make_shell()
        with pytest.raises(StageError, match="cannot view"):
            get_stage_vm(
                scope, prepare_session_id, SessionStage.VALIDATION, shell,
                as_of=ANCHOR,
            )

    def test_view_current_stage(self, conn, primary_id, prepare_session_id):
        """Viewing the current stage (PREPARE) works."""
        scope = Scope(conn, primary_id)
        shell = _make_shell()
        vm = get_stage_vm(
            scope, prepare_session_id, SessionStage.PREPARE, shell,
            as_of=ANCHOR,
        )
        assert vm.stage == SessionStage.PREPARE
        assert vm.session.id == prepare_session_id
        assert vm.transcript is not None, "demo session must have a transcript"

    def test_stepper_marks_current(self, conn, primary_id, prepare_session_id):
        """The stage stepper marks the current stage correctly."""
        scope = Scope(conn, primary_id)
        shell = _make_shell()
        vm = get_stage_vm(
            scope, prepare_session_id, SessionStage.PREPARE, shell,
            as_of=ANCHOR,
        )
        current_steps = [s for s in vm.stages if s["state"] == "current"]
        assert len(current_steps) == 1
        assert current_steps[0]["key"] == "prepare"
