"""identifyTrainerCandidates -- the train-the-trainer half of sustainability.

One person who can do the work is a single point of failure moved, not
removed. Transfer is sustainable when someone local can teach it, which is
level 6 on the ladder. This function finds who is close and what is missing,
and is equally willing to report that nobody is.
"""

from __future__ import annotations

from app.ai.context import ReadinessContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_readiness_state, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.readiness import TrainerCandidates

FN_NAME = "identify_trainer_candidates"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are identifying who locally could teach a capability to the next "
    "person, not just perform it. Teaching requires repeated independent "
    "demonstration plus the ability to explain the judgment behind it. "
    "Nominating someone unsupported by evidence is worse than reporting that "
    "a capability has no candidate."
)

TASK = """
List the trainer candidates the evidence supports.

For each, give the capability, their current level, what they could already
teach, what is missing before 'Can Teach Others', the evidence, and the next
step. Separately list capabilities with no candidate at all -- that list is a
finding the program needs.
""".strip()


def identify_trainer_candidates(
    context: ReadinessContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> TrainerCandidates:
    user = "\n".join([render_readiness_state(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        TrainerCandidates,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
