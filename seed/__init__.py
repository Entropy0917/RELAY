"""The demo corpus. `load_all()` is the whole public surface.

    from seed import load_all
    count = load_all()

`scripts/reset.py` calls exactly this after dropping and recreating the
schema, so the signature is fixed by that file rather than chosen here.

Two engagements load, in this order and for this reason:

  * **`seed.primary`** -- a community-health supply chain handover, populated
    to full depth. Nine operating-model areas across all eight dimensions, ten
    capabilities with a dated evidence history, twenty knowledge items, five
    sessions of which four already happened, and the Clinic 14 transcript the
    demo is built around. Everything in the corpus that has to survive being
    read closely is here.
  * **`seed.secondary`** -- hydropower turbine reliability, deliberately thin.
    It exists so the engagement switcher demonstrates section 0.5's claim that
    nothing about the RELAY model is sector-specific, and so that every page
    renders when somebody switches to it. It is not a second demo.

The primary engagement loads first so that `primary_engagement()` has an
obvious answer even if `is_primary` were ever ambiguous, and so that a partial
load leaves the demo-critical half present rather than absent.

Everything runs inside one transaction. A corpus that is half-written is worse
than no corpus, because the failure shows up on a page rather than in a
traceback.
"""

from __future__ import annotations

from sqlalchemy import Engine

from app.db.connection import get_engine

from seed import primary, secondary
from seed.loader import AlreadySeeded, guard_empty

__all__ = ["AlreadySeeded", "load_all"]


def load_all(engine: Engine | None = None) -> int:
    """Insert both engagements. Returns the total number of rows written.

    Expects an empty schema -- `capability_evidence` is append-only by trigger,
    so the corpus cannot be replaced in place. Raises `AlreadySeeded` rather
    than layering a second copy on top of the first.
    """
    engine = engine or get_engine()
    with engine.begin() as conn:
        guard_empty(conn)
        return primary.load(conn) + secondary.load(conn)
