"""identifyTransferRequirements -- what must transfer for one area to survive.

RELAY.txt (TRANSFER BLUEPRINT): for each area, the requirement categories are
fixed product vocabulary, so the model fills them in rather than inventing
its own. The value is in stating each requirement so that its presence or
absence is observable -- "understands procurement" is not a requirement,
"can raise an emergency order without the expert reviewing it" is.
"""

from __future__ import annotations

from app.ai.context import CorpusContext
from app.ai.prompts import ANALYST, REQUIREMENT_KINDS, render_corpus, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.operating_model import TransferRequirementSet

FN_NAME = "identify_transfer_requirements"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are deciding what would have to transfer for someone else to run "
    "this area without the departing expert. Judge the current state only "
    "from the material given -- an undocumented practice is not 'complete' "
    "because somebody mentioned it."
)

TASK = f"""
List the transfer requirements for the area in scope, covering these kinds:
{REQUIREMENT_KINDS}

Write each requirement so an observer could tell whether it has transferred.
Mark the state as complete, partial or none, and say what evidence supports
that state. Name what goes wrong if it never transfers.
""".strip()


def identify_transfer_requirements(
    context: CorpusContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> TransferRequirementSet:
    user = "\n".join([render_corpus(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        TransferRequirementSet,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
