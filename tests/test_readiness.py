"""Tests for the readiness engine (planv0.2.md section 4 B4).

Three things these tests are really defending:

  1. **Nothing is unexplained.** `test_every_public_result_is_explained` walks
     the package's whole public surface and fails if any returned number or
     category is missing its `inputs` or `formula`. Adding an opaque metric
     later breaks the build.
  2. **Nothing is baked in.** Every fixture below is synthetic and
     sector-neutral -- ids like `cap-a`, names like "Capability A". A test that
     needed a real engagement to make sense would mean the engine did too.
  3. **Nothing is ambient.** No clock, no database, no network. Asserted
     structurally as well as behaviourally.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
from datetime import date
from pathlib import Path

import pytest

from contracts.viewmodels import AreaCard, MetricTile
from contracts.vocabulary import (
    LEVEL_INDEPENDENT,
    LEVEL_TEACHER,
    KnowledgeType,
    RequirementKind,
    Role,
    Status,
    TransferState,
)

import app.readiness as rd
from app.readiness import (
    Area,
    Capability,
    CapabilityLevel,
    EngagementSnapshot,
    KnowledgeItem,
    Metric,
    Person,
    ReadinessWeights,
    Requirement,
    Verdict,
)
from app.readiness.explain import Explained
from app.readiness.risk import RiskFinding

TODAY = date(2026, 3, 1)
PACKAGE_DIR = Path(rd.__file__).parent


# ---------------------------------------------------------------------------
# Synthetic engagement builders -- no sector, no proper nouns
# ---------------------------------------------------------------------------


def expert(pid: str = "p-expert", departure: date | None = date(2026, 3, 29)) -> Person:
    return Person(id=pid, name=f"Expert {pid[-1].upper()}", role=Role.EXPERT, departure_date=departure)


def local(pid: str) -> Person:
    return Person(id=pid, name=f"Local {pid[-1].upper()}", role=Role.COUNTERPART)


def cap(cid: str, *, critical: bool = True) -> Capability:
    return Capability(id=cid, name=f"Capability {cid[-1].upper()}", critical=critical)


def level(person_id: str, capability_id: str, value: int) -> CapabilityLevel:
    return CapabilityLevel(person_id=person_id, capability_id=capability_id, level=value)


def area(
    aid: str,
    *,
    critical: bool = True,
    owner: str | None = None,
    validated: bool = False,
    capabilities: tuple[str, ...] = (),
) -> Area:
    return Area(
        id=aid,
        name=f"Area {aid[-1].upper()}",
        critical=critical,
        local_owner_id=owner,
        owner_validated=validated,
        capability_ids=capabilities,
    )


def requirements(
    area_id: str,
    kind: RequirementKind,
    *,
    total: int,
    complete: int,
    validated: bool = True,
    prefix: str = "r",
) -> tuple[Requirement, ...]:
    """`complete` of `total` requirements in COMPLETE state, the rest NONE."""
    return tuple(
        Requirement(
            id=f"{prefix}-{area_id}-{kind.value}-{i:02d}",
            area_id=area_id,
            kind=kind,
            state=TransferState.COMPLETE if i < complete else TransferState.NONE,
            validated=validated,
        )
        for i in range(total)
    )


def snapshot(**overrides: object) -> EngagementSnapshot:
    base: dict[str, object] = {"engagement_id": "eng-test", "as_of": TODAY}
    base.update(overrides)
    return EngagementSnapshot(**base)  # type: ignore[arg-type]


def reference_snapshot() -> EngagementSnapshot:
    """One engagement rich enough to exercise every branch of every metric."""
    return snapshot(
        people=(expert(), local("p-a"), local("p-b")),
        capabilities=(cap("cap-a"), cap("cap-b"), cap("cap-c"), cap("cap-d", critical=False)),
        levels=(
            level("p-expert", "cap-a", 6),
            level("p-expert", "cap-b", 6),
            level("p-expert", "cap-c", 5),
            level("p-a", "cap-a", LEVEL_TEACHER),
            level("p-a", "cap-b", LEVEL_INDEPENDENT),
            level("p-b", "cap-b", 2),
            level("p-b", "cap-c", 1),
            level("p-a", "cap-d", LEVEL_TEACHER),
        ),
        areas=(
            area("area-1", owner="p-a", validated=True, capabilities=("cap-a", "cap-b")),
            area("area-2", capabilities=("cap-c",)),
        ),
        requirements=(
            *requirements("area-1", RequirementKind.FORMAL, total=2, complete=2),
            *requirements("area-1", RequirementKind.TACIT, total=2, complete=1),
            *requirements("area-2", RequirementKind.TECHNICAL, total=2, complete=1),
            *requirements("area-2", RequirementKind.RELATIONSHIP, total=1, complete=0),
            *requirements(
                "area-2", RequirementKind.JUDGMENT, total=2, complete=2, validated=False
            ),
        ),
        knowledge=(
            KnowledgeItem(
                id="k-1",
                type=KnowledgeType.EXPERT_INSIGHT,
                validated=True,
                area_id="area-1",
                capability_id="cap-a",
            ),
            KnowledgeItem(id="k-2", type=KnowledgeType.HEURISTIC, validated=False),
        ),
    )


# ---------------------------------------------------------------------------
# The package must not know the database (or the clock) exists
# ---------------------------------------------------------------------------

FORBIDDEN_IMPORTS = ("sqlalchemy", "sqlite3", "flask", "app.db", "app.ai", "openai")
FORBIDDEN_CLOCK = (r"date\.today", r"datetime\.now", r"datetime\.utcnow", r"time\.time")


def package_sources() -> list[Path]:
    return sorted(p for p in PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def test_sources_exist() -> None:
    assert package_sources(), "found no readiness sources -- the structural tests are vacuous"


@pytest.mark.parametrize("module", FORBIDDEN_IMPORTS)
def test_readiness_does_not_import_infrastructure(module: str) -> None:
    """Scoring is pure. It cannot be allowed to issue a query by accident."""
    pattern = re.compile(rf"^\s*(import|from)\s+{re.escape(module)}\b", re.MULTILINE)
    hits = [str(p.name) for p in package_sources() if pattern.search(p.read_text(encoding="utf-8"))]
    assert not hits, f"app/readiness must not import {module}: {hits}"


@pytest.mark.parametrize("call", FORBIDDEN_CLOCK)
def test_readiness_never_reads_the_clock(call: str) -> None:
    """Every date comes in through EngagementSnapshot.as_of."""
    pattern = re.compile(call)
    hits = [str(p.name) for p in package_sources() if pattern.search(p.read_text(encoding="utf-8"))]
    assert not hits, f"app/readiness must take dates as parameters, not call {call}: {hits}"


# ---------------------------------------------------------------------------
# Generic: nothing may be unexplained
# ---------------------------------------------------------------------------


def collect_explained(obj: object, seen: set[int] | None = None) -> list[Explained]:
    """Every Metric / Verdict / RiskFinding reachable from a returned value."""
    seen = seen if seen is not None else set()
    if id(obj) in seen:
        return []
    seen.add(id(obj))

    found: list[Explained] = []
    if isinstance(obj, (Metric, Verdict, RiskFinding)):
        found.append(obj)  # type: ignore[arg-type]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        for f in dataclasses.fields(obj):
            found.extend(collect_explained(getattr(obj, f.name), seen))
    elif isinstance(obj, dict):
        for value in obj.values():
            found.extend(collect_explained(value, seen))
    elif isinstance(obj, (list, tuple, set)):
        for value in obj:
            found.extend(collect_explained(value, seen))
    return found


SNAP = reference_snapshot()
AREA = SNAP.areas[0]

# Every public function that produces a result, and how to call it. The
# completeness assertion below means a new public function cannot be added
# without landing here -- which is what stops an unexplained metric appearing.
PUBLIC_CALLS = {
    "all_area_readiness": lambda: rd.all_area_readiness(SNAP),
    "all_metrics": lambda: rd.all_metrics(SNAP),
    "area_capability_localization": lambda: rd.area_capability_localization(SNAP, AREA),
    "area_local_ownership": lambda: rd.area_local_ownership(SNAP, AREA),
    "area_readiness": lambda: rd.area_readiness(SNAP, AREA),
    "area_trainer_coverage": lambda: rd.area_trainer_coverage(SNAP, AREA),
    "capability_localization": lambda: rd.capability_localization(SNAP),
    "days_until_departure": lambda: rd.days_until_departure(SNAP),
    "departure_readiness": lambda: rd.departure_readiness(SNAP),
    "derive_local_capability": lambda: rd.derive_local_capability(
        localization=0.5, best_local_level=3
    ),
    "derive_status": lambda: rd.derive_status(0.68),
    "expert_dependent": lambda: rd.expert_dependent(SNAP),
    "formal_transfer": lambda: rd.formal_transfer(SNAP),
    "headline_metrics": lambda: rd.headline_metrics(SNAP),
    "informal_transfer": lambda: rd.informal_transfer(SNAP),
    "knowledge_at_risk": lambda: rd.knowledge_at_risk(SNAP),
    "local_ownership": lambda: rd.local_ownership(SNAP),
    "local_trainers": lambda: rd.local_trainers(SNAP),
    "locally_teachable": lambda: rd.locally_teachable(SNAP),
    "operating_model_readiness": lambda: rd.operating_model_readiness(SNAP),
    "readiness_components": lambda: rd.readiness_components(SNAP),
    "requirement_coverage": lambda: rd.requirement_coverage(SNAP),
    "requirement_coverage_by_kind": lambda: rd.requirement_coverage_by_kind(SNAP),
    "trainer_coverage": lambda: rd.trainer_coverage(SNAP),
    "validated_knowledge_count": lambda: rd.validated_knowledge_count(SNAP),
}

# Utilities that legitimately return something other than an explained result.
EXEMPT_CALLABLES = {
    "departing_expert",  # returns a Person; explained by the metric that uses it
    "percent",  # formatting helper
    "resolve_weights",  # returns (weights, provenance) for the popover
}


def test_public_call_table_covers_the_whole_surface() -> None:
    """A new public function must be exercised here, or this fails."""
    public_functions = {
        name
        for name in rd.__all__
        if inspect.isfunction(getattr(rd, name))
    }
    missing = public_functions - set(PUBLIC_CALLS) - EXEMPT_CALLABLES
    assert not missing, (
        "these public functions are not exercised by the explanation test: "
        f"{sorted(missing)}. Add them to PUBLIC_CALLS, or to EXEMPT_CALLABLES "
        "with a reason."
    )
    stale = set(PUBLIC_CALLS) - public_functions
    assert not stale, f"PUBLIC_CALLS names functions that no longer exist: {sorted(stale)}"


@pytest.mark.parametrize("name", sorted(PUBLIC_CALLS))
def test_every_public_result_is_explained(name: str) -> None:
    """value + inputs + formula on every number and every category returned."""
    results = collect_explained(PUBLIC_CALLS[name]())
    assert results, f"{name} returned nothing explainable"
    for result in results:
        key = getattr(result, "key", getattr(result, "kind", "?"))
        assert result.value is not None, f"{name}/{key}: no value"
        assert result.formula, f"{name}/{key}: empty formula"
        assert result.inputs, f"{name}/{key}: empty inputs"
        for k, v in result.inputs.items():
            assert isinstance(k, str) and isinstance(v, str), (
                f"{name}/{key}: inputs must be str->str for MetricTile, got {k!r}: {v!r}"
            )


def test_metric_maps_onto_the_metric_tile_contract() -> None:
    """The service layer's mapping must be a one-liner, so prove it is."""
    for metric in rd.headline_metrics(SNAP):
        tile = MetricTile(**metric.as_tile())  # type: ignore[arg-type]
        assert tile.value
        assert tile.formula
        assert tile.inputs


def test_area_readiness_maps_onto_the_area_card_contract() -> None:
    card = AreaCard(**rd.area_readiness(SNAP, AREA).as_card())  # type: ignore[arg-type]
    assert 0 <= card.formal_pct <= 100
    assert card.status_label


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_identical_inputs_give_identical_output() -> None:
    first = rd.all_metrics(reference_snapshot())
    second = rd.all_metrics(reference_snapshot())
    assert {k: v.value for k, v in first.items()} == {k: v.value for k, v in second.items()}
    assert {k: dict(v.inputs) for k, v in first.items()} == {
        k: dict(v.inputs) for k, v in second.items()
    }


def test_input_ordering_does_not_change_the_result() -> None:
    """Row order out of the database must not move a number."""
    base = reference_snapshot()
    shuffled = dataclasses.replace(
        base,
        people=tuple(reversed(base.people)),
        capabilities=tuple(reversed(base.capabilities)),
        levels=tuple(reversed(base.levels)),
        requirements=tuple(reversed(base.requirements)),
    )
    assert (
        rd.operating_model_readiness(base).value
        == rd.operating_model_readiness(shuffled).value
    )
    assert dict(rd.capability_localization(base).inputs) == dict(
        rd.capability_localization(shuffled).inputs
    )


def test_days_until_departure_uses_as_of_not_the_clock() -> None:
    metric = rd.days_until_departure(SNAP)
    assert metric.value == 28
    assert metric.display == "28 days"
    assert metric.inputs["as_of"] == TODAY.isoformat()

    later = dataclasses.replace(SNAP, as_of=date(2026, 3, 15))
    assert rd.days_until_departure(later).value == 14


def test_days_until_departure_without_a_departure_date() -> None:
    metric = rd.days_until_departure(
        snapshot(people=(expert(departure=None),))
    )
    assert metric.value == 0
    assert "note" in metric.inputs


# ---------------------------------------------------------------------------
# Boundary cases
# ---------------------------------------------------------------------------


def test_empty_engagement_scores_zero_and_says_why() -> None:
    empty = snapshot()
    readiness = rd.operating_model_readiness(empty)
    assert readiness.value == 0.0
    assert rd.derive_status(readiness.value).value is Status.CRITICAL

    localization = rd.capability_localization(empty)
    assert localization.value == 0.0
    # An empty denominator must be visible in the popover, not silently 0%.
    assert localization.inputs["note"] == rd.EMPTY_DENOMINATOR_NOTE


def test_empty_engagement_produces_no_risks() -> None:
    register = rd.knowledge_at_risk(snapshot())
    assert register.findings == ()
    assert register.count.value == 0


def test_all_capabilities_at_level_zero() -> None:
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"), cap("cap-b")),
        levels=(level("p-a", "cap-a", 0), level("p-a", "cap-b", 0)),
    )
    assert rd.capability_localization(snap).value == 0.0
    assert rd.locally_teachable(snap).value == 0
    assert rd.local_trainers(snap).value == 0
    # Nobody expert-dependent either: the expert has no recorded level.
    assert rd.expert_dependent(snap).value == 0


def test_all_capabilities_at_the_top_level() -> None:
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"), cap("cap-b")),
        levels=(
            level("p-a", "cap-a", LEVEL_TEACHER),
            level("p-a", "cap-b", LEVEL_TEACHER),
            level("p-expert", "cap-a", LEVEL_TEACHER),
        ),
        areas=(area("area-1", owner="p-a", validated=True, capabilities=("cap-a", "cap-b")),),
        requirements=(
            *requirements("area-1", RequirementKind.FORMAL, total=2, complete=2),
            *requirements("area-1", RequirementKind.TACIT, total=2, complete=2),
        ),
    )
    assert rd.capability_localization(snap).value == 1.0
    assert rd.locally_teachable(snap).value == 2
    assert rd.expert_dependent(snap).value == 0
    assert rd.trainer_coverage(snap).value == 1.0
    assert rd.operating_model_readiness(snap).value == pytest.approx(1.0)
    assert rd.derive_status(1.0).value is Status.SUSTAINABLE


def test_single_capability_engagement() -> None:
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"),),
        levels=(level("p-a", "cap-a", LEVEL_INDEPENDENT),),
    )
    localization = rd.capability_localization(snap)
    assert localization.value == 1.0
    assert localization.display == "100%"
    assert localization.inputs["numerator"] == "1"
    assert localization.inputs["denominator"] == "1"


def test_non_critical_capabilities_are_excluded_from_localization() -> None:
    snap = snapshot(
        people=(local("p-a"),),
        capabilities=(cap("cap-a"), cap("cap-b", critical=False)),
        levels=(level("p-a", "cap-a", LEVEL_INDEPENDENT),),
    )
    assert rd.capability_localization(snap).value == 1.0
    # ... but teachability is counted over every capability (section 4 B4).
    assert rd.locally_teachable(snap).inputs["capabilities_considered"] == "2"


# ---------------------------------------------------------------------------
# Level thresholds, tested exactly at the boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "localized"),
    [
        (LEVEL_INDEPENDENT - 1, False),
        (LEVEL_INDEPENDENT, True),
        (LEVEL_INDEPENDENT + 1, True),
    ],
)
def test_localization_threshold_is_exact(value: int, localized: bool) -> None:
    snap = snapshot(
        people=(local("p-a"),),
        capabilities=(cap("cap-a"),),
        levels=(level("p-a", "cap-a", value),),
    )
    assert rd.capability_localization(snap).value == (1.0 if localized else 0.0)


@pytest.mark.parametrize(
    ("value", "teachable"),
    [(LEVEL_TEACHER - 1, False), (LEVEL_TEACHER, True)],
)
def test_teacher_threshold_is_exact(value: int, teachable: bool) -> None:
    snap = snapshot(
        people=(local("p-a"),),
        capabilities=(cap("cap-a"),),
        levels=(level("p-a", "cap-a", value),),
    )
    assert rd.locally_teachable(snap).value == (1 if teachable else 0)
    assert rd.local_trainers(snap).value == (1 if teachable else 0)


def test_a_level_above_the_scale_is_rejected_at_the_boundary() -> None:
    with pytest.raises(ValueError):
        CapabilityLevel(person_id="p-a", capability_id="cap-a", level=rd.MAX_LEVEL + 1)
    with pytest.raises(ValueError):
        CapabilityLevel(person_id="p-a", capability_id="cap-a", level=-1)


def test_only_local_people_localize_a_capability() -> None:
    """An expert at level 6 is the problem, not the solution."""
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"),),
        levels=(level("p-expert", "cap-a", LEVEL_TEACHER), level("p-a", "cap-a", 2)),
    )
    assert rd.capability_localization(snap).value == 0.0
    assert rd.locally_teachable(snap).value == 0
    assert rd.expert_dependent(snap).value == 1


def test_a_manager_counts_as_local() -> None:
    manager = Person(id="p-m", name="Manager M", role=Role.MANAGER)
    snap = snapshot(
        people=(manager,),
        capabilities=(cap("cap-a"),),
        levels=(level("p-m", "cap-a", LEVEL_INDEPENDENT),),
    )
    assert rd.capability_localization(snap).value == 1.0


# ---------------------------------------------------------------------------
# Requirements: formal vs informal, and coverage
# ---------------------------------------------------------------------------


def test_formal_counts_complete_while_informal_also_needs_validation() -> None:
    snap = snapshot(
        areas=(area("area-1"),),
        requirements=(
            *requirements("area-1", RequirementKind.FORMAL, total=4, complete=3, validated=False),
            *requirements("area-1", RequirementKind.TACIT, total=4, complete=4, validated=False),
        ),
    )
    assert rd.formal_transfer(snap).value == pytest.approx(0.75)
    # Complete but unvalidated capture earns nothing on the informal side.
    assert rd.informal_transfer(snap).value == 0.0
    assert rd.informal_transfer(snap).inputs["validation_required"] == "yes"


def test_partial_state_earns_nothing_by_default_and_half_on_request() -> None:
    reqs = (
        Requirement(
            id="r-1", area_id="area-1", kind=RequirementKind.FORMAL, state=TransferState.COMPLETE
        ),
        Requirement(
            id="r-2", area_id="area-1", kind=RequirementKind.FORMAL, state=TransferState.PARTIAL
        ),
    )
    snap = snapshot(areas=(area("area-1"),), requirements=reqs)
    assert rd.formal_transfer(snap).value == pytest.approx(0.5)
    assert rd.formal_transfer(snap, credit=rd.PARTIAL_CREDIT).value == pytest.approx(0.75)
    # The credit map used is named in the formula, so the popover cannot lie.
    assert "partial=0.5" in rd.formal_transfer(snap, credit=rd.PARTIAL_CREDIT).formula


def test_requirement_coverage_spans_every_kind() -> None:
    by_kind = rd.requirement_coverage_by_kind(SNAP)
    assert set(by_kind) == set(RequirementKind)
    overall = rd.requirement_coverage(SNAP)
    assert 0.0 <= overall.value <= 1.0
    assert overall.inputs["denominator"] == str(len(SNAP.requirements))


def test_formal_and_informal_kind_groups_are_disjoint_and_total() -> None:
    assert not (rd.FORMAL_KINDS & rd.INFORMAL_KINDS)
    assert rd.FORMAL_KINDS | rd.INFORMAL_KINDS == set(RequirementKind)


# ---------------------------------------------------------------------------
# Ownership and trainer coverage
# ---------------------------------------------------------------------------


def test_an_owner_counts_only_when_local_and_validated() -> None:
    people = (expert(), local("p-a"))
    caps = (cap("cap-a"),)

    unvalidated = snapshot(people=people, capabilities=caps, areas=(area("area-1", owner="p-a"),))
    assert rd.local_ownership(unvalidated).value == 0.0

    expert_owned = snapshot(
        people=people,
        capabilities=caps,
        areas=(area("area-1", owner="p-expert", validated=True),),
    )
    assert rd.local_ownership(expert_owned).value == 0.0

    good = snapshot(
        people=people, capabilities=caps, areas=(area("area-1", owner="p-a", validated=True),)
    )
    assert rd.local_ownership(good).value == 1.0


def test_trainer_coverage_is_per_area_not_per_engagement() -> None:
    snap = snapshot(
        people=(local("p-a"),),
        capabilities=(cap("cap-a"), cap("cap-b")),
        levels=(level("p-a", "cap-a", LEVEL_TEACHER),),
        areas=(
            area("area-1", capabilities=("cap-a",)),
            area("area-2", capabilities=("cap-b",)),
        ),
    )
    assert rd.trainer_coverage(snap).value == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Weights -- per-engagement tunable (section 0.5)
# ---------------------------------------------------------------------------


def test_weights_default_to_the_documented_constant() -> None:
    assert rd.DEFAULT_WEIGHTS.as_mapping() == {
        "local_ownership": 0.25,
        "capability_localization": 0.30,
        "formal_transfer": 0.15,
        "informal_transfer": 0.20,
        "trainer_coverage": 0.10,
    }
    assert sum(rd.DEFAULT_WEIGHTS.as_mapping().values()) == pytest.approx(1.0)


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        ReadinessWeights(local_ownership=0.9)
    with pytest.raises(ValueError, match="negative"):
        ReadinessWeights(
            local_ownership=-0.1,
            capability_localization=0.5,
            formal_transfer=0.2,
            informal_transfer=0.3,
            trainer_coverage=0.1,
        )


def tuned() -> ReadinessWeights:
    """An engagement that cares only about ownership and localization."""
    return ReadinessWeights(
        local_ownership=0.5,
        capability_localization=0.5,
        formal_transfer=0.0,
        informal_transfer=0.0,
        trainer_coverage=0.0,
    )


def test_an_override_changes_the_number_and_says_so() -> None:
    default = rd.operating_model_readiness(SNAP)
    override = rd.operating_model_readiness(SNAP, weights=tuned())
    assert override.value != default.value
    assert override.inputs["weights_source"] == "explicit override"
    assert default.inputs["weights_source"] == "default"
    # The popover shows the weights that were actually applied.
    assert override.formula == tuned().describe()
    assert "0.5*local_ownership" in override.formula


def test_engagement_weights_from_the_snapshot_are_used() -> None:
    from_db = dataclasses.replace(SNAP, weights=tuned())
    metric = rd.operating_model_readiness(from_db)
    assert metric.value == rd.operating_model_readiness(SNAP, weights=tuned()).value
    assert metric.inputs["weights_source"] == "engagement (database)"


def test_an_explicit_override_beats_the_snapshot_weights() -> None:
    from_db = dataclasses.replace(SNAP, weights=tuned())
    metric = rd.operating_model_readiness(from_db, weights=rd.DEFAULT_WEIGHTS)
    assert metric.inputs["weights_source"] == "explicit override"
    assert metric.value == rd.operating_model_readiness(SNAP).value


def test_the_overall_score_is_reconstructable_from_its_inputs() -> None:
    """A reader must be able to redo the arithmetic from the popover alone."""
    metric = rd.operating_model_readiness(SNAP)
    total = 0.0
    for name in rd.DEFAULT_WEIGHTS.as_mapping():
        contribution = metric.inputs[name].split("=")[-1].strip()
        total += float(contribution)
    assert total == pytest.approx(metric.value, abs=1e-5)


# ---------------------------------------------------------------------------
# Status derivation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (1.00, Status.SUSTAINABLE),
        (0.90, Status.SUSTAINABLE),
        (0.8999, Status.ON_TRACK),
        (0.75, Status.ON_TRACK),
        (0.7499, Status.IN_PROGRESS),
        (0.68, Status.IN_PROGRESS),
        (0.40, Status.IN_PROGRESS),
        (0.3999, Status.AT_RISK),
        (0.15, Status.AT_RISK),
        (0.1499, Status.CRITICAL),
        (0.00, Status.CRITICAL),
    ],
)
def test_status_bands_are_exact_at_the_boundary(score: float, expected: Status) -> None:
    verdict = rd.derive_status(score)
    assert verdict.value is expected
    assert verdict.inputs["band"]
    assert verdict.formula == rd.DEFAULT_STATUS_THRESHOLDS.describe()


def test_status_thresholds_are_tunable() -> None:
    strict = rd.StatusThresholds(sustainable=0.99, on_track=0.95, in_progress=0.80, at_risk=0.50)
    assert rd.derive_status(0.90, thresholds=strict).value is Status.IN_PROGRESS
    assert rd.derive_status(0.90).value is Status.SUSTAINABLE


def test_status_thresholds_must_descend() -> None:
    with pytest.raises(ValueError, match="descend"):
        rd.StatusThresholds(sustainable=0.4, on_track=0.9)


@pytest.mark.parametrize(
    ("localization", "best_level", "expected"),
    [
        (1.0, LEVEL_INDEPENDENT, rd.LOCAL_CAPABILITY_STRONG),
        (0.5, LEVEL_INDEPENDENT, rd.LOCAL_CAPABILITY_DEVELOPING),
        (0.0, 3, rd.LOCAL_CAPABILITY_DEVELOPING),
        (0.0, 2, rd.LOCAL_CAPABILITY_DEVELOPING),
        (0.0, 1, rd.LOCAL_CAPABILITY_LIMITED),
        (0.0, -1, rd.LOCAL_CAPABILITY_LIMITED),
    ],
)
def test_local_capability_bands(localization: float, best_level: int, expected: str) -> None:
    verdict = rd.derive_local_capability(localization=localization, best_local_level=best_level)
    assert verdict.value == expected


# ---------------------------------------------------------------------------
# Per-area readiness, calibrated against the worked examples in RELAY.txt
# ---------------------------------------------------------------------------


def worked_area_snapshot(
    aid: str, *, formal_complete: int, informal_complete: int, owned: bool, best_level: int
) -> EngagementSnapshot:
    """One of RELAY.txt's five operating-model rows, reproduced synthetically.

    Twenty requirements a side gives 5% granularity, which is enough to hit the
    percentages that document prints. `best_level` encodes its Local Capability
    column: 6 is Strong (and therefore also the area's trainer), 3 is
    Developing, 1 is Limited.
    """
    capability_id = f"cap-{aid}"
    return snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap(capability_id),),
        levels=(level("p-a", capability_id, best_level),),
        areas=(
            area(
                aid,
                owner="p-a" if owned else None,
                validated=owned,
                capabilities=(capability_id,),
            ),
        ),
        requirements=(
            *requirements(aid, RequirementKind.FORMAL, total=20, complete=formal_complete),
            *requirements(aid, RequirementKind.TACIT, total=20, complete=informal_complete),
        ),
    )


# RELAY.txt's operating-model table: formal, informal, owner, local capability,
# and the status that document assigns the row.
WORKED_ROWS = [
    ("area-1", 20, 18, True, LEVEL_TEACHER, rd.LOCAL_CAPABILITY_STRONG, Status.SUSTAINABLE),
    ("area-2", 18, 13, True, 3, rd.LOCAL_CAPABILITY_DEVELOPING, Status.IN_PROGRESS),
    ("area-3", 15, 6, False, 1, rd.LOCAL_CAPABILITY_LIMITED, Status.AT_RISK),
    ("area-4", 17, 9, True, 3, rd.LOCAL_CAPABILITY_DEVELOPING, Status.IN_PROGRESS),
    ("area-5", 20, 16, True, LEVEL_TEACHER, rd.LOCAL_CAPABILITY_STRONG, Status.SUSTAINABLE),
]


@pytest.mark.parametrize(
    ("aid", "formal", "informal", "owned", "best_level", "band", "expected"), WORKED_ROWS
)
def test_default_thresholds_reproduce_the_worked_area_examples(
    aid: str,
    formal: int,
    informal: int,
    owned: bool,
    best_level: int,
    band: str,
    expected: Status,
) -> None:
    """The threshold table is calibrated, not guessed -- this is the evidence."""
    snap = worked_area_snapshot(
        aid,
        formal_complete=formal,
        informal_complete=informal,
        owned=owned,
        best_level=best_level,
    )
    result = rd.area_readiness(snap, snap.areas[0])
    assert result.local_capability.value == band
    assert result.status.value is expected, (
        f"{aid} scored {result.readiness.display} -> {result.status.value}"
    )


def test_area_readiness_uses_the_same_expression_as_the_engagement_score() -> None:
    """One area engagement: the area score and the headline must coincide."""
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"),),
        levels=(level("p-a", "cap-a", LEVEL_TEACHER),),
        areas=(area("area-1", owner="p-a", validated=True, capabilities=("cap-a",)),),
        requirements=(
            *requirements("area-1", RequirementKind.FORMAL, total=2, complete=1),
            *requirements("area-1", RequirementKind.TACIT, total=2, complete=1),
        ),
    )
    engagement = rd.operating_model_readiness(snap)
    area_score = rd.area_readiness(snap, snap.areas[0])
    assert area_score.readiness.value == pytest.approx(engagement.value)


def test_areas_are_returned_worst_first() -> None:
    results = rd.all_area_readiness(SNAP)
    values = [r.readiness.value for r in results]
    assert values == sorted(values)


def test_area_percentages_fit_the_area_card_contract() -> None:
    for result in rd.all_area_readiness(SNAP):
        card = result.as_card()
        assert 0 <= card["formal_pct"] <= 100  # type: ignore[operator]
        assert 0 <= card["informal_pct"] <= 100  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Knowledge at risk
# ---------------------------------------------------------------------------


def test_a_capability_with_no_local_coverage_is_critical() -> None:
    snap = snapshot(
        people=(expert(), local("p-a")),
        capabilities=(cap("cap-a"),),
        levels=(level("p-expert", "cap-a", LEVEL_TEACHER), level("p-a", "cap-a", 1)),
    )
    register = rd.knowledge_at_risk(snap)
    kinds = {f.kind for f in register.findings}
    assert rd.RiskKind.NO_LOCAL_COVERAGE in kinds
    assert rd.RiskKind.OBSERVED_NEVER_PERFORMED in kinds
    assert register.by_severity(Status.CRITICAL)


def test_a_single_local_holder_is_flagged() -> None:
    snap = snapshot(
        people=(local("p-a"),),
        capabilities=(cap("cap-a"),),
        levels=(level("p-a", "cap-a", LEVEL_INDEPENDENT),),
    )
    kinds = {f.kind for f in rd.knowledge_at_risk(snap).findings}
    assert rd.RiskKind.SINGLE_KNOWLEDGE_HOLDER in kinds
    assert rd.RiskKind.NO_LOCAL_COVERAGE not in kinds


def test_two_local_holders_clear_the_single_holder_flag() -> None:
    snap = snapshot(
        people=(local("p-a"), local("p-b")),
        capabilities=(cap("cap-a"),),
        levels=(
            level("p-a", "cap-a", LEVEL_INDEPENDENT),
            level("p-b", "cap-a", LEVEL_INDEPENDENT),
        ),
    )
    kinds = {f.kind for f in rd.knowledge_at_risk(snap).findings}
    assert rd.RiskKind.SINGLE_KNOWLEDGE_HOLDER not in kinds


def test_risks_are_ordered_worst_first_and_stably() -> None:
    register = rd.knowledge_at_risk(SNAP)
    order = [rd.risk.SEVERITY_ORDER.index(f.value) for f in register.findings]
    assert order == sorted(order)
    again = rd.knowledge_at_risk(reference_snapshot())
    assert [f.subject_id for f in register.findings] == [f.subject_id for f in again.findings]


def test_every_risk_severity_is_a_status_the_ui_can_render() -> None:
    for finding in rd.knowledge_at_risk(SNAP).findings:
        assert isinstance(finding.value, Status)
        assert finding.severity is finding.value


# ---------------------------------------------------------------------------
# Departure readiness
# ---------------------------------------------------------------------------


def test_departure_readiness_assembles_the_executive_view() -> None:
    result = rd.departure_readiness(SNAP)
    assert result.expert is not None and result.expert.id == "p-expert"
    assert result.days_remaining.value == 28
    assert result.capabilities_localized.value == 2  # cap-a and cap-b
    assert result.areas_locally_owned.value == 1
    assert result.local_trainers.value == 1
    assert result.validated_knowledge.value == 1
    assert result.open_risks.value == len(rd.knowledge_at_risk(SNAP).findings)
    assert len(result.tiles()) == 7


def test_departure_readiness_survives_an_engagement_with_no_expert() -> None:
    result = rd.departure_readiness(snapshot())
    assert result.expert is None
    assert result.status.value is Status.CRITICAL


def test_the_soonest_departure_wins() -> None:
    snap = snapshot(
        people=(
            expert("p-expert1", departure=date(2026, 6, 1)),
            expert("p-expert2", departure=date(2026, 3, 10)),
        )
    )
    assert rd.departing_expert(snap).id == "p-expert2"  # type: ignore[union-attr]
    assert rd.days_until_departure(snap).value == 9
