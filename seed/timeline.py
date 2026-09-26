"""Every date in the corpus, expressed as an offset from one anchor.

The demo has a hard number in it: the departing expert leaves in 28 days, and
that figure is on the executive dashboard in the first ten seconds
(RELAY.txt, "DEMO SUCCESS FLOW" step 1). A corpus with absolute dates baked in
is correct on exactly one day and quietly wrong on every other, which is the
sort of thing nobody notices until it is on a projector.

So nothing here is a literal date. The anchor is *today*, the assignment is
nine months long and ends 28 days from the anchor, and every session, every
piece of evidence and every capture date is an irregular number of days either
side of it. Re-run `scripts/reset.py` next month and the story still reads
correctly: dates shift together, intervals stay the same.

`RELAY_SEED_TODAY` pins the anchor for a test or a rehearsal that needs a
fixed calendar. It is resolved once, at import, so a single `load_all()` can
never straddle midnight and produce a corpus dated across two days.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

# The expert's remaining time. The whole demo narrative hangs off this.
DAYS_TO_DEPARTURE = 28

# Nine months, counted in days rather than months so arithmetic is exact.
# 277 rather than 274 so the start date is not suspiciously tidy.
ASSIGNMENT_DAYS = 277


def _resolve_anchor() -> date:
    pinned = os.environ.get("RELAY_SEED_TODAY")
    return date.fromisoformat(pinned) if pinned else date.today()


TODAY: date = _resolve_anchor()

DEPARTURE: date = TODAY + timedelta(days=DAYS_TO_DEPARTURE)
ASSIGNMENT_START: date = DEPARTURE - timedelta(days=ASSIGNMENT_DAYS)


def days_ago(n: int) -> date:
    """`n` days before the anchor. The corpus's usual unit of history."""
    return TODAY - timedelta(days=n)


def days_ahead(n: int) -> date:
    return TODAY + timedelta(days=n)


def timestamp(n: int) -> str:
    """An `created_at` string for something that happened `n` days ago.

    The hour is derived from the offset rather than fixed, so an audit trail
    rendered in order does not read as though every decision in nine months
    was taken at the same minute past nine.
    """
    hour = 8 + (n * 3) % 9
    minute = (n * 17) % 60
    return f"{days_ago(n).isoformat()}T{hour:02d}:{minute:02d}:00"
