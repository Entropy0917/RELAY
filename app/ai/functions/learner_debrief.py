"""generateLearnerDebrief -- 1-3 questions that test whether it landed.

RELAY.txt (LEARNER DEBRIEF) states the principle this function exists to
serve: do NOT assume that exposure means understanding. The questions are
therefore not comprehension checks on what was said -- they ask the learner to
reconstruct the reasoning and to extend it to a case that did not occur.

The expert debrief, if it has been collected, is included: the sharpest
learner question is usually aimed at the reasoning the expert just revealed
but did not narrate during the work.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, render_session_record, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.debrief import DebriefQuestions

FN_NAME = "learner_debrief"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are interviewing the learner immediately after a work session. Your "
    "goal is evidence about whether they understood the expert's reasoning, "
    "not whether they can repeat what happened. Presence is not "
    "understanding. A question they could answer from memory alone tells you "
    "nothing."
)

TASK = """
Write one to three debrief questions for the learner.

Prefer, in order:
1. Ask them to explain WHY something mattered, where the written rule alone
   would have led them elsewhere.
2. Extend the case: ask what they would do if the option the expert chose
   were unavailable.
3. Probe a step they observed but have not performed themselves.

Use language the learner used, where the material shows it. Reference the
actual moment in `grounded_in`.
""".strip()


def generate_learner_debrief(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> DebriefQuestions:
    user = "\n".join([render_session_record(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        DebriefQuestions,
        # The learner's own answers do not exist yet and are not in the prompt.
        context.as_inputs(exclude={"learner_debrief"}),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
