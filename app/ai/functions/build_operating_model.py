"""buildOperatingModel -- source material in, structured operating model out.

RELAY.txt (AI-GUIDED OPERATING MODEL BUILDER): the model is assembled from
documents and interviews, across all eight dimensions, and a human confirms
it. `open_questions` exists so the draft can be honest about what it guessed;
a builder that never admits uncertainty produces a confident wrong model.
"""

from __future__ import annotations

from app.ai.context import CorpusContext
from app.ai.prompts import ANALYST, OM_DIMENSION_LIST, render_corpus, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.operating_model import OperatingModelDraft

FN_NAME = "build_operating_model"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are drafting an operating model: what this organization actually "
    "does, who does it, how decisions get made, and what would break if one "
    "person left. Structure it across the eight RELAY dimensions. Draw every "
    "area from the material -- do not supply a generic template."
)

TASK = f"""
Draft the operating model.

Populate every area across these eight dimensions:
{OM_DIMENSION_LIST}

For each area, name the capabilities a person needs to run it, and state what
currently depends on the departing expert alone. List anything you inferred
rather than read in `open_questions`.
""".strip()


def build_operating_model(
    context: CorpusContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> OperatingModelDraft:
    user = "\n".join([render_corpus(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        OperatingModelDraft,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
