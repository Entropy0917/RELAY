"""The machinery the corpus modules share. No engagement content lives here.

Two jobs.

**Counting.** `scripts/reset.py` prints "seeded N row(s)", and the only honest
N is the number of rows actually written -- including the ones written
indirectly by `app.db.writes.apply_validation`, which inserts a validation, an
evidence row and moves a level without the caller touching a table. Rather
than maintaining a parallel tally that drifts, `SeedScope` counts at the one
place every insert passes through.

**Refusing to double-load.** `capability_evidence` carries an append-only
trigger (schema.py, invariant 2), so a second `load_all()` cannot tidy up
after the first: the cascade delete would abort. Rather than leave a
half-written corpus behind, the seed checks first and says what to run
instead. `scripts/reset.py` drops and recreates before calling in, so this
never fires in normal use -- it exists for the person who calls `load_all()`
by hand and would otherwise get a primary-key error three tables deep.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, Table, func, select

from app.db.schema import engagements
from app.db.scoped import Scope


class AlreadySeeded(RuntimeError):
    """The database already holds a corpus. Reset rather than layering."""


class SeedScope(Scope):
    """A `Scope` that remembers how many rows it wrote."""

    def __init__(self, conn: Connection, engagement_id: str) -> None:
        super().__init__(conn, engagement_id)
        self.written = 0

    def insert(self, table: Table, **values: Any) -> None:
        super().insert(table, **values)
        self.written += 1


def guard_empty(conn: Connection) -> None:
    """Raise unless the engagement root is empty."""
    existing = conn.execute(select(func.count()).select_from(engagements)).scalar_one()
    if existing:
        raise AlreadySeeded(
            f"{existing} engagement(s) already present. The seed corpus is not "
            f"additive -- capability_evidence is append-only, so it cannot be "
            f"replaced in place. Run `python scripts/reset.py` instead."
        )
