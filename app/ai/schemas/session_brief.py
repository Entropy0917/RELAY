"""PREPARE output: the 30-second brief an expert reads before the work.

Its purpose (RELAY.txt, PREPARE) is to make the expert a better trainer, not
to summarize the file. Hence `ask_before_explaining`: the single coaching move
that converts a demonstration into a transfer.

Field names match contracts.viewmodels.SessionBriefVM exactly. Keep them that
way -- the session loop passes this straight through.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionBrief(BaseModel):
    primary_target: str = Field(
        description="The one capability the learner should lead today."
    )
    current_level: str = Field(
        description="The learner's current level on that capability, as the "
        "RELAY ladder label."
    )
    todays_objective: str = Field(
        description="One sentence: what must be true at the end of the session."
    )
    your_role: str = Field(
        description="What the expert should do while the learner leads, in one "
        "sentence, addressed to the expert as 'you'."
    )
    ask_before_explaining: str = Field(
        description="A specific question the expert should ask the learner "
        "before giving any recommendation."
    )
    watch_for: list[str] = Field(
        min_length=1,
        max_length=4,
        description="Observable signals that would be evidence of real "
        "understanding, or of its absence.",
    )
    knowledge_gap_to_explore: str = Field(
        description="A capability or piece of tacit reasoning to expose the "
        "learner to if the session allows it."
    )
