"""RELAY is a product, not one demo.

planv0.2.md section 0.5 draws the line: the RELAY *model* (rails, levels,
statuses, stages) lives in code; everything an engagement fills in lives in
the database. This test enforces the half that is easy to violate by accident
-- demo content leaking into code or templates.

If you need a name, a sector or a number on screen, it comes from a table.
The only place demo content is allowed is seed/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

# Code and templates. NOT seed/ -- that is where engagement content belongs.
SCANNED = ["app", "contracts", "templates", "static", "tests"]

# Proper nouns and specifics from the demo engagement. Case-insensitive.
BANNED = [
    "kwame",
    "mensah",
    "boateng",
    "kojo",
    "asare",
    "sarah mitchell",
    "dr. mitchell",
    "ghana",
    "ghanaian",
    "accra",
    "clinic 14",
    "antimalarial",
    "artemether",
    "community health worker",
]

# Sector words that would hard-wire the product to one kind of engagement.
BANNED_DOMAIN = [
    "stockout",
    "malaria",
    "patient",
    "clinic",
]

ALLOWED_SUFFIXES = {".py", ".html", ".jinja", ".css", ".js", ".json", ".toml"}

# This file necessarily contains the banlist.
SELF = Path(__file__).resolve()


def scanned_files() -> list[Path]:
    out = []
    for d in SCANNED:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if (
                p.is_file()
                and p.suffix in ALLOWED_SUFFIXES
                and "__pycache__" not in p.parts
                and p.resolve() != SELF
            ):
                out.append(p)
    return out


def test_something_is_actually_scanned() -> None:
    """Guards against the banlist silently passing because it scanned nothing."""
    assert scanned_files(), f"no files found under {SCANNED} -- the ban test is vacuous"


@pytest.mark.parametrize("term", BANNED)
def test_no_demo_engagement_content_in_code(term: str) -> None:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    hits = [
        f"{p.relative_to(ROOT)}:{i}"
        for p in scanned_files()
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]
    assert not hits, (
        f"'{term}' is demo engagement content and belongs in seed/, not in code.\n"
        + "\n".join(f"  {h}" for h in hits)
    )


@pytest.mark.parametrize("term", BANNED_DOMAIN)
def test_no_sector_assumptions_in_code(term: str) -> None:
    """The product must read the same for a manufacturing or utilities handover."""
    pattern = re.compile(rf"\b{re.escape(term)}\w*", re.IGNORECASE)
    hits = [
        f"{p.relative_to(ROOT)}:{i}"
        for p in scanned_files()
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]
    assert not hits, (
        f"'{term}' hard-wires one sector into the product.\n"
        + "\n".join(f"  {h}" for h in hits)
    )


def test_fixtures_use_a_different_engagement_than_the_demo() -> None:
    """The frontend harness must never run on demo content.

    If a template only looks right with the demo engagement in it, that is a
    bug we want to find in the preview harness on day one -- not on stage.
    """
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "contracts" / "fixtures").glob("*.json")
    ).lower()
    assert blob, "no fixtures found"
    for term in BANNED:
        assert term not in blob, f"fixture content contains demo term '{term}'"
