"""extractTacitKnowledge output -- library items, not prose.

Every item is typed with contracts.vocabulary.KnowledgeType so it lands in one
of the seven library categories. An item that cannot be typed is usually a
summary of the session rather than a transferable piece of knowledge, which is
exactly what we do not want stored.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import KnowledgeType


class KnowledgeItem(BaseModel):
    title: str = Field(description="Short and specific enough to find later.")
    type: KnowledgeType
    capability: str = Field(description="The capability this knowledge belongs to.")
    operating_model_area: str
    situation: str = Field(description="When this applies.")
    content: str = Field(
        description="The knowledge itself, written so someone who was not "
        "present could act on it."
    )
    why_it_matters: str
    source: str = Field(
        description="Where it came from: transcript, expert debrief, learner debrief."
    )
    people_exposed: list[str] = Field(
        default_factory=list,
        description="People the material shows were present for this. Exposure "
        "only -- not understanding.",
    )


class TacitKnowledgeSet(BaseModel):
    items: list[KnowledgeItem] = Field(
        min_length=1,
        max_length=8,
        description="Only knowledge the material actually contains. Two real "
        "items beat six padded ones.",
    )
