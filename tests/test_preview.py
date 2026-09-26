"""Frontend preview harness: every contract fixture renders through its template."""

import pytest

from app import create_app
from app.preview import FIXTURES, TEMPLATES
from contracts.vocabulary import STAGE_ORDER


@pytest.fixture(scope="module")
def client():
    return create_app({"TESTING": True}).test_client()


def test_every_viewmodel_has_a_template():
    from contracts.viewmodels import VIEWMODELS
    assert set(VIEWMODELS) == set(TEMPLATES)


@pytest.mark.parametrize("path", ["/preview/", "/preview/_shell", "/preview/_macros"])
def test_harness_pages(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("name", sorted(p.stem for p in FIXTURES.glob("*.json")))
def test_fixture_renders(client, name):
    r = client.get(f"/preview/{name}")
    assert r.status_code == 200, r.text[:500]
    assert "not written yet" not in r.text, f"{name} fell back to the missing-template page"


@pytest.mark.parametrize("stage", [s.value for s in STAGE_ORDER])
def test_session_stage_renders_every_stage(client, stage):
    r = client.get(f"/preview/session_stage?stage={stage}")
    assert r.status_code == 200
    assert "not written yet" not in r.text
