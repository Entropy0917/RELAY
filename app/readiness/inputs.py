"""The input contract for readiness scoring -- deliberately not the database.

B1 (schema) and B4 (this package) are built in parallel, so nothing here
imports SQLAlchemy, sqlite3, Flask or app.db, and it never will. This module
describes what scoring *needs* as plain frozen dataclasses; the service layer
(B5) maps database rows onto them.

Two consequences worth keeping:

  * Scoring is pure. It cannot issue a query by accident, so it cannot be slow,
    order-dependent or engagement-leaking, and every test is a literal.
  * The schema can change shape without touching the formula, and the formula
    can change without a migration.

`as_of` is a field, not a clock read (planv0.2.md section 4 B4: "no I/O").
Days-until-departure has to be reproducible on demo day and in a test written
months earlier, so the caller supplies today's date explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    KnowledgeType,
    RequirementKind,
    Role,
    TransferState,
)

from app.readiness.weights import ReadinessWeights

MAX_LEVEL = len(CAPABILITY_LEVELS) - 1

# "Local" means the receiving organization: everyone who is not the departing
# expert. Managers count -- an area owned by a local manager is still locally
# owned. Exported so an engagement with a different role set can reason about it.
LOCAL_ROLES: frozenset[Role] = frozenset({Role.COUNTERPART, Role.MANAGER})


@dataclass(frozen=True)
class Person:
    """One participant. `name` is engagement data and only ever arrives here."""

    id: str
    name: str
    role: Role
    departure_date: date | None = None  # experts only; drives departure readiness

    @property
    def is_local(self) -> bool:
        return self.role in LOCAL_ROLES


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    critical: bool = True  # section 4 B4 scopes localization to critical caps


@dataclass(frozen=True)
class CapabilityLevel:
    """One person's standing on one capability -- a person_capabilities row.

    `level` indexes CAPABILITY_LEVELS; the index IS the level (vocabulary.py).
    """

    person_id: str
    capability_id: str
    level: int
    exposures: int = 0
    evidence_count: int = 0
    last_demonstrated: date | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.level <= MAX_LEVEL:
            raise ValueError(
                f"level {self.level} is outside 0..{MAX_LEVEL} "
                f"({self.person_id}/{self.capability_id})"
            )


@dataclass(frozen=True)
class Requirement:
    """One transfer requirement on one operating-model area.

    `validated` is separate from `state` on purpose: section 4 B4 counts formal
    requirements that are merely complete, but counts informal ones only where
    the capture was *validated*. Conflating the two would quietly inflate the
    informal half of the score, which is the half that is hard to earn.
    """

    id: str
    area_id: str
    kind: RequirementKind
    state: TransferState
    validated: bool = False
    capability_id: str | None = None


@dataclass(frozen=True)
class Area:
    """An operating-model area, with the capabilities running through it."""

    id: str
    name: str
    critical: bool = True
    local_owner_id: str | None = None
    owner_validated: bool = False
    capability_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeItem:
    """A library entry. Feeds risk (undocumented tacit) and departure counts."""

    id: str
    type: KnowledgeType
    validated: bool = False
    area_id: str | None = None
    capability_id: str | None = None
    exposed_person_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngagementSnapshot:
    """Everything scoring reads, for exactly one engagement, at one instant.

    Engagement-scoped by construction (planv0.2.md section 0.5): there is no
    way to hand this package two engagements at once, so no metric can mix them.
    """

    engagement_id: str
    as_of: date
    people: tuple[Person, ...] = ()
    capabilities: tuple[Capability, ...] = ()
    levels: tuple[CapabilityLevel, ...] = ()
    areas: tuple[Area, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    knowledge: tuple[KnowledgeItem, ...] = ()
    # Per-engagement weights read from the database. None = use DEFAULT_WEIGHTS.
    weights: ReadinessWeights | None = None

    def person(self, person_id: str) -> Person | None:
        return next((p for p in self.people if p.id == person_id), None)

    def capability(self, capability_id: str) -> Capability | None:
        return next((c for c in self.capabilities if c.id == capability_id), None)

    def area(self, area_id: str) -> Area | None:
        return next((a for a in self.areas if a.id == area_id), None)
