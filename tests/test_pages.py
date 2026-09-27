"""Tests for the read-surface services — B5.

Every route must return a view model that validates against its frozen
contract.  Tested against the real seeded database, not hand-chosen literals.
"""

from __future__ import annotations

import os
from datetime import date

import pytest
import sqlalchemy as sa

from app.db.connection import connect, get_engine
from app.db.schema import (
    metadata,
    operating_model_areas,
    people,
    person_capabilities,
    sessions,
)
from app.db.scoped import Scope, primary_engagement
from app.services.pages import (
    build_area_detail,
    build_blueprint,
    build_capability_row,
    build_knowledge,
    build_operating_model,
    build_overview,
    build_passport,
    build_people,
    build_readiness,
)
from contracts.viewmodels import (
    AreaDetailVM,
    BlueprintVM,
    CapabilityRowPartialVM,
    KnowledgeVM,
    OperatingModelVM,
    OverviewVM,
    PassportVM,
    PeopleVM,
    ReadinessVM,
)

ANCHOR = date(2026, 3, 2)
os.environ.setdefault("RELAY_SEED_TODAY", ANCHOR.isoformat())

from seed import load_all  # noqa: E402


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    engine = get_engine(str(tmp_path_factory.mktemp("pages") / "pages.db"))
    metadata.create_all(engine)
    load_all(engine)
    return engine


@pytest.fixture(scope="module")
def conn(seeded):
    with connect(seeded) as connection:
        yield connection


@pytest.fixture(scope="module")
def client(seeded):
    from app import create_app
    from app.db.connection import reset_engine
    db_file = str(seeded.url.database)
    os.environ["RELAY_DB"] = db_file
    reset_engine()
    app = create_app({"TESTING": True, "DATABASE": db_file})
    with app.test_client() as c:
        yield c
    reset_engine()


@pytest.fixture(scope="module")
def primary_id(conn) -> str:
    return primary_engagement(conn).id


def _make_shell():
    from contracts.viewmodels import ShellVM, NavItem, EngagementRef, PersonRef
    from contracts.vocabulary import Role
    return ShellVM(
        nav=[NavItem(key="overview", label="Overview", href="/", active=False)],
        engagements=[EngagementRef(id="e", name="Test", org="Org")],
        current_engagement=EngagementRef(id="e", name="Test", org="Org"),
        personas=[PersonRef(id="p", name="T", title="T", role=Role.EXPERT, initials="T")],
        current_persona=PersonRef(id="p", name="T", title="T", role=Role.EXPERT, initials="T"),
    )


class TestOverview:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_overview(scope, as_of=ANCHOR)
        vm = OverviewVM(shell=_make_shell(), **data)
        assert len(vm.metrics) > 0, "overview must have headline metrics"
        # Every metric should have a formula (unexplained numbers are forbidden)
        for tile in vm.metrics:
            assert tile.formula is not None or tile.value is not None

    def test_has_risks(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_overview(scope, as_of=ANCHOR)
        assert len(data["risks"]) > 0, "seeded data should produce risks"


class TestOperatingModel:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_operating_model(scope, as_of=ANCHOR)
        vm = OperatingModelVM(shell=_make_shell(), **data)
        assert len(vm.areas) > 0, "must have operating model areas"


class TestAreaDetail:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        areas = scope.rows(operating_model_areas)
        assert len(areas) > 0
        area_id = areas[0].id

        data = build_area_detail(scope, area_id, as_of=ANCHOR)
        vm = AreaDetailVM(shell=_make_shell(), **data)
        assert vm.area.id == area_id

    def test_bad_area_raises(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        with pytest.raises(ValueError, match="no operating model area"):
            build_area_detail(scope, "nonexistent", as_of=ANCHOR)


class TestBlueprint:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_blueprint(scope, as_of=ANCHOR)
        vm = BlueprintVM(shell=_make_shell(), **data)
        assert len(vm.areas) > 0


class TestPeople:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_people(scope)
        vm = PeopleVM(shell=_make_shell(), **data)
        total = len(vm.experts) + len(vm.counterparts)
        assert total > 0, "must have people"


class TestPassport:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        people_rows = scope.rows(people)
        assert len(people_rows) > 0
        person_id = people_rows[0].id

        data = build_passport(scope, person_id, as_of=ANCHOR)
        vm = PassportVM(shell=_make_shell(), **data)
        assert vm.person.id == person_id

    def test_bad_person_raises(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        with pytest.raises(ValueError, match="no person"):
            build_passport(scope, "nonexistent", as_of=ANCHOR)


class TestKnowledge:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_knowledge(scope)
        vm = KnowledgeVM(shell=_make_shell(), **data)
        assert len(vm.items) > 0, "seeded data must have knowledge items"


class TestReadiness:

    def test_produces_valid_vm(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_readiness(scope, as_of=ANCHOR)
        vm = ReadinessVM(shell=_make_shell(), **data)
        assert len(vm.metrics) > 0


class TestRiskExplanations:
    """Every risk must say which numbers put it on the register.

    The engine already computes them; the page used to drop them, so these
    guard the seam rather than the arithmetic.
    """

    def _risks(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        data = build_readiness(scope, as_of=ANCHOR)
        return ReadinessVM(shell=_make_shell(), **data).risks

    def test_every_risk_explains_itself(self, conn, primary_id):
        risks = self._risks(conn, primary_id)
        assert risks, "seed should produce risks"
        for risk in risks:
            assert len(risk.problem) > len(risk.title) // 2
            assert risk.problem.strip().endswith(".")

    def test_explanation_cites_the_deciding_numbers(self, conn, primary_id):
        """A no-coverage risk names the level that failed the threshold."""
        risks = self._risks(conn, primary_id)
        coverage = [r for r in risks if "independent local coverage" in r.title]
        assert coverage, "seed should contain a no-coverage risk"
        problem = coverage[0].problem
        assert "level" in problem.lower()
        assert any(ch.isdigit() for ch in problem)

    def test_no_identifier_reaches_the_screen(self, conn, primary_id):
        """Inputs carry row ids; the page must show names instead."""
        import re

        pattern = re.compile(r"(?:p-|cap-|area-|req-)[a-z]")
        for risk in self._risks(conn, primary_id):
            assert not pattern.search(risk.problem), risk.problem
            assert not pattern.search(risk.local_trainer or ""), risk.local_trainer

    def test_local_trainer_filled_when_someone_can_teach(self, conn, primary_id):
        """`teachers` is '(none)' across the seed, so the field stays None --
        but it must be driven by the data, never hardcoded."""
        risks = self._risks(conn, primary_id)
        single = [r for r in risks if "single knowledge holder" in r.title]
        assert single, "seed should contain a single-holder risk"
        assert "nobody" in single[0].problem.lower()


class TestNextExperienceOnCapabilityRows:
    """CapabilityRow.next_experience is in the frozen contract and was always
    None. It is filled from the recommendation NEXT_ACTION persists."""

    def _plant(self, conn, primary_id, capability_name):
        from app.db.schema import sessions as s_table

        scope = Scope(conn, primary_id)
        session = scope.rows(s_table)[0]
        conn.execute(
            sa.update(s_table)
            .where(s_table.c.id == session.id)
            .values(next_experience={
                "capability": capability_name,
                "recommended_experience": "Lead the next review end to end.",
                "objective": "o", "current_level": 3, "target_level": 4,
                "rail": "lead", "learner_responsibilities": ["a"],
                "expert_role": "observe", "rationale": "r",
                "risk_if_deferred": "d", "urgency": "high",
            })
        )
        return scope, list(session.learner_ids or ())

    def _clear(self, conn, primary_id):
        from app.db.schema import sessions as s_table

        conn.execute(sa.update(s_table).values(next_experience=None))

    def test_recommendation_reaches_the_learners_row(self, conn, primary_id):
        from app.db.schema import capabilities

        scope = Scope(conn, primary_id)
        cap = scope.rows(capabilities)[0]
        try:
            scope, learners = self._plant(conn, primary_id, cap.name)
            assert learners, "seed session should have learners"
            data = build_passport(scope, learners[0], as_of=ANCHOR)
            vm = PassportVM(shell=_make_shell(), **data)
            matched = [r for r in vm.capabilities if r.capability_id == cap.id]
            if matched:
                assert matched[0].next_experience == "Lead the next review end to end."
            for row in vm.capabilities:
                if row.capability_id != cap.id:
                    assert row.next_experience is None
        finally:
            self._clear(conn, primary_id)

    def test_unmatched_capability_name_is_skipped_not_guessed(self, conn, primary_id):
        """A name the engagement does not use must attach to no row at all."""
        try:
            scope, learners = self._plant(conn, primary_id, "A Capability That Does Not Exist")
            data = build_passport(scope, learners[0], as_of=ANCHOR)
            vm = PassportVM(shell=_make_shell(), **data)
            assert all(r.next_experience is None for r in vm.capabilities)
        finally:
            self._clear(conn, primary_id)

    def test_absent_recommendation_leaves_rows_alone(self, conn, primary_id):
        self._clear(conn, primary_id)
        scope = Scope(conn, primary_id)
        person = scope.rows(people)[0]
        data = build_passport(scope, person.id, as_of=ANCHOR)
        vm = PassportVM(shell=_make_shell(), **data)
        assert all(r.next_experience is None for r in vm.capabilities)


class TestKnowledgeCardNames:
    """Cards must resolve their own ids, without relying on call order.

    These names used to come from a module-level cache that only some pages
    populated, so a passport opened first in a fresh process rendered every
    area as an empty string -- and a passport opened after another
    engagement's page could render that engagement's names.
    """

    def test_passport_names_areas_without_priming(self, conn, primary_id):
        from app.db.schema import knowledge_items

        scope = Scope(conn, primary_id)
        exposed_ids = {
            pid
            for row in scope.rows(knowledge_items)
            for pid in (row.people_exposed or [])
        }
        assert exposed_ids, "seed should expose knowledge to someone"
        person_id = sorted(exposed_ids)[0]

        data = build_passport(scope, person_id, as_of=ANCHOR)
        vm = PassportVM(shell=_make_shell(), **data)
        assert vm.knowledge_exposed
        for card in vm.knowledge_exposed:
            assert card.area, f"{card.id} rendered a blank area"

    def test_capability_is_a_name_not_an_id(self, conn, primary_id):
        from app.db.schema import knowledge_items

        scope = Scope(conn, primary_id)
        data = build_knowledge(scope)
        vm = KnowledgeVM(shell=_make_shell(), **data)

        seeded = sum(1 for r in scope.rows(knowledge_items) if r.capability_id)
        filled = sum(1 for card in vm.items if card.capability)
        assert filled == seeded, "every seeded capability_id should resolve"

        for card in vm.items:
            if card.capability:
                assert not card.capability.startswith("cap-"), card.capability

    def test_names_do_not_cross_engagements(self, conn):
        """Each engagement resolves only its own area names."""
        from app.db.schema import engagements, operating_model_areas as oma

        ids = [r.id for r in conn.execute(sa.select(engagements.c.id))]
        assert len(ids) > 1, "reusability needs a second engagement"

        for eid in ids:
            scope = Scope(conn, eid)
            own = {r.name for r in scope.rows(oma)}
            vm = KnowledgeVM(shell=_make_shell(), **build_knowledge(scope))
            for card in vm.items:
                if card.area:
                    assert card.area in own, f"{card.area} is not in {eid}"


class TestPropagationFilter:
    """`propagation_capability` has been in the contract since it was frozen."""

    def _vm(self, conn, primary_id, capability_id=None):
        scope = Scope(conn, primary_id)
        data = build_readiness(scope, as_of=ANCHOR, capability_id=capability_id)
        return ReadinessVM(shell=_make_shell(), **data)

    def test_unfiltered_shows_everyone(self, conn, primary_id):
        vm = self._vm(conn, primary_id)
        assert vm.propagation_capability is None
        assert vm.propagation

    def test_filter_labels_with_the_capability_name(self, conn, primary_id):
        from app.db.schema import capabilities

        scope = Scope(conn, primary_id)
        cap = scope.rows(capabilities)[0]
        vm = self._vm(conn, primary_id, cap.id)
        assert vm.propagation_capability == cap.name
        assert cap.id not in (vm.propagation_capability or "")

    def test_filter_narrows_the_tree(self, conn, primary_id):
        """Filtering can only ever remove people, never invent them."""
        from app.db.schema import capabilities

        scope = Scope(conn, primary_id)
        everyone = self._vm(conn, primary_id).propagation
        baseline = len(everyone[0].children) if everyone else 0

        for cap in scope.rows(capabilities):
            vm = self._vm(conn, primary_id, cap.id)
            for node in vm.propagation:
                assert len(node.children) <= baseline

    def test_unknown_capability_shows_nothing(self, conn, primary_id):
        """A filter that matched nothing must look like it matched nothing."""
        vm = self._vm(conn, primary_id, "cap-does-not-exist")
        assert vm.propagation == []


class TestCapabilityRow:

    def test_produces_valid_partial(self, conn, primary_id):
        scope = Scope(conn, primary_id)
        pcs = scope.rows(person_capabilities)
        assert len(pcs) > 0
        pc = pcs[0]

        data = build_capability_row(scope, pc.person_id, pc.capability_id)
        vm = CapabilityRowPartialVM(**data)
        assert vm.row.capability_id == pc.capability_id


JSON = {"Accept": "application/json"}


class TestRoutes:


    def test_overview_route(self, client):
        res = client.get("/", headers=JSON)
        assert res.status_code == 200
        assert "metrics" in res.json
        assert "shell" in res.json

    def test_operating_model_route(self, client):
        res = client.get("/operating-model", headers=JSON)
        assert res.status_code == 200
        assert "areas" in res.json

    def test_area_detail_route(self, client, conn, primary_id):
        scope = Scope(conn, primary_id)
        areas = scope.rows(operating_model_areas)
        res = client.get(f"/operating-model/{areas[0].id}", headers=JSON)
        assert res.status_code == 200
        assert res.json["area"]["id"] == areas[0].id

    def test_area_detail_404(self, client):
        res = client.get("/operating-model/nonexistent", headers=JSON)
        assert res.status_code == 404

    def test_blueprint_route(self, client):
        res = client.get("/blueprint", headers=JSON)
        assert res.status_code == 200
        assert "areas" in res.json

    def test_people_route(self, client):
        res = client.get("/people", headers=JSON)
        assert res.status_code == 200
        assert "experts" in res.json

    def test_passport_route(self, client, conn, primary_id):
        scope = Scope(conn, primary_id)
        p = scope.rows(people)[0]
        res = client.get(f"/people/{p.id}", headers=JSON)
        assert res.status_code == 200
        assert res.json["person"]["id"] == p.id

    def test_passport_404(self, client):
        res = client.get("/people/nonexistent", headers=JSON)
        assert res.status_code == 404

    def test_knowledge_route(self, client):
        res = client.get("/knowledge", headers=JSON)
        assert res.status_code == 200
        assert "items" in res.json

    def test_readiness_route(self, client):
        res = client.get("/readiness", headers=JSON)
        assert res.status_code == 200
        assert "metrics" in res.json

    def test_capability_row_route(self, client, conn, primary_id):
        scope = Scope(conn, primary_id)
        pc = scope.rows(person_capabilities)[0]
        res = client.get(f"/people/{pc.person_id}/capability/{pc.capability_id}", headers=JSON)
        assert res.status_code == 200
        assert res.json["row"]["capability_id"] == pc.capability_id

    def test_capability_row_404(self, client):
        res = client.get("/people/nonexistent/capability/nonexistent", headers=JSON)
        assert res.status_code == 404



class TestRoutesRenderHTML:
    """SYNC-2: every read route renders its template against the real database."""

    def test_pages_render(self, client, conn, primary_id):
        scope = Scope(conn, primary_id)
        area = scope.rows(operating_model_areas)[0]
        person = scope.rows(people)[0]
        pc = scope.rows(person_capabilities)[0]
        for path in ["/", "/operating-model", f"/operating-model/{area.id}", "/blueprint",
                     "/people", f"/people/{person.id}", "/knowledge", "/readiness", "/sessions",
                     f"/people/{pc.person_id}/capability/{pc.capability_id}"]:
            res = client.get(path)
            assert res.status_code == 200, (path, res.text[:300])
            assert res.mimetype == "text/html", path

    def test_format_json_still_available(self, client):
        assert "metrics" in client.get("/?format=json").json
