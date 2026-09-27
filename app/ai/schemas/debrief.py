"""Debrief questions -- one shape, two audiences.

RELAY.txt is explicit: 1-3 TARGETED questions, dependent on what happened, and
never a generic survey. The bound is in the schema because it is the part a
model drifts on first; `grounded_in` is there to make an untargeted question
hard to write -- it has to point at something that actually occurred.

The expert debrief mines reasoning the expert did not narrate. The learner
debrief tests whether the reasoning landed. Same structure, different prompt.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DebriefQuestion(BaseModel):
    question: str = Field(
        description="The question, phrased as it will be shown to the person."
    )
    grounded_in: str = Field(
        description="The specific moment or decision in the material that "
        "makes this question worth asking."
    )
    looking_for: str = Field(
        description="What a good answer would reveal -- the tacit knowledge or "
        "the evidence of understanding being probed."
    )


class DebriefQuestions(BaseModel):
    questions: list[DebriefQuestion] = Field(
        min_length=1,
        max_length=3,
        description="One to three questions. Fewer, sharper questions are "
        "better than three weak ones.",
    )
