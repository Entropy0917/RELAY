"""Departure readiness -- the executive answer, in the shape RELAY.txt asks for.

RELAY.txt's Departure Readiness view is a header (the expert, days remaining)
over five counts: areas locally owned, critical capabilities available locally,
local trainers, validated insights, open risks. Each is assembled here from the
metrics that already exist rather than recounted, so this view can never
disagree with the readiness page.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.vocabulary import Status

from app.readiness import _query as q
from app.readiness.explain import Metric, Verdict, count_metric, ids
from app.readiness.inputs import EngagementSnapshot, Person
from app.readiness.metrics import (
    capability_localization,
    days_until_departure,
    local_ownership,
    local_trainers,
    operating_model_readiness,
)
from app.readiness.risk import knowledge_at_risk, validated_knowledge_count
from app.readiness.status import DEFAULT_STATUS_THRESHOLDS, StatusThresholds, derive_status
from app.readiness.weights import ReadinessWeights


@dataclass(frozen=True)
class DepartureReadiness:
    """Everything the Departure Readiness header and its five tiles need."""

    expert: Person | None
    days_remaining: Metric
    readiness: Metric
    status: Verdict[Status]
    areas_locally_owned: Metric
    capabilities_localized: Metric
    local_trainers: Metric
    validated_knowledge: Metric
    open_risks: Metric

    def tiles(self) -> list[Metric]:
        """In the order RELAY.txt lists them."""
        return [
            self.readiness,
            self.capabilities_localized,
            self.areas_locally_owned,
            self.local_trainers,
            self.validated_knowledge,
            self.open_risks,
            self.days_remaining,
        ]


def departing_expert(snapshot: EngagementSnapshot) -> Person | None:
    """The expert leaving soonest. None when nobody has a departure date."""
    dated = [p for p in q.experts(snapshot) if p.departure_date is not None]
    if not dated:
        return None
    return sorted(dated, key=lambda p: (p.departure_date, p.id))[0]  # type: ignore[arg-type,return-value]


def departure_readiness(
    snapshot: EngagementSnapshot,
    *,
    weights: ReadinessWeights | None = None,
    thresholds: StatusThresholds = DEFAULT_STATUS_THRESHOLDS,
) -> DepartureReadiness:
    """"Can the organization operate without the expert?", assembled."""
    readiness = operating_model_readiness(snapshot, weights=weights)
    register = knowledge_at_risk(snapshot)

    # RELAY.txt shows these as "7 / 9" counts, not percentages, so the ratio
    # metric's numerator is re-presented as a count. Same source, same formula.
    critical_areas = q.critical_areas(snapshot)
    owned = local_ownership(snapshot)
    areas_owned = count_metric(
        "areas_locally_owned",
        "Operating Model Areas",
        total=sum(1 for a in critical_areas if q.has_validated_local_owner(snapshot, a)),
        formula=owned.formula,
        inputs=dict(owned.inputs),
        caption=f"of {len(critical_areas)} locally owned",
    )

    critical = q.critical_capabilities(snapshot)
    localized = capability_localization(snapshot)
    caps_localized = count_metric(
        "capabilities_localized",
        "Critical Capabilities",
        total=sum(1 for c in critical if q.is_localized(snapshot, c.id)),
        formula=localized.formula,
        inputs=dict(localized.inputs),
        caption=f"of {len(critical)} independently available locally",
    )

    expert = departing_expert(snapshot)
    return DepartureReadiness(
        expert=expert,
        days_remaining=days_until_departure(snapshot),
        readiness=readiness,
        status=derive_status(readiness.value, thresholds=thresholds, key="departure_status"),
        areas_locally_owned=areas_owned,
        capabilities_localized=caps_localized,
        local_trainers=local_trainers(snapshot),
        validated_knowledge=validated_knowledge_count(snapshot),
        open_risks=count_metric(
            "open_risks",
            "Open Risks",
            total=len(register.findings),
            formula=register.count.formula,
            inputs={
                **dict(register.count.inputs),
                "subjects": ids(f.subject_id for f in register.findings),
            },
            caption="flagged before departure",
        ),
    )
