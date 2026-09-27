"""What an AI function is told about an engagement -- as parameters.

planv0.2.md section 0.5: prompts take engagement context as arguments and
never contain a hardcoded domain example. These models are the shape of that
argument. They carry no content themselves; B6 fills them from the database.

They also double as the cache key. `as_inputs()` is what gets hashed, so two
sessions with identical context share a cached answer and a changed transcript
misses -- which is the behaviour a demo rehearsal wants.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from contracts.vocabulary import CAPABILITY_LEVELS, Role


class Person(BaseModel):
    name: str
    title: str = ""
    role: Role = Role.COUNTERPART


class CapabilityState(BaseModel):
    """Where a person stands on one capability, plus why we believe it.

    `level_label` is derived rather than passed: the 0-6 ladder is product
    vocabulary, so the AI layer should not depend on a caller spelling it the
    same way twice.
    """

    capability: str
    level: int = Field(ge=0, le=6)
    person: str = ""
    evidence: list[str] = Field(default_factory=list)
    last_demonstrated: str | None = None

    @property
    def level_label(self) -> str:
        return CAPABILITY_LEVELS[self.level]


class QA(BaseModel):
    question: str
    answer: str | None = None


class EngagementContext(BaseModel):
    """The tenant. Every field here is database content, never a literal."""

    name: str
    sector: str
    organization: str = ""
    mission: str = ""
    days_until_departure: int | None = None


class SessionContext(BaseModel):
    """One transfer session, at whatever stage the caller has reached.

    Later stages simply fill in more fields: PREPARE has no transcript,
    SYNTHESIS has a transcript and both debriefs. The functions read only what
    they need, so one object serves the whole loop.
    """

    engagement: EngagementContext
    area: str = ""  # operating-model area this session sits in
    objective: str = ""
    expert: Person
    learners: list[Person] = Field(default_factory=list)
    capabilities: list[CapabilityState] = Field(default_factory=list)
    formal_rules: list[str] = Field(default_factory=list)
    open_gaps: list[str] = Field(default_factory=list)
    prior_sessions: list[str] = Field(default_factory=list)
    transcript: str | None = None
    notes: str | None = None
    expert_debrief: list[QA] = Field(default_factory=list)
    learner_debrief: list[QA] = Field(default_factory=list)

    def as_inputs(
        self, exclude: set[str] | None = None, **extra: Any
    ) -> dict[str, Any]:
        """Canonical cache input.

        `exclude` drops fields a given function never puts in its prompt. Without
        it, filling in a debrief later would cold-miss the cache for a function
        whose prompt did not change -- and a cold miss on stage is the thing the
        cache exists to prevent.
        """
        return {
            **self.model_dump(mode="json", exclude_none=True, exclude=exclude),
            **extra,
        }


class CorpusContext(BaseModel):
    """Source material, for the functions that build structure out of text.

    The operating-model builder and the requirement/gap analyses read
    documents and interview answers rather than a session. `existing_areas`
    lets a second pass extend a model instead of replacing it.
    """

    engagement: EngagementContext
    area: str = ""
    documents: list[str] = Field(
        default_factory=list, description="Title plus excerpt, one per entry."
    )
    interviews: list[QA] = Field(default_factory=list)
    existing_areas: list[str] = Field(default_factory=list)
    known_practice: list[str] = Field(
        default_factory=list, description="How the work is actually done, if known."
    )

    def as_inputs(
        self, exclude: set[str] | None = None, **extra: Any
    ) -> dict[str, Any]:
        return {
            **self.model_dump(mode="json", exclude_none=True, exclude=exclude),
            **extra,
        }


class ReadinessContext(BaseModel):
    """Engagement-wide state, for the functions that reason above one session."""

    engagement: EngagementContext
    areas: list[str] = Field(default_factory=list)
    capabilities: list[CapabilityState] = Field(default_factory=list)
    experts: list[Person] = Field(default_factory=list)
    counterparts: list[Person] = Field(default_factory=list)
    open_requirements: list[str] = Field(default_factory=list)
    knowledge_items: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)

    def as_inputs(
        self, exclude: set[str] | None = None, **extra: Any
    ) -> dict[str, Any]:
        return {
            **self.model_dump(mode="json", exclude_none=True, exclude=exclude),
            **extra,
        }
