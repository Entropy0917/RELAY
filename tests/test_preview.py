"""Every fixture renders through the preview harness without error."""

import pytest

from app import create_app
from contracts import fixture_names


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def test_index(client):
    assert client.get("/preview/").status_code == 200


@pytest.mark.parametrize("name,variant", fixture_names(), ids=lambda v: str(v))
def test_fixture_renders(client, name, variant):
    url = f"/preview/{name}" + (f"?variant={variant}" if variant else "")
    assert client.get(url).status_code == 200
