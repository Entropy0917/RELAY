"""Lookups over a snapshot. Internal -- not part of the package's surface.

These are the only place that knows how to walk the input dataclasses, so the
metric modules read like the formulas in planv0.2.md section 4 B4 rather than
like loops. Everything returns in a deterministic order (id-sorted) because the
`inputs` strings on every metric include these lists, and a popover that
reorders itself between two identical runs is a defect.
"""

from __future__ import annotations

from collections.abc import Iterable

from contracts.vocabulary import LEVEL_INDEPENDENT, LEVEL_TEACHER, Role

from app.readiness.inputs import (
    Area,
    Capability,
    CapabilityLevel,
    EngagementSnapshot,
    Person,
    Requirement,
)


def local_people(snapshot: EngagementSnapshot) -> list[Person]:
    return sorted((p for p in snapshot.people if p.is_local), key=lambda p: p.id)


def experts(snapshot: EngagementSnapshot) -> list[Person]:
    return sorted((p for p in snapshot.people if p.role is Role.EXPERT), key=lambda p: p.id)


def critical_capabilities(snapshot: EngagementSnapshot) -> list[Capability]:
    return sorted((c for c in snapshot.capabilities if c.critical), key=lambda c: c.id)


def critical_areas(snapshot: EngagementSnapshot) -> list[Area]:
    return sorted((a for a in snapshot.areas if a.critical), key=lambda a: a.id)


def levels_for(snapshot: EngagementSnapshot, capability_id: str) -> list[CapabilityLevel]:
    return sorted(
        (lv for lv in snapshot.levels if lv.capability_id == capability_id),
        key=lambda lv: lv.person_id,
    )


def holders_at_or_above(
    snapshot: EngagementSnapshot, capability_id: str, threshold: int
) -> list[Person]:
    """Local people standing at `threshold` or higher on one capability."""
    out: list[Person] = []
    for level in levels_for(snapshot, capability_id):
        if level.level < threshold:
            continue
        person = snapshot.person(level.person_id)
        if person is None:
            continue  # a level row for an unknown person scores nothing
        if person.is_local:
            out.append(person)
    return sorted(out, key=lambda p: p.id)


def is_localized(snapshot: EngagementSnapshot, capability_id: str) -> bool:
    """At least one local person at LEVEL_INDEPENDENT or above (section 4 B4)."""
    return bool(holders_at_or_above(snapshot, capability_id, LEVEL_INDEPENDENT))


def is_teachable(snapshot: EngagementSnapshot, capability_id: str) -> bool:
    """At least one local person at LEVEL_TEACHER. The level is exact at 6 by
    construction -- LEVEL_TEACHER is the top of the scale."""
    return bool(holders_at_or_above(snapshot, capability_id, LEVEL_TEACHER))


def expert_holders(snapshot: EngagementSnapshot, capability_id: str) -> list[Person]:
    """Experts standing at LEVEL_INDEPENDENT or above on one capability."""
    out = [
        person
        for level in levels_for(snapshot, capability_id)
        if level.level >= LEVEL_INDEPENDENT
        and (person := snapshot.person(level.person_id)) is not None
        and person.role is Role.EXPERT
    ]
    return sorted(out, key=lambda p: p.id)


def expert_is_capable(snapshot: EngagementSnapshot, capability_id: str) -> bool:
    """Half of expert dependency: the expert can do it (section 4 B4)."""
    return bool(expert_holders(snapshot, capability_id))


def max_local_level(snapshot: EngagementSnapshot, capability_id: str) -> int:
    """Highest level any local person holds. -1 when nobody local is on record,
    which is distinguishable from level 0 ('Not Exposed', but known about)."""
    levels = [
        lv.level
        for lv in levels_for(snapshot, capability_id)
        if (p := snapshot.person(lv.person_id)) is not None and p.is_local
    ]
    return max(levels) if levels else -1


def has_validated_local_owner(snapshot: EngagementSnapshot, area: Area) -> bool:
    """An owner counts only when they exist, are local, and were validated."""
    if area.local_owner_id is None or not area.owner_validated:
        return False
    owner = snapshot.person(area.local_owner_id)
    return owner is not None and owner.is_local


def area_trainers(snapshot: EngagementSnapshot, area: Area) -> list[Person]:
    """Local people who can teach at least one of the area's capabilities."""
    found: dict[str, Person] = {}
    for capability_id in area.capability_ids:
        for person in holders_at_or_above(snapshot, capability_id, LEVEL_TEACHER):
            found[person.id] = person
    return sorted(found.values(), key=lambda p: p.id)


def area_capabilities(snapshot: EngagementSnapshot, area: Area) -> list[Capability]:
    out = [c for cid in area.capability_ids if (c := snapshot.capability(cid)) is not None]
    return sorted(out, key=lambda c: c.id)


def requirements_of_kinds(
    requirements: Iterable[Requirement], kinds: frozenset[object]
) -> list[Requirement]:
    return sorted((r for r in requirements if r.kind in kinds), key=lambda r: r.id)


def area_requirements(snapshot: EngagementSnapshot, area: Area) -> list[Requirement]:
    return sorted((r for r in snapshot.requirements if r.area_id == area.id), key=lambda r: r.id)
