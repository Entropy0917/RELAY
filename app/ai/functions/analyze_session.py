"""analyzeSession -- AI SYNTHESIS. The centrepiece of the demo.

RELAY.txt (AI SYNTHESIS) combines the session, both debriefs, the operating
model, the blueprint, formal documentation and prior capability evidence, then
produces findings a human validates. The four findings this returns are the
four that change the system when approved: capability evidence, tacit
knowledge, the remaining gap, and the next activity.

This is the shape the SYNC-1 spike proved at 5/5 on `gemma4:31b-cloud` with
the schema in the prompt (planv0.2.md section 7). Nothing here writes
anything: approval is a human act, and only an approved validation moves a
capability level.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_session_record, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.synthesis import SessionSynthesis

FN_NAME = "analyze_session"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are synthesizing one transfer session into exactly four findings for "
    "a human to approve, edit or reject. Cite only what the material "
    "supports. A suggested level must be justified by something the learner "
    "did or said, not by attendance. If the session does not justify a level "
    "change, suggest the current level and say why in the evidence."
)

TASK = """
Produce exactly four findings.

capability_evidence  What the learner demonstrated about ONE capability, with
                     the current level, a suggested level for validation, a
                     confidence, and the sources each claim rests on.
tacit_knowledge      The expert reasoning this session exposed that is not in
                     the formal rules -- the signals, the judgment, and what
                     goes wrong once nobody knows it.
remaining_gap        What the learner now understands, set against what they
                     have still not done independently.
next_activity        The real work they should lead next, and what the expert
                     does instead of leading.

Distinguish understanding from demonstration throughout. Reasoning the learner
produced unprompted is stronger evidence than agreement with the expert.
""".strip()


def analyze_session(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> SessionSynthesis:
    user = "\n".join([render_session_record(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        SessionSynthesis,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
