"""generateDeparturePlan -- the last weeks, sequenced by consequence.

This is the function that answers the product's closing question as a plan
rather than a score: when the expert leaves, does the expertise stay? The
honest version is more useful than the complete-looking one, which is why
`still_expert_dependent_at_departure` must be earned rather than left empty.
"""

from __future__ import annotations

from app.ai.context import ReadinessContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_readiness_state, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.departure import DeparturePlan

FN_NAME = "generate_departure_plan"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are planning the expert's remaining weeks so that the most "
    "consequential knowledge transfers first. Sequence by what breaks "
    "without it, not by what is easiest to schedule. Be explicit about what "
    "will not transfer in the time available."
)

TASK = """
Produce the departure plan.

Work back from the days remaining. Assign each action a week, an owner and a
reason it belongs in that week. List the risks: what stops working, who could
absorb it, the mitigation, and how many working days the mitigation needs.
Then state plainly what will still be expert-dependent on the final day.
""".strip()


def generate_departure_plan(
    context: ReadinessContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> DeparturePlan:
    user = "\n".join([render_readiness_state(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        DeparturePlan,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
