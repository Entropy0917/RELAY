"""generateExpertDebrief -- 1-3 questions that mine what the expert did not say.

RELAY.txt (EXPERT DEBRIEF): questions must depend on what happened, and
generic surveys are explicitly ruled out. The highest-yield questions are
about moments where the expert departed from the written rule, noticed
something the learner did not, or made a call the material does not explain.
That is where the tacit knowledge is.

The learner debrief is a separate function on purpose: it tests understanding
rather than extracting reasoning, and it is shown to a different persona.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, render_session_record, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.debrief import DebriefQuestions

FN_NAME = "expert_debrief"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are interviewing the departing expert immediately after a work "
    "session. Your goal is the reasoning they did not narrate. Ask about the "
    "specific judgment calls in THIS session. A question that could have been "
    "asked before the session happened is a failed question."
)

TASK = """
Write one to three debrief questions for the expert.

Prefer, in order:
1. A point where the expert departed from the formal rule -- ask what made
   this case different.
2. Something the expert noticed that the learner did not.
3. What an inexperienced person would most likely get wrong here.

Quote or reference the actual moment in `grounded_in`. If the material only
supports one good question, ask one.
""".strip()


def generate_expert_debrief(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> DebriefQuestions:
    user = "\n".join(
        [render_session_record(context, debriefs=False), section("TASK", TASK)]
    )
    return run(
        FN_NAME,
        DebriefQuestions,
        # The debriefs are not in this prompt, so they must not be in the key.
        context.as_inputs(exclude={"expert_debrief", "learner_debrief"}),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
