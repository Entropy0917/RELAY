"""The seam holds, or the build fails.

These tests are the whole reason two people can work on this app at once.
They run on both branches. If either side drifts from the contract, this is
where it surfaces -- not at 3am, and not during the demo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from contracts.routes import NAV, ROUTES
from contracts.viewmodels import VIEWMODELS

FIXTURES = Path(__file__).parent.parent / "contracts" / "fixtures"

RULE_PARAM = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")


@pytest.mark.parametrize("name", sorted(VIEWMODELS))
def test_every_viewmodel_has_a_valid_fixture(name: str) -> None:
    """A fixture that does not validate is a build error, not a warning.

    The frontend designs against these. If one drifts from its model, the
    template built on it will break the moment the real route is wired in.
    """
    path = FIXTURES / f"{name}.json"
    assert path.exists(), (
        f"No fixture for view model '{name}'. "
        f"Run: .venv/Scripts/python -m contracts._build_fixtures"
    )
    VIEWMODELS[name].model_validate_json(path.read_text(encoding="utf-8"))


def test_no_orphan_fixtures() -> None:
    """A fixture with no view model means someone renamed one and missed it."""
    on_disk = {p.stem for p in FIXTURES.glob("*.json")}
    assert on_disk == set(VIEWMODELS), (
        f"orphan fixtures: {sorted(on_disk - set(VIEWMODELS))}, "
        f"missing fixtures: {sorted(set(VIEWMODELS) - on_disk)}"
    )


@pytest.mark.parametrize("key,route", sorted(ROUTES.items()))
def test_route_viewmodel_exists(key: str, route) -> None:
    if route.viewmodel is not None:
        assert route.viewmodel in VIEWMODELS, (
            f"route '{key}' names view model '{route.viewmodel}', which does not exist"
        )


@pytest.mark.parametrize("key,route", sorted(ROUTES.items()))
def test_route_params_match_rule(key: str, route) -> None:
    """`params` is what templates pass to url_for. It must match the URL rule."""
    in_rule = tuple(RULE_PARAM.findall(route.rule))
    assert in_rule == route.params, (
        f"route '{key}': rule declares {in_rule}, params declares {route.params}"
    )


@pytest.mark.parametrize("key,route", sorted(ROUTES.items()))
def test_endpoint_is_blueprint_qualified(key: str, route) -> None:
    """Endpoints are `blueprint.view`. Templates rely on that shape."""
    assert route.endpoint.count(".") == 1, (
        f"route '{key}': endpoint '{route.endpoint}' is not blueprint-qualified"
    )


def test_endpoints_are_unique() -> None:
    endpoints = [r.endpoint for r in ROUTES.values()]
    dupes = {e for e in endpoints if endpoints.count(e) > 1}
    assert not dupes, f"duplicate endpoints: {sorted(dupes)}"


def test_nav_points_at_real_routes() -> None:
    for key, label in NAV:
        assert key in ROUTES, f"NAV entry '{label}' points at unknown route '{key}'"
        assert ROUTES[key].methods == ("GET",), f"NAV route '{key}' must be GET"
        assert not ROUTES[key].params, f"NAV route '{key}' must take no parameters"


def test_partials_return_partial_viewmodels() -> None:
    """A partial renders a fragment, so it must not carry a shell."""
    for key, route in ROUTES.items():
        if route.partial and route.viewmodel:
            fields = VIEWMODELS[route.viewmodel].model_fields
            if route.viewmodel.startswith("partial_"):
                assert "shell" not in fields, (
                    f"partial route '{key}' renders '{route.viewmodel}', "
                    f"which carries a shell"
                )


def test_shell_is_present_on_every_page_viewmodel() -> None:
    """Every full page gets the same chrome. No exceptions, or nav breaks."""
    for name, model in VIEWMODELS.items():
        if name.startswith("partial_"):
            continue
        assert "shell" in model.model_fields, f"page view model '{name}' has no shell"


def test_fixtures_expose_more_than_one_engagement() -> None:
    """Multi-engagement support is a claim we make. Keep it testable.

    If the switcher only ever sees one engagement, nobody notices when the
    engagement scoping silently stops working.
    """
    data = json.loads((FIXTURES / "overview.json").read_text(encoding="utf-8"))
    assert len(data["shell"]["engagements"]) >= 2
