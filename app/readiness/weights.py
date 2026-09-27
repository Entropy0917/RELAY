"""Readiness weights, and the requirement groupings the formula runs over.

planv0.2.md section 0.5 draws the line precisely here: the *shape* of the
readiness expression is the product and lives in code; the *weights* are
tenant data and live in the database, tunable per engagement. So weights are a
parameter with a documented default -- never a literal inside a function.

Resolution order everywhere in this package is:

    explicit argument  >  snapshot.weights (from the database)  >  DEFAULT_WEIGHTS

DEFAULT_WEIGHTS is verbatim planv0.2.md section 4 B4. The UI surfaces
`describe()` in the "how this is calculated" popover, so if an engagement tunes
its weights the popover changes with it and the number stays honest.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields

from contracts.vocabulary import RequirementKind, TransferState

WEIGHT_SUM_TOLERANCE = 1e-9


@dataclass(frozen=True)
class ReadinessWeights:
    """The five components of operating_model_readiness. Must sum to 1.0."""

    local_ownership: float = 0.25
    capability_localization: float = 0.30
    formal_transfer: float = 0.15
    informal_transfer: float = 0.20
    trainer_coverage: float = 0.10

    def __post_init__(self) -> None:
        negative = [k for k, v in self.as_mapping().items() if v < 0]
        if negative:
            raise ValueError(f"readiness weights cannot be negative: {negative}")
        total = sum(self.as_mapping().values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            # A set that does not sum to 1 produces a score that cannot reach
            # 100% (or exceeds it), which would make every downstream status
            # wrong. Fail at the boundary, not three screens later.
            raise ValueError(f"readiness weights must sum to 1.0, got {total:g}")

    def as_mapping(self) -> dict[str, float]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def describe(self) -> str:
        """The weighted expression, for the popover. Reads as the spec reads."""
        return " + ".join(f"{w:g}*{name}" for name, w in self.as_mapping().items())


DEFAULT_WEIGHTS = ReadinessWeights()


def resolve_weights(
    snapshot_weights: ReadinessWeights | None,
    override: ReadinessWeights | None = None,
) -> tuple[ReadinessWeights, str]:
    """Pick the weight set and say where it came from.

    The provenance string goes into `inputs` so a reader of the popover can
    tell a tuned engagement from a default one without asking anybody.
    """
    if override is not None:
        return override, "explicit override"
    if snapshot_weights is not None:
        return snapshot_weights, "engagement (database)"
    return DEFAULT_WEIGHTS, "default"


# ---------------------------------------------------------------------------
# Requirement groupings
# ---------------------------------------------------------------------------
# section 4 B4 speaks of "formal" and "informal" requirements, but the frozen
# vocabulary has seven kinds. The split below is the product's reading of that:
# a requirement is *formal* when it can be written down and handed over, and
# *informal* when it only exists in someone's judgment, memory or standing with
# other people. Both sets are exported so an engagement that disagrees can say
# so at the call site rather than by editing this module.

FORMAL_KINDS: frozenset[RequirementKind] = frozenset(
    {
        RequirementKind.FORMAL,
        RequirementKind.TECHNICAL,
        RequirementKind.TOOL,
        RequirementKind.GOVERNANCE,
    }
)

INFORMAL_KINDS: frozenset[RequirementKind] = frozenset(
    {
        RequirementKind.TACIT,
        RequirementKind.JUDGMENT,
        RequirementKind.RELATIONSHIP,
    }
)


# How much a requirement's TransferState is worth. STRICT is section 4 B4 read
# literally -- "requirements complete / total" gives a partial nothing. An
# engagement that wants partial credit passes PARTIAL_CREDIT instead; the
# formula string changes with it, so the popover never lies about which was used.
STRICT_CREDIT: Mapping[TransferState, float] = {
    TransferState.COMPLETE: 1.0,
    TransferState.PARTIAL: 0.0,
    TransferState.NONE: 0.0,
}

PARTIAL_CREDIT: Mapping[TransferState, float] = {
    TransferState.COMPLETE: 1.0,
    TransferState.PARTIAL: 0.5,
    TransferState.NONE: 0.0,
}


def describe_credit(credit: Mapping[TransferState, float]) -> str:
    """Render a credit map for a formula string, in vocabulary order."""
    return ", ".join(f"{state.value}={credit.get(state, 0.0):g}" for state in TransferState)
