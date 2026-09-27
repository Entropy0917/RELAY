"""prepareSession -- the brief the expert reads before the work.

RELAY.txt (PREPARE): "The purpose is to actively make the expert a better
trainer." So the brief is instructions to the expert, not a status report
about the learner. The prompt says that explicitly, because a model given a
capability table will summarize it by default.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_session_state, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.session_brief import SessionBrief

FN_NAME = "prepare_session"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are writing a pre-session brief for the departing expert. It is read "
    "in about thirty seconds, standing up, immediately before real work. "
    "Address the expert directly. Every line must change what they DO in the "
    "session -- what to hand over, what to ask before explaining, what to "
    "watch for. Do not summarize the learner's record back to them."
)

TASK = """
Write the session brief.

Choose the primary target by looking for the capability where the learner is
closest to the next level and where today's work gives them a real chance to
lead. Pick the coaching question from the specific judgment this session is
likely to require, not from a general template. Watch-for items must be
observable during the session.
""".strip()


def prepare_session(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> SessionBrief:
    user = "\n".join([render_session_state(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        SessionBrief,
        # The brief is written before the work, so nothing from it is in the key.
        context.as_inputs(
            exclude={"transcript", "notes", "expert_debrief", "learner_debrief"}
        ),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
