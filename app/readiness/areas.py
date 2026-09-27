"""Per-area readiness -- the same weighted expression, narrowed to one area.

RELAY.txt's operating-model view is a table of areas with formal %, informal %,
a local owner, trainer coverage and a status. That is planv0.2.md section 4 B4's
five components with the two area-level ones collapsing to 0 or 1: an area
either has a validated local owner or it does not.

Running the identical expression rather than a parallel one is what guarantees
the area cards and the headline number can never tell different stories.

`AreaReadiness` is shaped for contracts.viewmodels.AreaCard: formal_pct,
informal_pct, local_capability, trainer_coverage, status, status_label all come
straight off it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from contracts.vocabulary import LEVEL_INDEPENDENT, LEVEL_TEACHER, Status, TransferState

from app.readiness import _query as q
from app.readiness.explain import (
    Metric,
    Verdict,
    ids,
    num,
    percent,
    ratio_metric,
    score_metric,
)
from app.readiness.inputs import Area, EngagementSnapshot
from app.readiness.status import (
    DEFAULT_STATUS_THRESHOLDS,
    StatusThresholds,
    derive_local_capability,
    derive_status,
)
from app.readiness.metrics import _requirement_ratio
from app.readiness.weights import (
    FORMAL_KINDS,
    INFORMAL_KINDS,
    STRICT_CREDIT,
    ReadinessWeights,
    resolve_weights,
)


@dataclass(frozen=True)
class AreaReadiness:
    """One area's readiness, with every contributing number still attached."""

    area_id: str
    area_name: str
    readiness: Metric
    status: Verdict[Status]
    local_capability: Verdict[str]
    components: Mapping[str, Metric]

    @property
    def formal(self) -> Metric:
        return self.components["formal_transfer"]

    @property
    def informal(self) -> Metric:
        return self.components["informal_transfer"]

    @property
    def has_trainer(self) -> bool:
        return self.components["trainer_coverage"].value >= 1.0

    @property
    def has_local_owner(self) -> bool:
        return self.components["local_ownership"].value >= 1.0

    def as_card(self) -> dict[str, object]:
        """Keyword arguments for contracts.viewmodels.AreaCard, minus local_owner.

        Percentages are whole numbers because AreaCard constrains them to
        0-100 ints; `readiness` keeps the exact value for anyone who needs it.
        """
        return {
            "id": self.area_id,
            "name": self.area_name,
            "formal_pct": int(self.formal.value * 100 + 0.5),
            "informal_pct": int(self.informal.value * 100 + 0.5),
            "local_capability": self.local_capability.value,
            "trainer_coverage": self.has_trainer,
            "status": self.status.value,
            "status_label": self.status.label,
        }


def area_local_ownership(snapshot: EngagementSnapshot, area: Area) -> Metric:
    owned = q.has_validated_local_owner(snapshot, area)
    owner = snapshot.person(area.local_owner_id) if area.local_owner_id else None
    return ratio_metric(
        "local_ownership",
        "Local Ownership",
        numerator=1 if owned else 0,
        denominator=1,
        formula="1 when the area has a validated local owner, else 0",
        inputs={
            "owner_id": area.local_owner_id or "(none)",
            "owner_is_local": "yes" if owner is not None and owner.is_local else "no",
            "owner_validated": "yes" if area.owner_validated else "no",
        },
        caption="owned locally" if owned else "no validated local owner",
    )


def area_capability_localization(snapshot: EngagementSnapshot, area: Area) -> Metric:
    critical = [c for c in q.area_capabilities(snapshot, area) if c.critical]
    localized = [c for c in critical if q.is_localized(snapshot, c.id)]
    return ratio_metric(
        "capability_localization",
        "Capability Localization",
        numerator=len(localized),
        denominator=len(critical),
        formula=(
            f"the area's critical capabilities with >=1 local person at level >= "
            f"{LEVEL_INDEPENDENT} / the area's critical capabilities"
        ),
        inputs={
            "localized_capabilities": ids(c.id for c in localized),
            "area_critical_capabilities": ids(c.id for c in critical),
        },
        caption=f"{len(localized)} of {len(critical)} capabilities",
    )


def area_trainer_coverage(snapshot: EngagementSnapshot, area: Area) -> Metric:
    trainers = q.area_trainers(snapshot, area)
    return ratio_metric(
        "trainer_coverage",
        "Trainer Coverage",
        numerator=1 if trainers else 0,
        denominator=1,
        formula=(
            f"1 when >=1 local person is at level {LEVEL_TEACHER} on one of the "
            f"area's capabilities, else 0"
        ),
        inputs={
            "trainers": ids(p.id for p in trainers),
            "area_capabilities": ids(area.capability_ids),
        },
        caption=f"{len(trainers)} local trainer(s)",
    )


def area_readiness(
    snapshot: EngagementSnapshot,
    area: Area,
    *,
    weights: ReadinessWeights | None = None,
    thresholds: StatusThresholds = DEFAULT_STATUS_THRESHOLDS,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> AreaReadiness:
    """The whole card for one area, every number carrying its own arithmetic."""
    resolved, provenance = resolve_weights(snapshot.weights, weights)
    requirements = q.area_requirements(snapshot, area)

    components: dict[str, Metric] = {
        "local_ownership": area_local_ownership(snapshot, area),
        "capability_localization": area_capability_localization(snapshot, area),
        "formal_transfer": _requirement_ratio(
            requirements,
            key="formal_transfer",
            label="Formal Knowledge Transfer",
            kinds=FORMAL_KINDS,
            credit=credit,
            require_validated=False,
            caption_noun="formal",
        ),
        "informal_transfer": _requirement_ratio(
            requirements,
            key="informal_transfer",
            label="Informal Knowledge Transfer",
            kinds=INFORMAL_KINDS,
            credit=credit,
            require_validated=True,
            caption_noun="informal",
        ),
        "trainer_coverage": area_trainer_coverage(snapshot, area),
    }

    total = 0.0
    recorded: dict[str, str] = {}
    for name, weight in resolved.as_mapping().items():
        contribution = components[name].value * weight
        total += contribution
        recorded[name] = (
            f"{percent(components[name].value)} x {num(weight)} = "
            f"{num(round(contribution, 6))}"
        )
    recorded["weights"] = resolved.describe()
    recorded["weights_source"] = provenance
    recorded["area_id"] = area.id

    readiness = score_metric(
        "area_readiness",
        f"{area.name} Readiness",
        value=total,
        formula=resolved.describe(),
        inputs=recorded,
        caption="weighted transfer readiness",
    )

    best_level = max(
        (q.max_local_level(snapshot, cid) for cid in area.capability_ids),
        default=-1,
    )

    return AreaReadiness(
        area_id=area.id,
        area_name=area.name,
        readiness=readiness,
        status=derive_status(total, thresholds=thresholds, key="area_status"),
        local_capability=derive_local_capability(
            localization=components["capability_localization"].value,
            best_local_level=best_level,
        ),
        components=components,
    )


def all_area_readiness(
    snapshot: EngagementSnapshot,
    *,
    weights: ReadinessWeights | None = None,
    thresholds: StatusThresholds = DEFAULT_STATUS_THRESHOLDS,
    credit: Mapping[TransferState, float] = STRICT_CREDIT,
) -> list[AreaReadiness]:
    """Every area, worst first -- the order the product wants to show them in."""
    scored = [
        area_readiness(snapshot, area, weights=weights, thresholds=thresholds, credit=credit)
        for area in sorted(snapshot.areas, key=lambda a: a.id)
    ]
    return sorted(scored, key=lambda r: (r.readiness.value, r.area_id))
