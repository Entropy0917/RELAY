"""How a number explains itself.

planv0.2.md section 4 B4 and RELAY.txt ("READINESS CALCULATION") both forbid an
opaque score: every figure the product shows must be reconstructable by the
person looking at it, without reading this source. So nothing in this package
returns a bare float. Every public function returns a `Metric` or a `Verdict`,
each carrying three things:

    value    the number (or the category)
    inputs   the actual values that produced it, as readable strings
    formula  the arithmetic, as a human-readable string

`contracts.viewmodels.MetricTile` is the consumer, which is why `as_tile()`
maps one-to-one onto its fields. This module deliberately does not import
viewmodels -- the mapping belongs to the service layer, not to scoring.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# Recorded in `inputs` when a ratio has nothing to divide by. section 4 B4
# gives no renormalization rule, so an empty denominator scores 0.0 and says
# so out loud rather than silently inventing a 100%.
EMPTY_DENOMINATOR_NOTE = "denominator is zero -- nothing defined yet, scored as 0"


@runtime_checkable
class Explained(Protocol):
    """Anything this package hands back. Tests assert the whole surface is this."""

    value: object
    inputs: Mapping[str, str]
    formula: str


@dataclass(frozen=True)
class Metric:
    """A number with its arithmetic attached.

    `value` is the machine-readable figure (a ratio is 0.0-1.0, a count is a
    whole number). `display` is what the tile shows: "68%", "4", "28 days".
    """

    key: str
    label: str
    value: float
    display: str
    formula: str
    inputs: Mapping[str, str] = field(default_factory=dict)
    caption: str | None = None

    def as_tile(self) -> dict[str, object]:
        """Keyword arguments for contracts.viewmodels.MetricTile."""
        return {
            "label": self.label,
            "value": self.display,
            "caption": self.caption,
            "formula": self.formula,
            "inputs": dict(self.inputs),
        }


@dataclass(frozen=True)
class Verdict[V]:
    """A category with its arithmetic attached -- a status, a band, a severity.

    Categories get the same treatment as numbers because "AT RISK" is exactly
    the kind of judgement a reader is entitled to interrogate.
    """

    key: str
    value: V
    label: str
    formula: str
    inputs: Mapping[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Formatting -- one place, so every number in the product rounds identically
# ---------------------------------------------------------------------------


def num(value: float) -> str:
    """Compact, stable rendering: 7 -> '7', 7.5 -> '7.5', 0.6825 -> '0.6825'."""
    return f"{value:g}"


def percent(ratio: float) -> str:
    """Round-half-up to a whole percent. Python's round() is round-half-even,
    which would make 0.685 render as 68% here and 69% in a spreadsheet."""
    return f"{int(ratio * 100 + 0.5)}%"


def ids(values: Iterable[object]) -> str:
    """Render a collection of ids for `inputs`, sorted so output is stable."""
    items = sorted(str(v) for v in values)
    return ", ".join(items) if items else "(none)"


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------


def ratio_metric(
    key: str,
    label: str,
    *,
    numerator: float,
    denominator: float,
    formula: str,
    inputs: Mapping[str, str] | None = None,
    caption: str | None = None,
) -> Metric:
    """A proportion. Always records both sides so the division is checkable."""
    value = numerator / denominator if denominator else 0.0
    recorded: dict[str, str] = {
        "numerator": num(numerator),
        "denominator": num(denominator),
    }
    if not denominator:
        recorded["note"] = EMPTY_DENOMINATOR_NOTE
    recorded.update(inputs or {})
    return Metric(
        key=key,
        label=label,
        value=value,
        display=percent(value),
        formula=formula,
        inputs=recorded,
        caption=caption if caption is not None else f"{num(numerator)} of {num(denominator)}",
    )


def count_metric(
    key: str,
    label: str,
    *,
    total: int,
    formula: str,
    inputs: Mapping[str, str] | None = None,
    caption: str | None = None,
) -> Metric:
    """A headline count, such as locally teachable capabilities."""
    return Metric(
        key=key,
        label=label,
        value=float(total),
        display=str(total),
        formula=formula,
        inputs=dict(inputs or {}),
        caption=caption,
    )


def score_metric(
    key: str,
    label: str,
    *,
    value: float,
    formula: str,
    inputs: Mapping[str, str] | None = None,
    caption: str | None = None,
) -> Metric:
    """A composite 0.0-1.0 score that is not a plain numerator/denominator."""
    return Metric(
        key=key,
        label=label,
        value=value,
        display=percent(value),
        formula=formula,
        inputs=dict(inputs or {}),
        caption=caption,
    )


def days_metric(
    key: str,
    label: str,
    *,
    days: int,
    formula: str,
    inputs: Mapping[str, str] | None = None,
    caption: str | None = None,
) -> Metric:
    """A countdown. Negative means the date has passed -- shown, never hidden."""
    return Metric(
        key=key,
        label=label,
        value=float(days),
        display=f"{days} days",
        formula=formula,
        inputs=dict(inputs or {}),
        caption=caption,
    )
