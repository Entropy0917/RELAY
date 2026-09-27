"""generateTransferPlan output: sequenced experiences, not a curriculum.

The plan is a series of real work items placed on the transfer rails, each
with an owner and a window. Sequencing is the value -- a learner cannot lead
what they have never assisted with, and time before departure is finite.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import Rail


class TransferPlanStep(BaseModel):
    sequence: int = Field(ge=1, description="1-based order. Earlier steps unblock later ones.")
    capability: str
    rail: Rail
    learner: str
    experience: str = Field(
        description="The real work that carries the transfer, not a training exercise."
    )
    expert_role: str
    success_signal: str = Field(
        description="What would have to be observed for this step to count as done."
    )
    target_window: str = Field(
        description="When this should happen, expressed relative to the "
        "departure date given in the context."
    )
    depends_on: list[int] = Field(
        default_factory=list, description="Sequence numbers that must complete first."
    )


class TransferPlan(BaseModel):
    area: str
    steps: list[TransferPlanStep] = Field(min_length=1)
    not_achievable_before_departure: list[str] = Field(
        default_factory=list,
        description="Capabilities the remaining time cannot realistically cover. "
        "Say so rather than producing an unachievable plan.",
    )
