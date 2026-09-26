"""The engagement-wide readiness metrics, verbatim from planv0.2.md section 4 B4.

    capability_localization  = critical caps with >=1 local counterpart at level >=4 / critical caps
    locally_teachable        = count(caps with >=1 counterpart at level 6)
    expert_dependent         = critical caps where the expert is capable AND no local >=4
    local_ownership          = areas with a validated local owner / critical areas
    formal_transfer          = formal requirements complete / total formal
    informal_transfer        = informal requirements with validated capture / total informal
    trainer_coverage         = areas with >=1 local trainer / critical areas

    operating_model_readiness = weighted sum of the five (weights.py)

Every function here is pure: it reads a snapshot and returns a Metric. No
clock, no database, no AI. The one date-dependent figure --
days_until_departure -- reads `snapshot.as_of`, which the caller supplied.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    LEVEL_INDEPENDENT,
    LEVEL_TEACHER,
    RequirementKind,
    TransferState,
)

from app.readiness import _query as q
from app.readiness.explain import (
    Metric,
    count_metric,
    days_metric,
    ids,
    num,
    percent,
    ratio_metric,
    score_metric,
)
from app.readiness.inputs import EngagementSnapshot, Requirement
from app.readiness.weights import (
    FORMAL_KINDS,
    INFORMAL_KINDS,
    STRICT_CREDIT,
    ReadinessWeights,
    describe_credit,
    resolve_weights,
)

INDEPENDENT_LABEL = CAPABILITY_LEVELS[LEVEL_INDEPENDENT]
TEACHER_LABEL = CAPABILITY_LEVELS[LEVEL_TEACHER]


# ---------------------------------------------------------------------------
# Capability metrics
# ---------------------------------------------------------------------------


def capability_localization(snapshot: EngagementSnapshot) -> Metric:
    """Can the receiving organization do the critical work on its own?"""
    critical = q.critical_capabilities(snapshot)
    localized = [c for c in critical if q.is_localized(snapshot, c.id)]
    return ratio_metric(
        "capability_localization",
        "Capability Localization",
        numerator=len(localized),
        denominator=len(critical),
        formula=(
            f"critical capabilities with >=1 local person at level >= "
            f"{LEVEL_INDEPENDENT} ({INDEPENDENT_LABEL}) / critical capabilities"
        ),
        inputs={
            "threshold": f"{LEVEL_INDEPENDENT} ({INDEPENDENT_LABEL})",
            "localized_capabilities": ids(c.id for c in localized),
            "critical_capabilities": ids(c.id for c in critical),
        },
        caption=f"{len(localized)} of {len(critical)} critical capabilities",
    )


def locally_teachable(snapshot: EngagementSnapshot) -> Metric:
    """Capabilities the organization can now propagate without the expert.

    section 4 B4 writes this over *all* capabilities, not only critical ones --
    a teachable non-critical capability is still local teaching capacity.
    """
    teachable = [c for c in snapshot.capabilities if q.is_teachable(snapshot, c.id)]
    trainers: set[str] = set()
    for capability in teachable:
        trainers.update(p.id for p in q.holders_at_or_above(snapshot, capability.id, LEVEL_TEACHER))
    return count_metric(
        "locally_teachable",
        "Locally Teachable Capabilities",
        total=len(teachable),
        formula=(
            f"count(capabilities with >=1 local person at level "
            f"{LEVEL_TEACHER} ({TEACHER_LABEL}))"
        ),
        inputs={
            "threshold": f"{LEVEL_TEACHER} ({TEACHER_LABEL})",
            "teachable_capabilities": ids(c.id for c in teachable),
            "capabilities_considered": num(len(snapshot.capabilities)),
            "local_trainers": ids(trainers),
        },
        caption=f"of {len(snapshot.capabilities)} capabilities",
    )


def expert_dependent(snapshot: EngagementSnapshot) -> Metric:
    """Critical work that walks out of the door with the expert."""
    critical = q.critical_capabilities(snapshot)
    dependent = [
        c
        for c in critical
        if q.expert_is_capable(snapshot, c.id) and not q.is_localized(snapshot, c.id)
    ]
    return count_metric(
        "expert_dependent",
        "Expert-Dependent Capabilities",
        total=len(dependent),
        formula=(
            f"count(critical capabilities where an expert is at level >= "
            f"{LEVEL_INDEPENDENT} AND no local person is at level >= {LEVEL_INDEPENDENT})"
        ),
        inputs={
            "threshold": f"{LEVEL_INDEPENDENT} ({INDEPENDENT_LABEL})",
            "dependent_capabilities": ids(c.id for c in dependent),
            "critical_capabilities": ids(c.id for c in critical),
        },
        caption=f"of {len(critical)} critical capabilities",
    )


def local_trainers(snapshot: EngagementSnapshot) -> Metric:
    """Headcount of people who can teach at least one capability."""
    people: set[str] = set()
    for capability in snapshot.capabilities:
        people.update(p.id for p in q.holders_at_or_above(snapshot, capability.id, LEVEL_TEACHER))
    return count_metric(
        "local_trainers",
        "Local Trainers",
        total=len(people),
        formula=f"count(distinct local people at level {LEVEL_TEACHER} on any capability)",
        inputs={
            "threshold": f"{LEVEL_TEACHER} ({TEACHER_LABEL})",
            "trainers": ids(people),
            "local_people": ids(p.id for p in q.local_people(snapshot)),
        },
        caption="identified",
    )


# ---------------------------------------------------------------------------
# Area metrics
# ---------------------------------------------------------------------------


def local_ownership(snapshot: EngagementSnapshot) -> Metric:
    """Critical areas somebody local has been validated as owning."""
    critical = q.critical_areas(snapshot)
    owned = [a for a in critical if q.has_validated_local_owner(snapshot, a)]
    return ratio_metric(
        "local_ownership",
        "Local Ownership",
        numerator=len(owned),
        denominator=len(critical),
        formula="critical areas with a validated local owner / critical areas",
        inputs={
            "owned_areas": ids(a.id for a in owned),
            "critical_areas": ids(a.id for a in critical),
            "rule": "owner must exist, hold a local role, and be validated",
        },
        caption=f"{len(owned)} of {len(critical)} critical areas",
    )


def trainer_coverage(snapshot: EngagementSnapshot) -> Metric:
    """Critical areas that can train their own successors."""
    critical = q.critical_areas(snapshot)
    covered = [a for a in critical if q.area_trainers(snapshot, a)]
    return ratio_metric(
        "trainer_coverage",
        "Trainer Coverage",
        numerator=len(covered),
        denominator=len(critical),
        formula=(
            f"critical areas with >=1 local person at level {LEVEL_TEACHER} "
            f"on one of the area's capabilities / critical areas"
        ),
        inputs={
            "threshold": f"{LEVEL_TEACHER} ({TEACHER_LABEL})",
            "covered_areas": ids(a.id for a in covered),
            "critical_areas": ids(a.id for a in critical),
        },
        caption=f"{len(covered)} of {len(critical)} critical areas",
    )


# ---------------------------------------------------------------------------
# Requirement metrics
# ---------------------------------------------------------------------------


def _requirement_ratio(
    requirements: Sequence[Requirement],
    *,
    key: str,
    label: str,
    kinds: frozenset[RequirementKind],
    credit: Mapping[TransferState, float],
    require_validated: bool,
    caption_noun: str,
) -> Metric:
    """Shared body for formal/informal/per-kind coverage.

    `require_validated` is the difference section 4 B4 draws between the two
    halves: formal knowledge counts when it is marked complete, informal
    knowledge counts only when the capture was validated by a human.
    """
    in_scope = q.requirements_of_kinds(requirements, kinds)
    earned = 0.0
    counted: list[str] = []
    for requirement in in_scope:
        if require_validated and not requirement.validated:
            continue
        share = credit.get(requirement.state, 0.0)
        if share:
            earned += share
            counted.append(requirement.id)

    validation_clause = " with validated capture" if require_validated else ""
    return ratio_metric(
        key,
        label,
        numerator=earned,
        denominator=len(in_scope),
        formula=(
            f"{caption_noun} requirements{validation_clause} scored by transfer state "
            f"[{describe_credit(credit)}] / total {caption_noun} requirements"
        ),
        inputs={
            "kinds": ids(k.value for k in kinds),
            "state_credit": describe_credit(credit),
            "validation_required": "yes" if require_validated else "no",
            "counted_requirements": ids(counted),
            "requirements_in_scope": ids(r.id for r in in_scope),
        },
        caption=f"{num(earned)} of {len(in_scope)} {caption_noun} requirements",
    )


def formal_transfer(
    snapshot: EngagementSnapshot,
    *,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> Metric:
    """Documentable knowledge that has actually been handed over."""
    return _requirement_ratio(
        snapshot.requirements,
        key="formal_transfer",
        label="Formal Knowledge Transfer",
        kinds=FORMAL_KINDS,
        credit=credit,
        require_validated=False,
        caption_noun="formal",
    )


def informal_transfer(
    snapshot: EngagementSnapshot,
    *,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> Metric:
    """Judgment, relationships and tacit practice -- the half that is hard."""
    return _requirement_ratio(
        snapshot.requirements,
        key="informal_transfer",
        label="Informal Knowledge Transfer",
        kinds=INFORMAL_KINDS,
        credit=credit,
        require_validated=True,
        caption_noun="informal",
    )


def requirement_coverage(
    snapshot: EngagementSnapshot,
    *,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> Metric:
    """Every transfer requirement, of every kind, in one figure."""
    all_kinds = frozenset(RequirementKind)
    return _requirement_ratio(
        snapshot.requirements,
        key="requirement_coverage",
        label="Transfer Requirement Coverage",
        kinds=all_kinds,
        credit=credit,
        require_validated=False,
        caption_noun="transfer",
    )


def requirement_coverage_by_kind(
    snapshot: EngagementSnapshot,
    *,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> dict[RequirementKind, Metric]:
    """Per-kind coverage, in vocabulary order. Drives the blueprint breakdown."""
    return {
        kind: _requirement_ratio(
            snapshot.requirements,
            key=f"requirement_coverage.{kind.value}",
            label=f"{kind.value.title()} Coverage",
            kinds=frozenset({kind}),
            credit=credit,
            require_validated=False,
            caption_noun=kind.value,
        )
        for kind in RequirementKind
    }


# ---------------------------------------------------------------------------
# The composite
# ---------------------------------------------------------------------------

# The five components of the weighted expression, keyed by the weight they
# carry. Order is the order they appear in section 4 B4's formula.
COMPONENT_METRICS: dict[str, Callable[[EngagementSnapshot], Metric]] = {
    "local_ownership": local_ownership,
    "capability_localization": capability_localization,
    "formal_transfer": formal_transfer,
    "informal_transfer": informal_transfer,
    "trainer_coverage": trainer_coverage,
}


def readiness_components(snapshot: EngagementSnapshot) -> dict[str, Metric]:
    """The five weighted inputs, computed once so nothing recomputes them."""
    return {name: fn(snapshot) for name, fn in COMPONENT_METRICS.items()}


def operating_model_readiness(
    snapshot: EngagementSnapshot,
    *,
    weights: ReadinessWeights | None = None,
    components: Mapping[str, Metric] | None = None,
) -> Metric:
    """"Can the organization operate without the expert?" as one number.

    The popover has to let a reader rebuild the arithmetic, so `inputs` carries
    each component as `value x weight = contribution` rather than just the
    component's percentage.
    """
    resolved, provenance = resolve_weights(snapshot.weights, weights)
    parts = dict(components) if components is not None else readiness_components(snapshot)

    total = 0.0
    recorded: dict[str, str] = {}
    for name, weight in resolved.as_mapping().items():
        component = parts[name]
        contribution = component.value * weight
        total += contribution
        recorded[name] = (
            f"{percent(component.value)} x {num(weight)} = {num(round(contribution, 6))}"
        )
    recorded["weights"] = resolved.describe()
    recorded["weights_source"] = provenance

    return score_metric(
        "operating_model_readiness",
        "Operating Model Readiness",
        value=total,
        formula=resolved.describe(),
        inputs=recorded,
        caption="weighted transfer readiness",
    )


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------


def days_until_departure(snapshot: EngagementSnapshot) -> Metric:
    """Days from `snapshot.as_of` to the soonest expert departure.

    Reads the snapshot's date, never the clock -- a demo that renders a
    different number on Tuesday than it did in rehearsal is a defect.
    Returns 0 days with a note when no expert has a departure date.
    """
    departures = sorted(
        (p for p in q.experts(snapshot) if p.departure_date is not None),
        key=lambda p: (p.departure_date, p.id),  # type: ignore[arg-type,return-value]
    )
    if not departures:
        return days_metric(
            "days_until_departure",
            "Time Until Expert Departure",
            days=0,
            formula="departure_date - as_of",
            inputs={
                "as_of": snapshot.as_of.isoformat(),
                "note": "no expert on this engagement has a departure date",
            },
            caption="no departure scheduled",
        )

    soonest = departures[0]
    assert soonest.departure_date is not None
    remaining = (soonest.departure_date - snapshot.as_of).days
    return days_metric(
        "days_until_departure",
        "Time Until Expert Departure",
        days=remaining,
        formula="departure_date - as_of",
        inputs={
            "departure_date": soonest.departure_date.isoformat(),
            "as_of": snapshot.as_of.isoformat(),
            "expert_id": soonest.id,
        },
        caption="until departure",
    )
