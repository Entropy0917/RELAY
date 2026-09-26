"""Joint, frozen contract between backend and frontend. See planv0.2 §1."""

import json
from pathlib import Path

from contracts.viewmodels import VIEWMODELS, VM

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_path(name: str, variant: str | None = None) -> Path:
    return FIXTURES / (f"{name}__{variant}.json" if variant else f"{name}.json")


def load_fixture(name: str, variant: str | None = None) -> VM:
    """Load and validate a fixture. `<name>__<variant>.json` holds alternate states
    (e.g. `session_synthesis__ai_error`) validated against the same model."""
    model = VIEWMODELS[name]
    return model.model_validate(json.loads(fixture_path(name, variant).read_text()))


def fixture_names() -> list[tuple[str, str | None]]:
    """Every (name, variant) pair present on disk."""
    out = []
    for p in sorted(FIXTURES.glob("*.json")):
        name, _, variant = p.stem.partition("__")
        out.append((name, variant or None))
    return out
