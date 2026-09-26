"""assessCapabilityEvidence output.

Synthesis produces one capability finding as part of a session. This function
is the same judgment applied on its own -- across several people, or against
a body of evidence that did not come from one session.

`suggested_level` is always a proposal. B1 invariant 1 means the AI layer
physically cannot write a level; this schema keeps the language honest so the
UI never reads as if it certified anyone.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CapabilityFinding(BaseModel):
    person: str
    capability: str
    current_level: int = Field(ge=0, le=6)
    suggested_level: int = Field(
        ge=0, le=6, description="Proposal for human validation, never a decision."
    )
    evidence: str = Field(description="What the person did, drawn from the material.")
    evidence_sources: list[str] = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]
    counter_evidence: str = Field(
        default="",
        description="Anything in the material that argues against the "
        "suggested level. Empty only if there genuinely is none.",
    )


class CapabilityAssessment(BaseModel):
    findings: list[CapabilityFinding] = Field(
        min_length=1,
        description="One entry per person-capability pair the material supports. "
        "Do not pad: silence is a valid result for a capability not exercised.",
    )
