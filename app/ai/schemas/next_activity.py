"""NEXT ACTION output: what the learner should lead next, and why.

Distinct from synthesis.NextActivity, which is one finding inside a session's
synthesis. This is the standalone recommendation -- it can be asked for
outside a session (from a capability passport, or when planning the week) and
it carries the justification fields the validation UI shows: rationale,
impact, risk. Those map onto contracts.viewmodels.FindingVM.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from contracts.vocabulary import Rail


class NextExperience(BaseModel):
    capability: str = Field(description="The capability this experience advances.")
    current_level: int = Field(ge=0, le=6)
    target_level: int = Field(
        ge=0, le=6, description="Where this single experience could realistically get them."
    )
    rail: Rail = Field(
        description="Which transfer rail this experience sits on. A person "
        "advances by doing, so prefer Assist/Lead over Know/Observe once they "
        "have been exposed."
    )
    objective: str = Field(description="One sentence, stated as an outcome.")
    recommended_experience: str = Field(
        description="A specific piece of real upcoming work, not a training exercise."
    )
    learner_responsibilities: list[str] = Field(min_length=1)
    expert_role: str
    rationale: str = Field(
        description="Why RELAY recommends this now, referencing the evidence."
    )
    risk_if_deferred: str = Field(
        description="What stays expert-dependent if this does not happen before departure."
    )
    urgency: Literal["low", "medium", "high"]
