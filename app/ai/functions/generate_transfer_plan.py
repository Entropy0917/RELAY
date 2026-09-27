"""generateTransferPlan -- sequenced real work, bounded by the departure date.

The plan's honesty is the point. Time before departure is finite, and a plan
that quietly assumes otherwise costs the engagement the chance to prioritise.
`not_achievable_before_departure` is therefore a first-class output, not an
exception path.
"""

from __future__ import annotations

from app.ai.context import ReadinessContext
from app.ai.prompts import (
    ANALYST,
    MODEL_PRIMER,
    render_readiness_state,
    section,
)
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.plan import TransferPlan

FN_NAME = "generate_transfer_plan"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are sequencing the transfer of one area into real upcoming work. "
    "Every step is operational work the learner does, not a class. Respect "
    "the rails and the time remaining: if the remaining days cannot cover a "
    "capability, say so instead of compressing it."
)

TASK = """
Produce the transfer plan for the area in scope.

Order the steps so that each one is possible given the ones before it. Give
every step a learner, a rail, the expert's role, and a success signal an
observer could check. Place each step in a window relative to the departure
date. List anything the remaining time cannot realistically cover.
""".strip()


def generate_transfer_plan(
    context: ReadinessContext,
    *,
    area: str = "",
    client: Client | None = None,
    use_cache: bool = True,
) -> TransferPlan:
    scope = section("AREA IN SCOPE", area) if area else ""
    user = "\n".join(
        part for part in [render_readiness_state(context), scope, section("TASK", TASK)] if part
    )
    return run(
        FN_NAME,
        TransferPlan,
        context.as_inputs(area=area),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
