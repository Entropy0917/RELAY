"""RELAY readiness engine -- deterministic, explainable, and database-free.

planv0.2.md section 4 B4: pure functions, no AI, no I/O. Every public function
returns a result carrying `value`, `inputs` and `formula`, so the UI can render
"how this is calculated" straight from what it was handed and a reader can
rebuild the arithmetic without opening this package.

Three properties this package holds on purpose:

  * **No database.** Scoring reads `inputs.EngagementSnapshot`, a frozen
    dataclass the service layer fills from rows. Nothing here imports
    SQLAlchemy, sqlite3, Flask or app.db, so B4 was never blocked on B1 and
    scoring can never issue a query.
  * **No clock.** `EngagementSnapshot.as_of` is the only "today" there is.
    Demo-day numbers are reproducible; tests are not time-bombs.
  * **No engagement content.** Names and labels arrive in the snapshot
    (section 0.5). Nothing sector-specific is written here.

Typical use from the service layer:

    snapshot = build_snapshot(engagement_id, as_of=today)
    tiles = [m.as_tile() for m in headline_metrics(snapshot)]
"""

from __future__ import annotations

from collections.abc import Callable

from app.readiness.areas import (
    AreaReadiness,
    all_area_readiness,
    area_capability_localization,
    area_local_ownership,
    area_readiness,
    area_trainer_coverage,
)
from app.readiness.departure import (
    DepartureReadiness,
    departing_expert,
    departure_readiness,
)
from app.readiness.explain import (
    EMPTY_DENOMINATOR_NOTE,
    Explained,
    Metric,
    Verdict,
    percent,
)
from app.readiness.inputs import (
    LOCAL_ROLES,
    MAX_LEVEL,
    Area,
    Capability,
    CapabilityLevel,
    EngagementSnapshot,
    KnowledgeItem,
    Person,
    Requirement,
)
from app.readiness.metrics import (
    COMPONENT_METRICS,
    capability_localization,
    days_until_departure,
    expert_dependent,
    formal_transfer,
    informal_transfer,
    local_ownership,
    local_trainers,
    locally_teachable,
    operating_model_readiness,
    readiness_components,
    requirement_coverage,
    requirement_coverage_by_kind,
    trainer_coverage,
)
from app.readiness.risk import (
    RISK_SEVERITY,
    RiskFinding,
    RiskKind,
    RiskRegister,
    knowledge_at_risk,
    validated_knowledge_count,
)
from app.readiness.status import (
    DEFAULT_STATUS_THRESHOLDS,
    LOCAL_CAPABILITY_DEVELOPING,
    LOCAL_CAPABILITY_LIMITED,
    LOCAL_CAPABILITY_STRONG,
    StatusThresholds,
    derive_local_capability,
    derive_status,
)
from app.readiness.weights import (
    DEFAULT_WEIGHTS,
    FORMAL_KINDS,
    INFORMAL_KINDS,
    PARTIAL_CREDIT,
    STRICT_CREDIT,
    ReadinessWeights,
    resolve_weights,
)

# Metrics that need nothing but a snapshot. The registry exists so callers --
# and tests -- can iterate the surface instead of listing it by hand, which is
# what stops an unexplained metric being added later without anyone noticing.
SNAPSHOT_METRICS: dict[str, Callable[[EngagementSnapshot], Metric]] = {
    "capability_localization": capability_localization,
    "locally_teachable": locally_teachable,
    "expert_dependent": expert_dependent,
    "local_trainers": local_trainers,
    "local_ownership": local_ownership,
    "trainer_coverage": trainer_coverage,
    "formal_transfer": formal_transfer,
    "informal_transfer": informal_transfer,
    "requirement_coverage": requirement_coverage,
    "days_until_departure": days_until_departure,
    "operating_model_readiness": operating_model_readiness,
}

# The executive row, in the order RELAY.txt's EXECUTIVE METRICS section lists it.
HEADLINE_KEYS: tuple[str, ...] = (
    "operating_model_readiness",
    "capability_localization",
    "locally_teachable",
    "expert_dependent",
    "days_until_departure",
)


def headline_metrics(
    snapshot: EngagementSnapshot, *, weights: ReadinessWeights | None = None
) -> list[Metric]:
    """The executive metrics row. Maps onto MetricTile via `Metric.as_tile()`."""
    out: list[Metric] = []
    for key in HEADLINE_KEYS:
        if key == "operating_model_readiness":
            out.append(operating_model_readiness(snapshot, weights=weights))
        else:
            out.append(SNAPSHOT_METRICS[key](snapshot))
    return out


def all_metrics(
    snapshot: EngagementSnapshot, *, weights: ReadinessWeights | None = None
) -> dict[str, Metric]:
    """Every snapshot-level metric, keyed. The Readiness page's full set."""
    computed = {name: fn(snapshot) for name, fn in SNAPSHOT_METRICS.items()}
    computed["operating_model_readiness"] = operating_model_readiness(
        snapshot, weights=weights
    )
    return computed


__all__ = [
    # results
    "AreaReadiness",
    "DepartureReadiness",
    "Explained",
    "Metric",
    "RiskFinding",
    "RiskKind",
    "RiskRegister",
    "Verdict",
    # inputs
    "Area",
    "Capability",
    "CapabilityLevel",
    "EngagementSnapshot",
    "KnowledgeItem",
    "Person",
    "Requirement",
    "LOCAL_ROLES",
    "MAX_LEVEL",
    # constants
    "COMPONENT_METRICS",
    "DEFAULT_STATUS_THRESHOLDS",
    "DEFAULT_WEIGHTS",
    "EMPTY_DENOMINATOR_NOTE",
    "FORMAL_KINDS",
    "HEADLINE_KEYS",
    "INFORMAL_KINDS",
    "LOCAL_CAPABILITY_DEVELOPING",
    "LOCAL_CAPABILITY_LIMITED",
    "LOCAL_CAPABILITY_STRONG",
    "PARTIAL_CREDIT",
    "RISK_SEVERITY",
    "SNAPSHOT_METRICS",
    "STRICT_CREDIT",
    "ReadinessWeights",
    "StatusThresholds",
    # metrics
    "all_area_readiness",
    "all_metrics",
    "area_capability_localization",
    "area_local_ownership",
    "area_readiness",
    "area_trainer_coverage",
    "capability_localization",
    "days_until_departure",
    "departing_expert",
    "departure_readiness",
    "derive_local_capability",
    "derive_status",
    "expert_dependent",
    "formal_transfer",
    "headline_metrics",
    "informal_transfer",
    "knowledge_at_risk",
    "local_ownership",
    "local_trainers",
    "locally_teachable",
    "operating_model_readiness",
    "percent",
    "readiness_components",
    "requirement_coverage",
    "requirement_coverage_by_kind",
    "resolve_weights",
    "trainer_coverage",
    "validated_knowledge_count",
]
