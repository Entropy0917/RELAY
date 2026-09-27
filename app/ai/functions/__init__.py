"""The fourteen AI functions from RELAY.txt (AI FUNCTIONS), one per module.

All of them go through app.ai.run.run, so all of them inherit the same
policy: cache -> live -> raise, Pydantic validation on our side, one bounded
retry, and no silent fallback.

REGISTRY exists so that tooling can enumerate the functions without importing
fourteen modules by hand -- tests round-trip every schema against its mock
fixture through it, and a rehearsal script can warm the cache the same way.
Its `spec_name` is the camelCase name the spec uses, kept so the mapping back
to RELAY.txt stays obvious.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel

from app.ai.functions.analyze_readiness import analyze_readiness
from app.ai.functions.analyze_session import analyze_session
from app.ai.functions.assess_capability_evidence import assess_capability_evidence
from app.ai.functions.build_operating_model import build_operating_model
from app.ai.functions.expert_debrief import generate_expert_debrief
from app.ai.functions.extract_tacit_knowledge import extract_tacit_knowledge
from app.ai.functions.generate_departure_plan import generate_departure_plan
from app.ai.functions.generate_transfer_plan import generate_transfer_plan
from app.ai.functions.identify_formal_informal_gaps import (
    identify_formal_informal_gaps,
)
from app.ai.functions.identify_trainer_candidates import identify_trainer_candidates
from app.ai.functions.identify_transfer_requirements import (
    identify_transfer_requirements,
)
from app.ai.functions.learner_debrief import generate_learner_debrief
from app.ai.functions.prepare_session import prepare_session
from app.ai.functions.recommend_next_experience import recommend_next_experience
from app.ai.schemas import (
    CapabilityAssessment,
    DebriefQuestions,
    DeparturePlan,
    FormalInformalAnalysis,
    NextExperience,
    OperatingModelDraft,
    ReadinessAnalysis,
    SessionBrief,
    SessionSynthesis,
    TacitKnowledgeSet,
    TrainerCandidates,
    TransferPlan,
    TransferRequirementSet,
)


@dataclass(frozen=True)
class AIFunction:
    name: str  # cache key and mock fixture filename
    spec_name: str  # the name RELAY.txt uses
    schema: type[BaseModel]
    call: Callable[..., Any]
    context: str  # which app.ai.context model it takes


REGISTRY: dict[str, AIFunction] = {
    fn.name: fn
    for fn in (
        AIFunction(
            "build_operating_model",
            "buildOperatingModel",
            OperatingModelDraft,
            build_operating_model,
            "CorpusContext",
        ),
        AIFunction(
            "identify_transfer_requirements",
            "identifyTransferRequirements",
            TransferRequirementSet,
            identify_transfer_requirements,
            "CorpusContext",
        ),
        AIFunction(
            "identify_formal_informal_gaps",
            "identifyFormalInformalGaps",
            FormalInformalAnalysis,
            identify_formal_informal_gaps,
            "CorpusContext",
        ),
        AIFunction(
            "generate_transfer_plan",
            "generateTransferPlan",
            TransferPlan,
            generate_transfer_plan,
            "ReadinessContext",
        ),
        AIFunction(
            "prepare_session",
            "prepareSession",
            SessionBrief,
            prepare_session,
            "SessionContext",
        ),
        AIFunction(
            "expert_debrief",
            "generateExpertDebrief",
            DebriefQuestions,
            generate_expert_debrief,
            "SessionContext",
        ),
        AIFunction(
            "learner_debrief",
            "generateLearnerDebrief",
            DebriefQuestions,
            generate_learner_debrief,
            "SessionContext",
        ),
        AIFunction(
            "analyze_session",
            "analyzeSession",
            SessionSynthesis,
            analyze_session,
            "SessionContext",
        ),
        AIFunction(
            "extract_tacit_knowledge",
            "extractTacitKnowledge",
            TacitKnowledgeSet,
            extract_tacit_knowledge,
            "SessionContext",
        ),
        AIFunction(
            "assess_capability_evidence",
            "assessCapabilityEvidence",
            CapabilityAssessment,
            assess_capability_evidence,
            "SessionContext",
        ),
        AIFunction(
            "recommend_next_experience",
            "recommendNextExperience",
            NextExperience,
            recommend_next_experience,
            "SessionContext",
        ),
        AIFunction(
            "identify_trainer_candidates",
            "identifyTrainerCandidates",
            TrainerCandidates,
            identify_trainer_candidates,
            "ReadinessContext",
        ),
        AIFunction(
            "analyze_readiness",
            "analyzeReadiness",
            ReadinessAnalysis,
            analyze_readiness,
            "ReadinessContext",
        ),
        AIFunction(
            "generate_departure_plan",
            "generateDeparturePlan",
            DeparturePlan,
            generate_departure_plan,
            "ReadinessContext",
        ),
    )
}

__all__ = [
    "AIFunction",
    "REGISTRY",
    "analyze_readiness",
    "analyze_session",
    "assess_capability_evidence",
    "build_operating_model",
    "extract_tacit_knowledge",
    "generate_departure_plan",
    "generate_expert_debrief",
    "generate_learner_debrief",
    "generate_transfer_plan",
    "identify_formal_informal_gaps",
    "identify_trainer_candidates",
    "identify_transfer_requirements",
    "prepare_session",
    "recommend_next_experience",
]
