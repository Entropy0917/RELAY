"""Engine and connection handling.

`foreign_keys=ON` is not optional. SQLite ignores foreign keys unless you ask,
and half of the engagement-scoping guarantee in section 0.5 is FK integrity.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import Connection, Engine, create_engine, event

_engine: Engine | None = None


def db_path() -> str:
    return os.environ.get("RELAY_DB", "relay.db")


def get_engine(path: str | None = None) -> Engine:
    """Process-wide engine. Pass `path` in tests to get a throwaway one."""
    global _engine
    if path is not None:
        return _make_engine(path)
    if _engine is None:
        _engine = _make_engine(db_path())
    return _engine


def _make_engine(path: str) -> Engine:
    engine = create_engine(f"sqlite+pysqlite:///{path}", future=True)

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_conn, _record):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()

    return engine


@contextmanager
def connect(engine: Engine | None = None) -> Iterator[Connection]:
    """A transaction. Commits on success, rolls back on any exception."""
    eng = engine or get_engine()
    with eng.begin() as conn:
        yield conn


def reset_engine() -> None:
    """Drop the cached engine. Tests use this; the app never needs it."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
