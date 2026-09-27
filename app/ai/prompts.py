"""Shared prompt construction. Context in, text out -- no content in here.

Two rules this file exists to keep:

  1. Section 0.5. Nothing below names a person, an organization, a sector or a
     domain example. Every concrete noun arrives through app.ai.context. A
     few-shot example would have to be sector-neutral, so there are none:
     RELAY's own vocabulary (rails, levels, knowledge types) does the work an
     example would otherwise do.
  2. The AI-safety line the spec draws. The system preamble states in every
     call that suggested levels are recommendations for human validation. The
     database enforces it too (B1 invariant 1), but a model that is told it
     decides will write as if it decides, and that tone leaks into the UI.
"""

from __future__ import annotations

from app.ai.context import (
    CapabilityState,
    CorpusContext,
    QA,
    ReadinessContext,
    SessionContext,
)
from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    KNOWLEDGE_LABEL,
    OM_DIMENSIONS,
    RAIL_LABEL,
    RAIL_ORDER,
    REQUIREMENT_LABEL,
)

ANALYST = (
    "You are a knowledge-transfer analyst for RELAY, a system that tracks "
    "whether expertise actually transfers from a departing expert to local "
    "staff before the expert leaves.\n"
    "Ground every statement in the material you are given. Never invent "
    "evidence, names, numbers or events. If the material does not support a "
    "conclusion, say what is missing instead of filling the gap.\n"
    "Capability levels you suggest are recommendations for a human to "
    "validate, never decisions. Exposure is not understanding: treat "
    "'the learner was present' as weaker evidence than 'the learner "
    "reasoned it out unprompted'."
)

CAPABILITY_LADDER = "\n".join(
    f"  {i} {label}" for i, label in enumerate(CAPABILITY_LEVELS)
)

TRANSFER_RAILS = " -> ".join(RAIL_LABEL[rail] for rail in RAIL_ORDER)

MODEL_PRIMER = (
    f"RELAY capability ladder (the index IS the level):\n{CAPABILITY_LADDER}\n\n"
    f"RELAY transfer rails, in order: {TRANSFER_RAILS}\n"
    "A person advances along the rails by doing, not by being told."
)


OM_DIMENSION_LIST = "\n".join(f"  {key}: {label}" for key, label in OM_DIMENSIONS)

REQUIREMENT_KINDS = "\n".join(
    f"  {kind.value}: {label}" for kind, label in REQUIREMENT_LABEL.items()
)

KNOWLEDGE_TYPES = "\n".join(
    f"  {kind.value}: {label}" for kind, label in KNOWLEDGE_LABEL.items()
)


def section(title: str, body: str) -> str:
    return f"{title}\n{'-' * len(title)}\n{body.strip()}\n"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "(none recorded)"


def render_capabilities(capabilities: list[CapabilityState]) -> str:
    if not capabilities:
        return "(none recorded)"
    lines = []
    for cap in capabilities:
        who = f"{cap.person}: " if cap.person else ""
        line = f"- {who}{cap.capability} -- level {cap.level} ({cap.level_label})"
        if cap.last_demonstrated:
            line += f", last demonstrated {cap.last_demonstrated}"
        lines.append(line)
        lines.extend(f"    evidence: {item}" for item in cap.evidence)
    return "\n".join(lines)


def render_debrief(pairs: list[QA]) -> str:
    if not pairs:
        return "(not yet collected)"
    return "\n".join(
        f"Q: {qa.question}\nA: {qa.answer or '(unanswered)'}" for qa in pairs
    )


def render_people(context: SessionContext) -> str:
    learners = (
        ", ".join(f"{p.name} ({p.title})" if p.title else p.name for p in context.learners)
        or "(none recorded)"
    )
    expert = context.expert
    expert_line = f"{expert.name} ({expert.title})" if expert.title else expert.name
    return f"Departing expert: {expert_line}\nLearners: {learners}"


def render_engagement(
    context: SessionContext | ReadinessContext | CorpusContext,
) -> str:
    eng = context.engagement
    lines = [f"Engagement: {eng.name}", f"Sector: {eng.sector}"]
    if eng.organization:
        lines.append(f"Organization: {eng.organization}")
    if eng.mission:
        lines.append(f"Mission: {eng.mission}")
    if eng.days_until_departure is not None:
        lines.append(f"Days until the expert departs: {eng.days_until_departure}")
    return "\n".join(lines)


def render_session_state(context: SessionContext) -> str:
    """Everything known before the session happens. Used by PREPARE."""
    parts = [
        section("ENGAGEMENT", render_engagement(context)),
        section("PEOPLE", render_people(context)),
    ]
    if context.area:
        parts.append(section("OPERATING MODEL AREA", context.area))
    if context.objective:
        parts.append(section("PLANNED OBJECTIVE", context.objective))
    parts.append(section("CURRENT CAPABILITY STATE", render_capabilities(context.capabilities)))
    parts.append(section("FORMAL RULES AND DOCUMENTATION", bullets(context.formal_rules)))
    parts.append(section("KNOWN GAPS", bullets(context.open_gaps)))
    if context.prior_sessions:
        parts.append(section("PRIOR SESSIONS", bullets(context.prior_sessions)))
    return "\n".join(parts)


def render_session_record(context: SessionContext, *, debriefs: bool = True) -> str:
    """Everything known after the session happened. Used by CAPTURE onwards."""
    parts = [render_session_state(context)]
    parts.append(section("SESSION TRANSCRIPT", context.transcript or "(not provided)"))
    if context.notes:
        parts.append(section("SESSION NOTES", context.notes))
    if debriefs:
        parts.append(section("EXPERT DEBRIEF", render_debrief(context.expert_debrief)))
        parts.append(section("LEARNER DEBRIEF", render_debrief(context.learner_debrief)))
    return "\n".join(parts)


def render_corpus(context: CorpusContext) -> str:
    """Source material for the structure-building functions."""
    parts = [section("ENGAGEMENT", render_engagement(context))]
    if context.area:
        parts.append(section("AREA IN SCOPE", context.area))
    if context.existing_areas:
        parts.append(
            section("OPERATING MODEL AREAS ALREADY DEFINED", bullets(context.existing_areas))
        )
    parts.append(section("DOCUMENTATION PROVIDED", bullets(context.documents)))
    parts.append(section("INTERVIEWS", render_debrief(context.interviews)))
    parts.append(section("OBSERVED PRACTICE", bullets(context.known_practice)))
    return "\n".join(parts)


def render_readiness_state(context: ReadinessContext) -> str:
    """Engagement-wide state for the functions that reason above one session."""
    experts = ", ".join(p.name for p in context.experts) or "(none recorded)"
    counterparts = ", ".join(p.name for p in context.counterparts) or "(none recorded)"
    parts = [
        section("ENGAGEMENT", render_engagement(context)),
        section("PEOPLE", f"Departing: {experts}\nLocal: {counterparts}"),
        section("OPERATING MODEL AREAS", bullets(context.areas)),
        section("CAPABILITY STATE", render_capabilities(context.capabilities)),
        section("OPEN TRANSFER REQUIREMENTS", bullets(context.open_requirements)),
        section("VALIDATED KNOWLEDGE ITEMS", bullets(context.knowledge_items)),
    ]
    if context.weights:
        parts.append(
            section(
                "READINESS WEIGHTS",
                bullets([f"{k}: {v}" for k, v in sorted(context.weights.items())]),
            )
        )
    return "\n".join(parts)
