"""Pre-warm the AI response cache for deterministic rehearsal and demo runs.

planv0.2.md section 9, step 1:
    "1. Rehearse the full 15-step path once — warms the AI response cache."

This script queries sessions that carry a transcript and runs session
synthesis via analyze_session.  Successful responses are saved in the
`ai_cache` SQLite table.  Because scripts/reset.py preserves `ai_cache`,
subsequent resets leave the warm responses intact so that the live demo
runs instantly (<10ms) without touching the network.

Usage:
    python scripts/warm_cache.py
    python scripts/warm_cache.py --session-id <id>
    python scripts/warm_cache.py --stats
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai import analyze_session
from app.ai.cache import stats
from app.db.adapters import session_context
from app.db.connection import connect, get_engine
from app.db.schema import sessions
from app.db.scoped import Scope, primary_engagement


def warm_cache(*, session_id: str | None = None, as_of: date | None = None) -> None:
    engine = get_engine()
    with connect(engine) as conn:
        eng = primary_engagement(conn)
        scope = Scope(conn, eng.id)

        all_sessions = scope.rows(sessions)
        target_sessions = []
        if session_id:
            target_sessions = [s for s in all_sessions if s.id == session_id]
            if not target_sessions:
                print(f"Error: no session with id '{session_id}' found in engagement '{eng.id}'.")
                sys.exit(1)
        else:
            # Warm all sessions that have transcripts
            target_sessions = [s for s in all_sessions if bool(s.transcript and s.transcript.strip())]

        if not target_sessions:
            print("No sessions with transcripts found to warm.")
            return

        print(f"Found {len(target_sessions)} session(s) with transcript to warm:")
        for s in target_sessions:
            print(f"  - {s.id} (stage: {s.stage})")

        ref_date = as_of or date.today()
        for s in target_sessions:
            print(f"\nWarming cache for session '{s.id}'...")
            ctx = session_context(scope, s.id, as_of=ref_date)
            start = time.perf_counter()
            try:
                res = analyze_session(ctx)
                elapsed = time.perf_counter() - start
                print(f"  OK in {elapsed:.2f}s: produced {len(res.findings())} findings")
            except Exception as exc:
                print(f"  FAILED: {exc}")

    cache_stats = stats()
    print("\nCurrent AI cache stats:")
    if cache_stats:
        for fn_name, count in cache_stats.items():
            print(f"  {fn_name}: {count} cached response(s)")
    else:
        print("  (empty)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-warm the AI cache")
    parser.add_argument("--session-id", help="Specific session ID to warm")
    parser.add_argument("--as-of", help="Anchor date (YYYY-MM-DD)", default=None)
    parser.add_argument("--stats", action="store_true", help="Print cache stats and exit")
    args = parser.parse_args()

    if args.stats:
        s = stats()
        print("AI Cache Stats:")
        for fn_name, count in s.items():
            print(f"  {fn_name}: {count}")
        if not s:
            print("  (empty)")
        return

    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    warm_cache(session_id=args.session_id, as_of=as_of)


if __name__ == "__main__":
    main()
