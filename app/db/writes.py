"""The only way a capability level ever moves.

This is the product's central safety claim: RELAY's AI proposes, a human
decides. `findings` is what the model produced; `validations` is what a person
did about it. Keeping those two separate is what lets the UI show
"AI SUGGESTION" and "VALIDATED BY" as different things and mean it.

The ordering below is not stylistic. The trigger in schema.py rejects a level
change that does not cite an approved validation, so the validation row must
exist before the level moves. Write it the other way round and the database
refuses -- which is the point.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Row

from app.db.schema import (
    capability_evidence,
    findings,
    person_capabilities,
    validations,
)
from app.db.scoped import Scope


class ValidationRefused(RuntimeError):
    """The requested validation is not something the data model permits."""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def apply_validation(
    scope: Scope,
    *,
    finding_id: str,
    validated_by_id: str,
    action: str,
    person_capability_id: str | None = None,
    new_level: int | None = None,
    evidence_summary: str | None = None,
    evidence_source: str | None = None,
    observed_on: date | None = None,
    edited_body: dict | None = None,
    note: str | None = None,
) -> str:
    """Record a human decision on an AI finding. Returns the validation id.

    On `approve` with a `new_level`, this also appends evidence and moves the
    level -- in that order, and only then.
    """
    finding = scope.by_id(findings, finding_id)
    if finding is None:
        raise ValidationRefused(f"no finding '{finding_id}' in this engagement")
    if finding.status != "pending":
        raise ValidationRefused(
            f"finding '{finding_id}' is already {finding.status}; "
            f"validations are not re-decided"
        )

    validation_id = _new_id("val")
    scope.insert(
        validations,
        id=validation_id,
        finding_id=finding_id,
        person_capability_id=person_capability_id,
        validated_by_id=validated_by_id,
        action=action,
        edited_body=edited_body,
        note=note,
        created_at=_now(),
    )
    scope.update(
        findings,
        finding_id,
        status=action if action != "approve" else "approved",
        body=edited_body if edited_body is not None else finding.body,
    )

    if action != "approve" or new_level is None:
        return validation_id

    if person_capability_id is None:
        raise ValidationRefused(
            "approving a level change requires person_capability_id"
        )

    pc = scope.by_id(person_capabilities, person_capability_id)
    if pc is None:
        raise ValidationRefused(
            f"no person_capability '{person_capability_id}' in this engagement"
        )
    if not 0 <= new_level <= 6:
        raise ValidationRefused(f"level {new_level} is outside 0..6")

    # Evidence first: history is the justification for the level, so it must
    # never be possible to have the level without it.
    scope.insert(
        capability_evidence,
        id=_new_id("ev"),
        person_capability_id=person_capability_id,
        session_id=finding.session_id,
        observed_on=observed_on or date.today(),
        level_at_time=new_level,
        summary=evidence_summary or finding.title,
        source=evidence_source or f"validation:{validation_id}",
        created_at=_now(),
    )

    # Now the level, citing the validation that authorised it. The trigger
    # verifies that citation.
    scope.update(
        person_capabilities,
        person_capability_id,
        level=new_level,
        last_validation_id=validation_id,
        exposure_count=pc.exposure_count + 1,
        last_demonstrated=observed_on or date.today(),
    )
    return validation_id


def append_evidence(
    scope: Scope,
    *,
    person_capability_id: str,
    summary: str,
    source: str,
    session_id: str | None = None,
    observed_on: date | None = None,
) -> str:
    """Record an exposure that does not change the level.

    Most evidence is like this. A level change is the exception, not the rule.
    """
    pc = scope.by_id(person_capabilities, person_capability_id)
    if pc is None:
        raise ValidationRefused(f"no person_capability '{person_capability_id}'")

    evidence_id = _new_id("ev")
    scope.insert(
        capability_evidence,
        id=evidence_id,
        person_capability_id=person_capability_id,
        session_id=session_id,
        observed_on=observed_on or date.today(),
        level_at_time=pc.level,
        summary=summary,
        source=source,
        created_at=_now(),
    )
    scope.update(
        person_capabilities,
        person_capability_id,
        exposure_count=pc.exposure_count + 1,
    )
    return evidence_id


def evidence_for(scope: Scope, person_capability_id: str) -> list[Row]:
    return scope.rows(
        capability_evidence,
        capability_evidence.c.person_capability_id == person_capability_id,
    )
