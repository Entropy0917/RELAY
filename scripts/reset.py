"""Drop, migrate, seed. Sub-second, and safe to run mid-demo.

One rule makes this useful on demo day rather than dangerous: it **preserves
ai_cache**. A reset restores known-good data without costing the warm model
responses that make the demo deterministic. See planv0.2.md section 9.

Usage:
    python scripts/reset.py            # rebuild from seed
    python scripts/reset.py --no-seed  # empty schema only
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.db.connection import connect, db_path, get_engine
from app.db.schema import PRESERVED_TABLES, metadata


def reset(seed: bool = True, verbose: bool = True) -> None:
    started = time.perf_counter()
    engine = get_engine()

    existing = set(inspect(engine).get_table_names())
    doomed = [t for t in existing if t not in PRESERVED_TABLES]
    kept = sorted(existing & PRESERVED_TABLES)

    with connect(engine) as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for name in doomed:
            conn.execute(text(f'DROP TABLE IF EXISTS "{name}"'))
        conn.execute(text("PRAGMA foreign_keys=ON"))

    metadata.create_all(engine)

    if verbose:
        print(f"  dropped {len(doomed)} table(s)")
        print(f"  preserved {kept or 'nothing (no cache yet)'}")
        print(f"  created {len(metadata.tables)} table(s)")

    if seed:
        _seed(verbose)

    if verbose:
        print(f"  {db_path()} ready in {(time.perf_counter() - started) * 1000:.0f}ms")


def _seed(verbose: bool) -> None:
    """Load the seed corpus (B3).

    Absent during concurrent development, which is expected and not an error --
    but it is reported plainly rather than passed over in silence.
    """
    try:
        from seed import load_all
    except ImportError:
        if verbose:
            print("  seed/ not present yet (B3) -- schema created, no data")
        return
    count = load_all()
    if verbose:
        print(f"  seeded {count} row(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-seed", action="store_true", help="schema only")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    reset(seed=not args.no_seed, verbose=not args.quiet)
