"""recommendNextExperience -- what the learner should lead next.

RELAY.txt (NEXT ACTION): every session feeds the next one, and the
recommendation becomes part of the next Session Brief. That closes the loop
PLAN -> WORK -> REFLECT -> CAPTURE -> VALIDATE -> PRACTICE -> REASSESS.

Separate from synthesis because it is also asked for outside a session -- from
a capability passport, or when a program manager plans the remaining weeks --
and because it carries the justification fields the validation UI renders:
rationale, risk, urgency.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import (
    ANALYST,
    MODEL_PRIMER,
    render_session_record,
    render_session_state,
    section,
)
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.next_activity import NextExperience

FN_NAME = "recommend_next_experience"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are recommending the next real piece of work the learner should "
    "lead. Capability moves by doing. Recommend upcoming operational work, "
    "never a training exercise, a workshop or a document to read. Respect the "
    "rails: someone who has only observed should assist before leading."
)

TASK = """
Recommend the single next experience.

Choose the capability where advancing has the largest effect on what survives
the expert's departure -- usually one the learner understands but has not
performed independently. State the objective as an outcome. Make the learner's
responsibilities concrete enough that an observer could tell whether they did
them. Say what the expert does instead of leading.
""".strip()


def recommend_next_experience(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> NextExperience:
    body = (
        render_session_record(context)
        if context.transcript or context.expert_debrief
        else render_session_state(context)
    )
    user = "\n".join([body, section("TASK", TASK)])
    return run(
        FN_NAME,
        NextExperience,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
