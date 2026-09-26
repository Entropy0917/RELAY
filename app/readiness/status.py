"""Turning a readiness score into one of the five statuses -- explainably.

planv0.2.md section 4 B4 gives the formula but no threshold table, and
RELAY.txt names the five states without numbers. The defaults below are
calibrated so that the five worked operating-model areas in RELAY.txt
(section "Operating Model view") come out with the statuses that document
assigns them when their figures are run through the weighted expression:

    formal/informal/owner/trainer     score   spec says
    100% / 90% / owned / trainer      0.98    SUSTAINABLE
    100% / 80% / owned / trainer      0.96    SUSTAINABLE
     90% / 65% / owned / no trainer   0.515   TRANSFER IN PROGRESS
     85% / 45% / owned / no trainer   0.468   TRANSFER IN PROGRESS
     75% / 30% / no owner / none      0.173   AT RISK

Nothing in the source fixes the CRITICAL boundary, so it sits below the worst
worked example. Thresholds are a parameter with a default, like the weights,
and the band that fired is reported in `inputs` -- the reader never has to
guess which rule applied.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.vocabulary import STATUS_LABEL, Status

from app.readiness.explain import Verdict, num, percent


@dataclass(frozen=True)
class StatusThresholds:
    """Lower bounds, inclusive, checked from the top down."""

    sustainable: float = 0.90
    on_track: float = 0.75
    in_progress: float = 0.40
    at_risk: float = 0.15

    def __post_init__(self) -> None:
        ordered = [self.sustainable, self.on_track, self.in_progress, self.at_risk]
        if ordered != sorted(ordered, reverse=True):
            raise ValueError(f"status thresholds must descend, got {ordered}")

    def bands(self) -> list[tuple[Status, float]]:
        return [
            (Status.SUSTAINABLE, self.sustainable),
            (Status.ON_TRACK, self.on_track),
            (Status.IN_PROGRESS, self.in_progress),
            (Status.AT_RISK, self.at_risk),
        ]

    def describe(self) -> str:
        parts = [f"score >= {num(low)} -> {status.value}" for status, low in self.bands()]
        return "; ".join(parts) + f"; else {Status.CRITICAL.value}"


DEFAULT_STATUS_THRESHOLDS = StatusThresholds()


# RELAY.txt shows each area's local capability as Strong / Developing / Limited
# alongside its status. These are product vocabulary, not engagement data, but
# they are not in contracts/vocabulary.py -- moving them there is a contract
# change and needs both owners, so they live here for now.
LOCAL_CAPABILITY_STRONG = "Strong"
LOCAL_CAPABILITY_DEVELOPING = "Developing"
LOCAL_CAPABILITY_LIMITED = "Limited"

# Lowest level that still counts as "Developing" rather than "Limited": the
# person has at least assisted, so there is something to build on.
LEVEL_DEVELOPING = 2


def derive_status(
    score: float,
    *,
    thresholds: StatusThresholds = DEFAULT_STATUS_THRESHOLDS,
    key: str = "status",
) -> Verdict[Status]:
    """Map a 0.0-1.0 readiness score onto a Status, showing the band that fired."""
    for status, low in thresholds.bands():
        if score >= low:
            fired = status
            bound = f"score {percent(score)} >= {num(low)}"
            break
    else:
        fired = Status.CRITICAL
        bound = f"score {percent(score)} < {num(thresholds.at_risk)}"

    return Verdict(
        key=key,
        value=fired,
        label=STATUS_LABEL[fired],
        formula=thresholds.describe(),
        inputs={
            "score": percent(score),
            "score_exact": num(score),
            "band": bound,
            "thresholds": thresholds.describe(),
        },
    )


def derive_local_capability(
    *,
    localization: float,
    best_local_level: int,
    key: str = "local_capability",
) -> Verdict[str]:
    """Strong / Developing / Limited for one area, per RELAY.txt's area cards.

    Strong means every one of the area's critical capabilities has a local
    person at LEVEL_INDEPENDENT. Developing means some progress exists --
    either partial localization or somebody at least assisting. Otherwise the
    area is Limited.
    """
    if localization >= 1.0 and best_local_level >= 0:
        band = LOCAL_CAPABILITY_STRONG
    elif localization > 0.0 or best_local_level >= LEVEL_DEVELOPING:
        band = LOCAL_CAPABILITY_DEVELOPING
    else:
        band = LOCAL_CAPABILITY_LIMITED

    return Verdict(
        key=key,
        value=band,
        label=band,
        formula=(
            f"all capabilities localized -> {LOCAL_CAPABILITY_STRONG}; "
            f"any localized or best local level >= {LEVEL_DEVELOPING} -> "
            f"{LOCAL_CAPABILITY_DEVELOPING}; else {LOCAL_CAPABILITY_LIMITED}"
        ),
        inputs={
            "capability_localization": percent(localization),
            "best_local_level": str(best_local_level) if best_local_level >= 0 else "none on record",
            "developing_level": str(LEVEL_DEVELOPING),
        },
    )
