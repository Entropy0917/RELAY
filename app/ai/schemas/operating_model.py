"""Operating-model construction and its transfer requirements.

Three functions share this module because they share a subject: what the work
actually consists of (buildOperatingModel), what would have to transfer for
someone else to run it (identifyTransferRequirements), and how much of it is
written down at all (identifyFormalInformalGaps).

The eight dimensions and the seven requirement kinds come from
contracts.vocabulary -- they are product structure, so the model fills them in
rather than inventing categories of its own.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.vocabulary import RequirementKind, Status, TransferState


class OperatingModelArea(BaseModel):
    """One area of the operating model, populated across all 8 dimensions."""

    name: str
    purpose: str = Field(description="What this area exists to achieve.")
    processes: list[str] = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    governance: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    decision_rights: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(
        min_length=1, description="Named capabilities a person needs to run this area."
    )
    expert_dependency: str = Field(
        description="What in this area currently only the departing expert can do."
    )


class OperatingModelDraft(BaseModel):
    mission: str
    areas: list[OperatingModelArea] = Field(min_length=1)
    open_questions: list[str] = Field(
        default_factory=list,
        description="What a human must confirm before this draft is trusted.",
    )


class TransferRequirement(BaseModel):
    kind: RequirementKind
    label: str
    description: str = Field(
        description="What specifically must transfer, stated so that its "
        "presence or absence is observable."
    )
    state: TransferState = Field(
        description="Current transfer state, judged only from the material given."
    )
    evidence: str = Field(description="Why that state, citing the material.")
    risk_if_untransferred: str


class TransferRequirementSet(BaseModel):
    area: str
    requirements: list[TransferRequirement] = Field(min_length=1)


class FormalInformalGap(BaseModel):
    topic: str
    formal_rule: str = Field(
        description="What the written documentation says, or '(undocumented)'."
    )
    actual_practice: str = Field(description="What experienced people actually do.")
    why_they_differ: str
    documented: bool = Field(
        description="True only if the actual practice is written down somewhere."
    )
    severity: Status = Field(
        description="How much risk the gap carries when the expert leaves."
    )


class FormalInformalAnalysis(BaseModel):
    """The spec's central claim: documentation captures the rule, not the judgment."""

    area: str
    formal_coverage_pct: int = Field(
        ge=0, le=100, description="Share of the work the documentation covers."
    )
    informal_coverage_pct: int = Field(
        ge=0,
        le=100,
        description="Share of the judgment and tacit practice captured anywhere.",
    )
    gaps: list[FormalInformalGap] = Field(min_length=1)
