"""Every fixture validates against its view model; every view model has a fixture;
every route references a real view model."""

import json

import pytest

from contracts import FIXTURES, fixture_names, load_fixture
from contracts.routes import ROUTES
from contracts.viewmodels import VIEWMODELS


@pytest.mark.parametrize("name,variant", fixture_names(), ids=lambda v: str(v))
def test_fixture_validates(name, variant):
    assert name in VIEWMODELS, f"fixture {name} has no view model"
    load_fixture(name, variant)


@pytest.mark.parametrize("name", sorted(VIEWMODELS))
def test_every_viewmodel_has_fixture(name):
    assert (FIXTURES / f"{name}.json").exists(), f"missing contracts/fixtures/{name}.json"


def test_fixtures_are_json_objects():
    for p in FIXTURES.glob("*.json"):
        assert isinstance(json.loads(p.read_text()), dict), p.name


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r.name)
def test_route_viewmodel_exists(route):
    if route.viewmodel is not None:
        assert route.viewmodel in VIEWMODELS
        assert route.template is not None


def test_route_names_unique():
    names = [r.name for r in ROUTES]
    assert len(names) == len(set(names))
