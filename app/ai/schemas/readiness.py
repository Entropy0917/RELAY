"""analyzeReadiness and identifyTrainerCandidates.

Note what is NOT here: a readiness score. Scores are computed by B4 from
capability data, with the formula surfaced in a popover -- the spec forbids an
unexplained number, and a model-generated percentage is unexplainable by
construction. This function interprets the state that B4 measures: what is
brittle, what depends on one person, what must happen before departure.

identifyTrainerCandidates is the train-the-trainer half: transfer is only
sustainable if someone local can teach it, which is level 6 on the ladder.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import Status


class ReadinessRisk(BaseModel):
    severity: Status
    title: str
    problem: str = Field(description="What is fragile, stated concretely.")
    evidence: str
    recommended_action: str
    local_owner: str = Field(
        default="", description="Who locally could hold this. Empty if nobody can yet."
    )


class ReadinessAnalysis(BaseModel):
    summary: str = Field(
        description="Two sentences a program manager could read aloud: what is "
        "ready, what is not."
    )
    expert_dependent: list[str] = Field(
        description="Capabilities or decisions still resting on the departing expert."
    )
    sustainable: list[str] = Field(
        description="What would survive the departure unchanged, with evidence."
    )
    risks: list[ReadinessRisk] = Field(min_length=1)
    before_departure: list[str] = Field(
        min_length=1,
        description="Ordered actions that must happen before the expert leaves.",
    )


class TrainerCandidate(BaseModel):
    person: str
    capability: str
    current_level: int = Field(ge=0, le=6)
    readiness_to_teach: str = Field(
        description="What they can already teach, and what is missing before "
        "they reach 'Can Teach Others'."
    )
    evidence: list[str] = Field(min_length=1)
    next_step: str


class TrainerCandidates(BaseModel):
    candidates: list[TrainerCandidate] = Field(
        description="People whose evidence supports teaching others. May be "
        "empty -- an engagement with no trainer candidate is a finding, not a "
        "reason to nominate someone."
    )
    capabilities_with_no_candidate: list[str] = Field(default_factory=list)
