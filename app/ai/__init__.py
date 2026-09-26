"""RELAY's AI layer (planv0.2.md section 4, B2).

One policy, applied everywhere: cache -> live -> RAISE.

    from app.ai import analyze_session, SessionContext, AIError

    try:
        synthesis = analyze_session(context)
    except AIError as exc:
        return render(exc.as_error_partial(retry_href=...)), 502

What callers get: typed, validated data or a typed error. Never a fixture
standing in for a live answer, never placeholder analysis, never a partially
parsed response. Switching provider or model is one env var
(RELAY_AI_PROVIDER, RELAY_MODEL) and changes no call site.
"""

from __future__ import annotations

from app.ai.context import (
    CapabilityState,
    CorpusContext,
    EngagementContext,
    Person,
    QA,
    ReadinessContext,
    SessionContext,
)
from app.ai.errors import AIError, ProviderUnreachable, SchemaViolation, Timeout
from app.ai.functions import (
    REGISTRY,
    AIFunction,
    analyze_readiness,
    analyze_session,
    assess_capability_evidence,
    build_operating_model,
    extract_tacit_knowledge,
    generate_departure_plan,
    generate_expert_debrief,
    generate_learner_debrief,
    generate_transfer_plan,
    identify_formal_informal_gaps,
    identify_trainer_candidates,
    identify_transfer_requirements,
    prepare_session,
    recommend_next_experience,
)
from app.ai.provider import Client, Request, get_client
from app.ai.run import run

__all__ = [
    "AIError",
    "AIFunction",
    "CapabilityState",
    "Client",
    "CorpusContext",
    "EngagementContext",
    "Person",
    "ProviderUnreachable",
    "QA",
    "REGISTRY",
    "ReadinessContext",
    "Request",
    "SchemaViolation",
    "SessionContext",
    "Timeout",
    "analyze_readiness",
    "analyze_session",
    "assess_capability_evidence",
    "build_operating_model",
    "extract_tacit_knowledge",
    "generate_departure_plan",
    "generate_expert_debrief",
    "generate_learner_debrief",
    "generate_transfer_plan",
    "get_client",
    "identify_formal_informal_gaps",
    "identify_trainer_candidates",
    "identify_transfer_requirements",
    "prepare_session",
    "recommend_next_experience",
    "run",
]
