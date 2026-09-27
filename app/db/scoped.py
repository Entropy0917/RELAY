"""The only data-access path (planv0.2.md section 8, risk 12).

Every content table carries `engagement_id`, but a FK column does nothing on
its own -- one forgotten `WHERE` and two engagements bleed into each other,
silently, and the readiness numbers on screen become nonsense that still looks
plausible. That is the worst kind of bug to have on stage.

So queries do not get written by hand. They go through `Scope`, which binds a
single engagement and injects the predicate itself. Services take a `Scope`;
they never take a bare `Connection`.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, Row, Select, Table, delete, insert, select, update

from app.db.schema import CONTENT_TABLES, engagements

_SCOPED = {t.name for t in CONTENT_TABLES}


class UnscopedQuery(RuntimeError):
    """Raised when someone tries to reach a content table without an engagement."""


class Scope:
    """A connection bound to one engagement."""

    def __init__(self, conn: Connection, engagement_id: str) -> None:
        self.conn = conn
        self.engagement_id = engagement_id

    # -- reads -------------------------------------------------------------

    def select(self, table: Table, *where: Any) -> Select:
        """A SELECT that is already filtered to this engagement."""
        stmt = select(table)
        if table.name in _SCOPED:
            stmt = stmt.where(table.c.engagement_id == self.engagement_id)
        elif table is not engagements:
            raise UnscopedQuery(
                f"'{table.name}' is not engagement-scoped and not the engagement "
                f"root. Every content table needs engagement_id (section 0.5)."
            )
        return stmt.where(*where) if where else stmt

    def rows(self, table: Table, *where: Any) -> list[Row]:
        return list(self.conn.execute(self.select(table, *where)))

    def one(self, table: Table, *where: Any) -> Row | None:
        return self.conn.execute(self.select(table, *where)).first()

    def by_id(self, table: Table, row_id: str) -> Row | None:
        return self.one(table, table.c.id == row_id)

    # -- writes ------------------------------------------------------------

    def insert(self, table: Table, **values: Any) -> None:
        if table.name in _SCOPED:
            values.setdefault("engagement_id", self.engagement_id)
            if values["engagement_id"] != self.engagement_id:
                raise UnscopedQuery(
                    f"refusing to insert into '{table.name}' for engagement "
                    f"'{values['engagement_id']}' from a scope bound to "
                    f"'{self.engagement_id}'"
                )
        self.conn.execute(insert(table).values(**values))

    def insert_many(self, table: Table, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            self.insert(table, **row)

    def update(self, table: Table, row_id: str, **values: Any) -> None:
        """Scoped UPDATE.

        Note this cannot be used to move `person_capabilities.level` -- the
        database trigger rejects that unless an approved validation authorises
        it. Use `app.db.writes.apply_validation`.
        """
        stmt = update(table).where(table.c.id == row_id)
        if table.name in _SCOPED:
            stmt = stmt.where(table.c.engagement_id == self.engagement_id)
        self.conn.execute(stmt.values(**values))

    def delete(self, table: Table, row_id: str) -> None:
        stmt = delete(table).where(table.c.id == row_id)
        if table.name in _SCOPED:
            stmt = stmt.where(table.c.engagement_id == self.engagement_id)
        self.conn.execute(stmt)


def list_engagements(conn: Connection) -> list[Row]:
    """The one legitimate unscoped read: the switcher needs all of them."""
    return list(conn.execute(select(engagements).order_by(engagements.c.name)))


def primary_engagement(conn: Connection) -> Row:
    row = conn.execute(
        select(engagements).where(engagements.c.is_primary.is_(True))
    ).first()
    if row is None:
        raise RuntimeError(
            "no primary engagement in the database -- run scripts/reset.py"
        )
    return row
