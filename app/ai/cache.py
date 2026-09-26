"""Validated AI responses, keyed by function and input.

Two jobs, both demo-critical:

  1. Determinism. The same inputs produce the same findings on every run, so a
     rehearsed demo does not drift between takes (planv0.2.md risk 8).
  2. Insurance. A pre-warmed cache means the flagship path never touches the
     network on stage (risk 2). That is the *only* sanctioned way a demo
     survives an unreachable provider -- there is no automatic fallback.

  ==========================================================================
  scripts/reset.py MUST PRESERVE THIS TABLE.
  ==========================================================================
  A reset drops and reseeds engagement data. If it drops `ai_cache` too, the
  operator loses a warm cache seconds before presenting and every step of the
  demo becomes a live model call. planv0.2.md section 4 B1 states this as a
  requirement; it is restated here because this is the file that would get
  read when someone wonders why the demo went cold.

KEY DESIGN. The key is `(fn_name, sha256(canonical_json(inputs)))` where
`inputs` are the *engagement inputs* to the function -- not the rendered
prompt, and not the model name. Deliberate: switching to the offline model
(RELAY_MODEL=<local model>, section 7) must still hit a cache warmed on the
cloud model, otherwise the offline path is useless at 46s per call. The model
and provider that produced a row are stored for forensics, not for lookup.

This module owns its own connection and creates the table if it is missing. It
does not import app.db: B1 lands in parallel and the AI layer must not be
blocked on it. Both point at RELAY_DB, so they share one file.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_DB = "relay.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_cache (
    fn_name    TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    payload    TEXT NOT NULL,
    model      TEXT,
    provider   TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fn_name, input_hash)
)
"""


def db_path() -> Path:
    """Read the env var on every call so tests and `flask run` can differ."""
    return Path(os.environ.get("RELAY_DB", DEFAULT_DB))


def connect() -> sqlite3.Connection:
    path = db_path()
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


@contextmanager
def _session() -> Iterator[sqlite3.Connection]:
    """Commit and close. sqlite3's own context manager does not close, and an
    open handle keeps the DB file locked on Windows -- which breaks reset."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def canonical_json(value: Any) -> str:
    """Stable text for hashing: sorted keys, no incidental whitespace.

    `default=str` means a date or an enum hashes as its string form rather
    than exploding -- callers pass view-model-ish data, not raw ORM objects.
    """
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def cache_key(inputs: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(inputs).encode("utf-8")).hexdigest()


def get(fn_name: str, key: str) -> str | None:
    with _session() as conn:
        row = conn.execute(
            "SELECT payload FROM ai_cache WHERE fn_name = ? AND input_hash = ?",
            (fn_name, key),
        ).fetchone()
    return row[0] if row else None


def put(
    fn_name: str,
    key: str,
    payload: str,
    *,
    model: str | None = None,
    provider: str | None = None,
) -> None:
    """Store a response that has ALREADY validated. Nothing else gets in here."""
    with _session() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ai_cache "
            "(fn_name, input_hash, payload, model, provider, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                fn_name,
                key,
                payload,
                model,
                provider,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )


def drop(fn_name: str, key: str) -> None:
    """Evict one row. Used when a cached payload no longer fits its schema."""
    with _session() as conn:
        conn.execute(
            "DELETE FROM ai_cache WHERE fn_name = ? AND input_hash = ?",
            (fn_name, key),
        )


def clear(fn_name: str | None = None) -> int:
    """Maintenance only -- a reset must never call this (see module docstring)."""
    with _session() as conn:
        cur = (
            conn.execute("DELETE FROM ai_cache WHERE fn_name = ?", (fn_name,))
            if fn_name
            else conn.execute("DELETE FROM ai_cache")
        )
        return cur.rowcount


def stats() -> dict[str, int]:
    """Rows per function. Lets a rehearsal confirm the cache is actually warm."""
    with _session() as conn:
        rows = conn.execute(
            "SELECT fn_name, COUNT(*) FROM ai_cache GROUP BY fn_name"
        ).fetchall()
    return {name: count for name, count in rows}
