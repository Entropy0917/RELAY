"""Knowledge at risk -- what disappears when the expert leaves.

RELAY.txt ("KNOWLEDGE AT RISK") names seven things to flag. Each becomes one
`RiskKind` below, each finding carries its own `inputs` and `formula`, and the
severity is a `Status` so the whole register renders through the same status
component as everything else.

Findings carry ids and names taken from the snapshot; the phrasing is built
from product vocabulary alone, so the register reads the same for any sector
(planv0.2.md section 0.5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    LEVEL_INDEPENDENT,
    LEVEL_TEACHER,
    KnowledgeType,
    RequirementKind,
    Status,
    TransferState,
)

from app.readiness import _query as q
from app.readiness.explain import Metric, count_metric, ids
from app.readiness.inputs import EngagementSnapshot
from app.readiness.weights import INFORMAL_KINDS


class RiskKind(StrEnum):
    """One per flag in RELAY.txt's knowledge-at-risk list."""

    NO_LOCAL_COVERAGE = "no_local_coverage"
    NO_LOCAL_OWNER = "no_local_owner"
    UNDOCUMENTED_TACIT = "undocumented_tacit"
    OBSERVED_NEVER_PERFORMED = "observed_never_performed"
    SINGLE_KNOWLEDGE_HOLDER = "single_knowledge_holder"
    EXPERT_DEPENDENT_RELATIONSHIP = "expert_dependent_relationship"
    NO_LOCAL_TRAINER = "no_local_trainer"


# Severity per kind. CRITICAL is "this capability or area has no local floor at
# all"; AT_RISK is "something local exists but will not survive departure";
# IN_PROGRESS is "transferring, but thin". Exported so an engagement can argue.
RISK_SEVERITY: dict[RiskKind, Status] = {
    RiskKind.NO_LOCAL_COVERAGE: Status.CRITICAL,
    RiskKind.NO_LOCAL_OWNER: Status.CRITICAL,
    RiskKind.UNDOCUMENTED_TACIT: Status.AT_RISK,
    RiskKind.OBSERVED_NEVER_PERFORMED: Status.AT_RISK,
    RiskKind.SINGLE_KNOWLEDGE_HOLDER: Status.IN_PROGRESS,
    RiskKind.EXPERT_DEPENDENT_RELATIONSHIP: Status.IN_PROGRESS,
    RiskKind.NO_LOCAL_TRAINER: Status.IN_PROGRESS,
}

# Worst first, then by kind, then by subject -- a stable order, so two runs of
# the same snapshot produce the same register.
SEVERITY_ORDER: list[Status] = [Status.CRITICAL, Status.AT_RISK, Status.IN_PROGRESS]
_KIND_ORDER = list(RiskKind)


@dataclass(frozen=True)
class RiskFinding:
    """One flagged risk. `value` is the severity -- named so it explains itself
    exactly like every metric in this package does."""

    kind: RiskKind
    value: Status
    scope: str  # "capability" | "area" | "requirement"
    subject_id: str
    subject_name: str
    detail: str
    formula: str
    inputs: dict[str, str] = field(default_factory=dict)

    @property
    def severity(self) -> Status:
        return self.value


@dataclass(frozen=True)
class RiskRegister:
    """The findings plus a headline count, so a tile can show it directly."""

    findings: tuple[RiskFinding, ...]
    count: Metric

    def by_severity(self, severity: Status) -> tuple[RiskFinding, ...]:
        return tuple(f for f in self.findings if f.value is severity)


def _level_label(level: int) -> str:
    return CAPABILITY_LEVELS[level] if 0 <= level < len(CAPABILITY_LEVELS) else "none on record"


def knowledge_at_risk(snapshot: EngagementSnapshot) -> RiskRegister:
    """Everything RELAY.txt asks to be flagged before the expert departs."""
    findings: list[RiskFinding] = []

    for capability in q.critical_capabilities(snapshot):
        best = q.max_local_level(snapshot, capability.id)
        independent = q.holders_at_or_above(snapshot, capability.id, LEVEL_INDEPENDENT)
        expert_capable = q.expert_is_capable(snapshot, capability.id)

        if not independent:
            findings.append(
                RiskFinding(
                    kind=RiskKind.NO_LOCAL_COVERAGE,
                    value=RISK_SEVERITY[RiskKind.NO_LOCAL_COVERAGE],
                    scope="capability",
                    subject_id=capability.id,
                    subject_name=capability.name,
                    detail=(
                        "No local person has demonstrated this capability "
                        "independently."
                    ),
                    formula=(
                        f"critical capability with no local person at level >= "
                        f"{LEVEL_INDEPENDENT}"
                    ),
                    inputs={
                        "best_local_level": f"{best} ({_level_label(best)})",
                        "threshold": str(LEVEL_INDEPENDENT),
                        "expert_capable": "yes" if expert_capable else "no",
                    },
                )
            )
            if 0 <= best < 3:
                findings.append(
                    RiskFinding(
                        kind=RiskKind.OBSERVED_NEVER_PERFORMED,
                        value=RISK_SEVERITY[RiskKind.OBSERVED_NEVER_PERFORMED],
                        scope="capability",
                        subject_id=capability.id,
                        subject_name=capability.name,
                        detail=(
                            "Local exposure has not progressed past supervised "
                            "practice."
                        ),
                        formula="critical capability where the best local level is below 3",
                        inputs={"best_local_level": f"{best} ({_level_label(best)})"},
                    )
                )
        elif len(independent) == 1:
            findings.append(
                RiskFinding(
                    kind=RiskKind.SINGLE_KNOWLEDGE_HOLDER,
                    value=RISK_SEVERITY[RiskKind.SINGLE_KNOWLEDGE_HOLDER],
                    scope="capability",
                    subject_id=capability.id,
                    subject_name=capability.name,
                    detail="Exactly one local person can perform this independently.",
                    formula=(
                        f"critical capability with exactly one local person at level >= "
                        f"{LEVEL_INDEPENDENT}"
                    ),
                    inputs={
                        "holders": ids(p.id for p in independent),
                        "teachers": ids(
                            p.id
                            for p in q.holders_at_or_above(
                                snapshot, capability.id, LEVEL_TEACHER
                            )
                        ),
                    },
                )
            )

    for area in q.critical_areas(snapshot):
        if not q.has_validated_local_owner(snapshot, area):
            findings.append(
                RiskFinding(
                    kind=RiskKind.NO_LOCAL_OWNER,
                    value=RISK_SEVERITY[RiskKind.NO_LOCAL_OWNER],
                    scope="area",
                    subject_id=area.id,
                    subject_name=area.name,
                    detail="This area has no validated local owner.",
                    formula="critical area where no validated local owner is recorded",
                    inputs={
                        "owner_id": area.local_owner_id or "(none)",
                        "owner_validated": "yes" if area.owner_validated else "no",
                    },
                )
            )
        if not q.area_trainers(snapshot, area):
            findings.append(
                RiskFinding(
                    kind=RiskKind.NO_LOCAL_TRAINER,
                    value=RISK_SEVERITY[RiskKind.NO_LOCAL_TRAINER],
                    scope="area",
                    subject_id=area.id,
                    subject_name=area.name,
                    detail="This area cannot yet train its own successors.",
                    formula=(
                        f"critical area with no local person at level {LEVEL_TEACHER} "
                        f"on any of its capabilities"
                    ),
                    inputs={"area_capabilities": ids(area.capability_ids)},
                )
            )

    documented = {
        item.capability_id
        for item in snapshot.knowledge
        if item.validated and item.capability_id is not None
    }

    for requirement in sorted(snapshot.requirements, key=lambda r: r.id):
        if requirement.kind not in INFORMAL_KINDS:
            continue
        transferred = requirement.state is TransferState.COMPLETE and requirement.validated
        if not transferred:
            findings.append(
                RiskFinding(
                    kind=RiskKind.UNDOCUMENTED_TACIT,
                    value=RISK_SEVERITY[RiskKind.UNDOCUMENTED_TACIT],
                    scope="requirement",
                    subject_id=requirement.id,
                    subject_name=requirement.kind.value,
                    detail="Tacit knowledge with no validated local capture.",
                    formula=(
                        "informal requirement that is not complete, or is complete "
                        "but unvalidated"
                    ),
                    inputs={
                        "kind": requirement.kind.value,
                        "state": requirement.state.value,
                        "validated": "yes" if requirement.validated else "no",
                        "area_id": requirement.area_id,
                        "capability_documented": (
                            "yes" if requirement.capability_id in documented else "no"
                        ),
                    },
                )
            )
        if (
            requirement.kind is RequirementKind.RELATIONSHIP
            and requirement.state is not TransferState.COMPLETE
        ):
            findings.append(
                RiskFinding(
                    kind=RiskKind.EXPERT_DEPENDENT_RELATIONSHIP,
                    value=RISK_SEVERITY[RiskKind.EXPERT_DEPENDENT_RELATIONSHIP],
                    scope="requirement",
                    subject_id=requirement.id,
                    subject_name=requirement.kind.value,
                    detail="External relationships still run through the expert.",
                    formula="relationship requirement whose transfer state is not complete",
                    inputs={
                        "state": requirement.state.value,
                        "area_id": requirement.area_id,
                    },
                )
            )

    ordered = tuple(
        sorted(
            findings,
            key=lambda f: (
                SEVERITY_ORDER.index(f.value),
                _KIND_ORDER.index(f.kind),
                f.subject_id,
            ),
        )
    )

    counts = {severity: sum(1 for f in ordered if f.value is severity) for severity in SEVERITY_ORDER}
    count = count_metric(
        "knowledge_at_risk",
        "Knowledge at Risk",
        total=len(ordered),
        formula=(
            "count of flagged risks: no local coverage, no local owner, "
            "undocumented tacit knowledge, exposure that never became practice, "
            "a single local holder, expert-dependent relationships, no local trainer"
        ),
        inputs={
            **{f"{s.value}_count": str(n) for s, n in counts.items()},
            "kinds_checked": ids(k.value for k in RiskKind),
        },
        caption="items flagged before departure",
    )

    return RiskRegister(findings=ordered, count=count)


def validated_knowledge_count(snapshot: EngagementSnapshot) -> Metric:
    """Validated library entries -- the counterweight to the risk register."""
    validated = [item for item in snapshot.knowledge if item.validated]
    by_type = {t: sum(1 for i in validated if i.type is t) for t in KnowledgeType}
    return count_metric(
        "validated_knowledge",
        "Validated Knowledge Items",
        total=len(validated),
        formula="count(knowledge items where validated is true)",
        inputs={
            **{f"{t.value}_count": str(n) for t, n in by_type.items() if n},
            "total_items": str(len(snapshot.knowledge)),
        },
        caption="captured and validated",
    )
