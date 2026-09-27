"""identifyFormalInformalGaps -- the product's central claim, as analysis.

RELAY.txt (FORMAL VS INFORMAL KNOWLEDGE): documentation captures the rule;
expertise is knowing when the rule does not apply. This function finds those
divergences, which is where the transfer risk actually sits -- a fully
documented area with undocumented judgment is more dangerous than an
obviously undocumented one, because it looks safe.
"""

from __future__ import annotations

from app.ai.context import CorpusContext
from app.ai.prompts import ANALYST, render_corpus, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.operating_model import FormalInformalAnalysis

FN_NAME = "identify_formal_informal_gaps"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are comparing what the documentation says with what experienced "
    "people actually do. The gap between them is tacit knowledge. Do not "
    "treat a divergence as an error: it is usually judgment that nobody "
    "wrote down. Percentages are estimates from the material -- keep them "
    "defensible and coarse."
)

TASK = """
Analyse the formal/informal gap for the area in scope.

For each topic where practice diverges from documentation, state the written
rule (or '(undocumented)'), what experienced people actually do, and why they
differ. Mark whether the actual practice is written down anywhere. Rate how
much risk the gap carries when the expert leaves.

Estimate two coverage figures: how much of the work the documentation covers,
and how much of the judgment is captured anywhere at all.
""".strip()


def identify_formal_informal_gaps(
    context: CorpusContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> FormalInformalAnalysis:
    user = "\n".join([render_corpus(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        FormalInformalAnalysis,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
