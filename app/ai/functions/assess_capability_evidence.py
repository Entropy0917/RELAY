"""assessCapabilityEvidence -- capability findings across everyone present.

Synthesis produces one capability finding as part of the session's four. This
function does the same judgment at breadth: every person-capability pair the
material actually supports.

`counter_evidence` is required-by-habit rather than by schema: a model asked
only for supporting evidence will always find some. Asking for the argument
against is what keeps a suggested level honest enough for an expert to trust
the approve button.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_session_record, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.capability import CapabilityAssessment

FN_NAME = "assess_capability_evidence"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are assessing what this material evidences about each person's "
    "capabilities. Suggested levels are proposals for a human to validate. "
    "Attendance is not evidence. Agreeing with the expert is weak evidence. "
    "Reasoning produced unprompted, or a correct judgment made before the "
    "expert spoke, is strong evidence."
)

TASK = """
Produce one finding per person-capability pair the material supports.

Give the current level, a suggested level, the evidence in the person's own
actions or words, the sources it rests on, and a confidence. State any
counter-evidence. If a capability was not genuinely exercised, leave it out
rather than reporting no change.
""".strip()


def assess_capability_evidence(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> CapabilityAssessment:
    user = "\n".join([render_session_record(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        CapabilityAssessment,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
