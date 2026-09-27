"""analyzeReadiness -- interpretation, deliberately not a score.

B4 computes readiness from capability data and exposes the formula, because
the spec forbids an unexplained number. A model-generated percentage would be
unexplainable by construction, so this function is not allowed to produce one.
It reads the state B4 measured and says what is brittle, what would survive,
and what has to happen before the expert leaves.
"""

from __future__ import annotations

from app.ai.context import ReadinessContext
from app.ai.prompts import ANALYST, MODEL_PRIMER, render_readiness_state, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.readiness import ReadinessAnalysis

FN_NAME = "analyze_readiness"

SYSTEM = (
    f"{ANALYST}\n\n{MODEL_PRIMER}\n\n"
    "You are assessing whether this engagement's expertise will survive the "
    "expert's departure. Do not produce a readiness score or a percentage -- "
    "those are computed elsewhere from the capability data and shown with "
    "their formula. Your job is what the numbers do not say: where the "
    "transfer is brittle, and what is still resting on one person."
)

TASK = """
Analyse readiness.

Name what remains expert-dependent and what would genuinely survive
unchanged, each with the evidence. List the risks with a severity, the
problem, the evidence, a recommended action, and a local owner where one
exists. Finish with the ordered actions that must happen before departure.
""".strip()


def analyze_readiness(
    context: ReadinessContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> ReadinessAnalysis:
    user = "\n".join([render_readiness_state(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        ReadinessAnalysis,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
