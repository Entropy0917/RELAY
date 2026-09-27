"""AI SYNTHESIS -- the centrepiece, and the hardest schema in the product.

Four heterogeneous nested findings. This exact shape is the one the SYNC-1
spike measured at 5/5 valid on `gemma4:31b-cloud` with the schema in the
prompt (planv0.2.md section 7, scripts/spike_structured_output.py). It is
reused verbatim rather than redesigned: a different shape is an unmeasured
shape, and this is the output the demo turns on.

`kind` discriminators are kept because they map onto
contracts.vocabulary.FindingKind, which is what the validation UI renders and
what B6 writes to the findings table.

Nothing here decides anything. `suggested_level` is a proposal that a human
approves, edits or rejects; only an approved validation moves a level.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]


class CapabilityEvidence(BaseModel):
    """Evidence that a learner moved, or demonstrably did not."""

    kind: Literal["capability_evidence"]
    person: str = Field(description="The learner this evidence is about.")
    capability: str
    evidence: str = Field(
        description="What the person actually did or said, in one or two "
        "sentences, drawn from the material."
    )
    current_level: int = Field(ge=0, le=6)
    suggested_level: int = Field(
        ge=0,
        le=6,
        description="Proposed level for human validation. Equal to "
        "current_level when the session did not justify a move.",
    )
    confidence: Confidence
    evidence_sources: list[str] = Field(
        min_length=1,
        description="Where each claim comes from: transcript, expert debrief, "
        "learner debrief, prior evidence.",
    )


class TacitKnowledge(BaseModel):
    """The expert reasoning that is not written down anywhere."""

    kind: Literal["tacit_knowledge"]
    title: str
    operating_model_area: str
    capability: str
    situation: str = Field(description="The conditions under which this applies.")
    observed_signals: list[str] = Field(
        min_length=1, description="What the expert noticed that a novice would not."
    )
    expert_reasoning: str = Field(
        description="Why the expert judged it the way they did, in their logic."
    )
    recommended_response: str
    why_it_matters: str = Field(
        description="What goes wrong once the expert is gone and nobody knows this."
    )


class RemainingGap(BaseModel):
    """Understanding is not demonstration. This is the difference."""

    kind: Literal["remaining_gap"]
    capability: str
    understands: str = Field(description="What the learner has shown they grasp.")
    not_yet_demonstrated: list[str] = Field(
        min_length=1,
        description="What they have not yet done independently. Specific acts, "
        "not topics.",
    )


class NextActivity(BaseModel):
    """The next session, proposed by this one. Feeds the next Session Brief."""

    kind: Literal["next_activity"]
    objective: str
    recommended_experience: str = Field(
        description="A concrete piece of real work the learner should lead."
    )
    learner_responsibilities: list[str] = Field(min_length=1)
    expert_role: str = Field(
        description="What the expert does instead of leading -- observe, "
        "question, validate."
    )


class SessionSynthesis(BaseModel):
    capability_evidence: CapabilityEvidence
    tacit_knowledge: TacitKnowledge
    remaining_gap: RemainingGap
    next_activity: NextActivity
