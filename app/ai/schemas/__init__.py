"""One Pydantic model per AI function -- the contract the model must meet.

These are validation targets first and prompt material second: run.py serializes
the JSON Schema into the prompt for unconstrained providers (planv0.2.md
section 7), which is why field descriptions are written for a reader rather
than for a docstring. Keep them short and imperative; they are tokens.

Field names on SessionBrief deliberately match contracts.viewmodels.SessionBriefVM
so the session loop can hand one straight to the other without a mapping layer.
"""

from __future__ import annotations

from app.ai.schemas.capability import CapabilityAssessment, CapabilityFinding
from app.ai.schemas.debrief import DebriefQuestion, DebriefQuestions
from app.ai.schemas.departure import DepartureAction, DeparturePlan, DepartureRisk
from app.ai.schemas.knowledge import KnowledgeItem, TacitKnowledgeSet
from app.ai.schemas.next_activity import NextExperience
from app.ai.schemas.operating_model import (
    FormalInformalAnalysis,
    FormalInformalGap,
    OperatingModelArea,
    OperatingModelDraft,
    TransferRequirement,
    TransferRequirementSet,
)
from app.ai.schemas.plan import TransferPlan, TransferPlanStep
from app.ai.schemas.readiness import (
    ReadinessAnalysis,
    ReadinessRisk,
    TrainerCandidate,
    TrainerCandidates,
)
from app.ai.schemas.session_brief import SessionBrief
from app.ai.schemas.synthesis import (
    CapabilityEvidence,
    NextActivity,
    RemainingGap,
    SessionSynthesis,
    TacitKnowledge,
)

__all__ = [
    "CapabilityAssessment",
    "CapabilityEvidence",
    "CapabilityFinding",
    "DebriefQuestion",
    "DebriefQuestions",
    "DepartureAction",
    "DeparturePlan",
    "DepartureRisk",
    "FormalInformalAnalysis",
    "FormalInformalGap",
    "KnowledgeItem",
    "NextActivity",
    "NextExperience",
    "OperatingModelArea",
    "OperatingModelDraft",
    "ReadinessAnalysis",
    "ReadinessRisk",
    "RemainingGap",
    "SessionBrief",
    "SessionSynthesis",
    "TacitKnowledge",
    "TacitKnowledgeSet",
    "TrainerCandidate",
    "TrainerCandidates",
    "TransferPlan",
    "TransferPlanStep",
    "TransferRequirement",
    "TransferRequirementSet",
]
