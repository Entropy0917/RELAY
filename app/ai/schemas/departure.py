"""generateDeparturePlan output: the last weeks, sequenced by consequence.

This is the function that answers the product's closing question -- when the
expert leaves, does the expertise stay? -- as a plan rather than a score. What
remains expert-dependent on the final day is stated explicitly, because the
honest version of this plan is more useful than a complete-looking one.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import Status


class DepartureRisk(BaseModel):
    title: str
    severity: Status
    what_stops_working: str = Field(
        description="What degrades after the departure, concretely."
    )
    who_absorbs_it: str = Field(default="", description="Empty if nobody can.")
    mitigation: str
    days_needed: int = Field(
        ge=0, description="Working days the mitigation realistically takes."
    )


class DepartureAction(BaseModel):
    week: int = Field(ge=1, description="Weeks from now, 1 = this week.")
    action: str
    owner: str
    capability: str = Field(default="")
    why_now: str = Field(description="What makes this the right week for it.")


class DeparturePlan(BaseModel):
    days_remaining: int = Field(ge=0)
    summary: str
    actions: list[DepartureAction] = Field(min_length=1)
    risks: list[DepartureRisk] = Field(min_length=1)
    still_expert_dependent_at_departure: list[str] = Field(
        description="What will not transfer in the time available. State it "
        "plainly; an empty list must be earned by the evidence."
    )
