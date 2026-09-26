"""Reusability constraint (planv0.2 §0.5): no seed proper noun may appear outside
seed/. A hit here is a defect, not a warning."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANNED = ["app", "templates", "contracts", "static"]
SUFFIXES = {".py", ".html", ".jinja", ".j2", ".json", ".css", ".js", ".txt", ".md"}

# Word-boundary, case-insensitive. Extend as the seed grows.
BANLIST = [
    "Kwame", "Mensah", "Mitchell", "Ama", "Boateng", "Kojo", "Asare",
    "Ghana", "Ghanaian", "Clinic 14", "antimalarial", "antimalarials",
    "Peace Corps",
]
PATTERN = re.compile(r"\b(" + "|".join(re.escape(w) for w in BANLIST) + r")\b", re.IGNORECASE)


def test_no_seed_proper_nouns_outside_seed():
    hits = []
    for top in SCANNED:
        base = ROOT / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in SUFFIXES:
                for n, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
                    if m := PATTERN.search(line):
                        hits.append(f"{path.relative_to(ROOT)}:{n}: {m.group(0)!r}")
    assert not hits, "seed content leaked outside seed/:\n" + "\n".join(hits)
