"""extractTacitKnowledge -- session material into typed library items.

Synthesis surfaces the single most important piece of tacit knowledge from a
session. This function sweeps for all of it, types each item into one of the
seven knowledge categories, and writes it so someone who was not present can
act on it. That last constraint is what separates a library item from a
meeting note.

`people_exposed` records presence only. Exposure is not understanding, and the
capability layer is where understanding gets evidenced.
"""

from __future__ import annotations

from app.ai.context import SessionContext
from app.ai.prompts import ANALYST, KNOWLEDGE_TYPES, render_session_record, section
from app.ai.provider import Client
from app.ai.run import run
from app.ai.schemas.knowledge import TacitKnowledgeSet

FN_NAME = "extract_tacit_knowledge"

SYSTEM = (
    f"{ANALYST}\n\n"
    "You are extracting knowledge worth keeping after the expert leaves. "
    "Capture reasoning, thresholds, exceptions and relationships -- not a "
    "summary of the meeting. Write each item so a reader who was not present "
    "could act on it. Extract only what the material contains."
)

TASK = f"""
Extract the knowledge items in this material. Type each one:
{KNOWLEDGE_TYPES}

State when each applies, the knowledge itself, and why it matters once nobody
present knows it. Record who the material shows was exposed to it. Two real
items are better than six padded ones.
""".strip()


def extract_tacit_knowledge(
    context: SessionContext,
    *,
    client: Client | None = None,
    use_cache: bool = True,
) -> TacitKnowledgeSet:
    user = "\n".join([render_session_record(context), section("TASK", TASK)])
    return run(
        FN_NAME,
        TacitKnowledgeSet,
        context.as_inputs(),
        system=SYSTEM,
        user=user,
        client=client,
        use_cache=use_cache,
    )
