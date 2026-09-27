"""The AI layer's promises, tested without a network and without a model.

Three of these tests exist because of a design decision the project owner
reversed deliberately (planv0.2.md section 7): RELAY fails loud. There is no
automatic fallback to a fixture, a mock or another provider. If that rule ever
gets softened by accident, `test_unreachable_provider_never_returns_a_fixture`
and `test_mock_is_only_reachable_when_a_human_asks_for_it` fail.

Nothing here requires Ollama. The HTTP layer is faked; the provider tests
assert on which client got constructed, not on what it would have returned.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from app.ai import cache
from app.ai.errors import ProviderUnreachable, SchemaViolation, Timeout
from app.ai.functions import REGISTRY
from app.ai.provider import (
    AnthropicClient,
    MockClient,
    OllamaNativeClient,
    OpenAICompatClient,
    Request,
    get_client,
)
from app.ai.run import default_timeout, run

FIXTURES = Path(__file__).parent.parent / "app" / "ai" / "fixtures"


class Tiny(BaseModel):
    """A two-field schema, so the runtime is tested rather than a model's prose."""

    headline: str
    items: list[str]


VALID = '{"headline": "ok", "items": ["one"]}'
PROSE = "Sure! Here is my analysis of the session:\n\n- point one\n- point two"


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Every test gets its own cache file and a clean provider environment."""
    monkeypatch.setenv("RELAY_DB", str(tmp_path / "test.db"))
    for var in (
        "RELAY_AI_PROVIDER",
        "RELAY_MODEL",
        "RELAY_AI_BASE_URL",
        "RELAY_AI_TIMEOUT",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OLLAMA_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)


class FakeClient:
    """Records every call so the retry budget can be asserted exactly."""

    provider = "fake"
    model = "fake-model"

    def __init__(self, *replies: str, constrained: bool = False) -> None:
        self.replies = list(replies)
        self.constrained = constrained
        self.calls: list[Request] = []

    def complete(self, request: Request) -> str:
        self.calls.append(request)
        return self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]


class DeadClient:
    provider = "ollama"
    model = "dead-model"
    constrained = False

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: Request) -> str:
        self.calls += 1
        raise ProviderUnreachable(self.provider, "connection refused")


# ---------------------------------------------------------------------------
# Provider selection -- one env var, zero call-site changes
# ---------------------------------------------------------------------------


def test_default_provider_is_ollama_cloud_unconstrained(monkeypatch):
    """Section 7: cloud routing drops the constraint, so we must not claim it."""
    client = get_client()
    assert isinstance(client, OpenAICompatClient)
    assert client.provider == "ollama"
    assert client.model.endswith("-cloud")
    assert client.base_url.endswith("/v1")
    assert client.constrained is False


def test_ollama_api_key_calls_the_cloud_api_directly(monkeypatch):
    """With a key there is no local daemon: ollama.com, bare model name, the key sent."""
    monkeypatch.setenv("OLLAMA_API_KEY", "k-test")
    client = get_client()
    assert isinstance(client, OpenAICompatClient)
    assert client.provider == "ollama"
    assert client.base_url == "https://ollama.com/v1"
    assert not client.model.endswith("-cloud")
    assert client._api_key == "k-test"


def test_local_model_selects_constrained_decoding(monkeypatch):
    """A local model binds format=<schema> properly -- strictly better there."""
    monkeypatch.setenv("RELAY_MODEL", "some-local-model:20b")
    client = get_client()
    assert isinstance(client, OllamaNativeClient)
    assert client.constrained is True


@pytest.mark.parametrize(
    "provider,key_var,expected",
    [
        ("xai", "XAI_API_KEY", OpenAICompatClient),
        ("openai", "OPENAI_API_KEY", OpenAICompatClient),
        ("anthropic", "ANTHROPIC_API_KEY", AnthropicClient),
    ],
)
def test_provider_swap_is_one_env_var(monkeypatch, provider, key_var, expected):
    monkeypatch.setenv("RELAY_AI_PROVIDER", provider)
    monkeypatch.setenv(key_var, "test-key")
    client = get_client()
    assert isinstance(client, expected)
    assert client.provider == provider


def test_missing_credentials_is_unreachable_not_a_fallback(monkeypatch):
    monkeypatch.setenv("RELAY_AI_PROVIDER", "openai")
    with pytest.raises(ProviderUnreachable):
        get_client()


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("RELAY_AI_PROVIDER", "not-a-provider")
    with pytest.raises(ProviderUnreachable):
        get_client()


def test_base_url_is_overridable(monkeypatch):
    monkeypatch.setenv("RELAY_AI_BASE_URL", "http://elsewhere:9999")
    assert get_client().base_url == "http://elsewhere:9999/v1"


def test_mock_is_only_reachable_when_a_human_asks_for_it(monkeypatch):
    """The whole fail-loud design in one assertion."""
    assert not isinstance(get_client(), MockClient)
    monkeypatch.setenv("RELAY_AI_PROVIDER", "mock")
    assert isinstance(get_client(), MockClient)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def test_cache_key_is_stable_across_key_order():
    """Dict ordering must not cause a cold miss during a demo."""
    assert cache.cache_key({"a": 1, "b": [2, 3]}) == cache.cache_key(
        {"b": [2, 3], "a": 1}
    )


def test_cache_key_changes_with_content():
    assert cache.cache_key({"a": 1}) != cache.cache_key({"a": 2})


def test_cache_miss_then_hit():
    key = cache.cache_key({"x": 1})
    assert cache.get("fn", key) is None
    cache.put("fn", key, VALID, model="m", provider="p")
    assert cache.get("fn", key) == VALID


def test_cache_is_scoped_by_function_name():
    key = cache.cache_key({"x": 1})
    cache.put("fn_a", key, VALID, model="m", provider="p")
    assert cache.get("fn_b", key) is None


def test_run_hits_the_cache_without_calling_the_provider():
    client = FakeClient(VALID)
    first = run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    second = run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    assert first == second
    assert len(client.calls) == 1


def test_warm_cache_survives_an_unreachable_provider():
    """Risk 2's mitigation: a pre-warmed demo never touches the network."""
    run("fn", Tiny, {"x": 1}, system="s", user="u", client=FakeClient(VALID))
    dead = DeadClient()
    assert run("fn", Tiny, {"x": 1}, system="s", user="u", client=dead).headline == "ok"
    assert dead.calls == 0


def test_stale_cache_row_is_evicted_not_served():
    key = cache.cache_key({"x": 1})
    cache.put("fn", key, '{"wrong_field": true}', model="m", provider="p")
    client = FakeClient(VALID)
    assert run("fn", Tiny, {"x": 1}, system="s", user="u", client=client).headline == "ok"
    assert len(client.calls) == 1
    assert cache.get("fn", key) is not None  # replaced with the valid response


def test_use_cache_false_always_calls_the_provider():
    client = FakeClient(VALID)
    run("fn", Tiny, {"x": 1}, system="s", user="u", client=client, use_cache=False)
    run("fn", Tiny, {"x": 1}, system="s", user="u", client=client, use_cache=False)
    assert len(client.calls) == 2
    assert cache.stats() == {}


# ---------------------------------------------------------------------------
# Structured output: schema in the prompt, one bounded retry
# ---------------------------------------------------------------------------


def test_unconstrained_client_gets_the_schema_in_the_prompt():
    client = FakeClient(VALID)
    run("fn", Tiny, {"x": 1}, system="s", user="the material", client=client)
    prompt = client.calls[0].user
    assert "the material" in prompt
    assert "JSON SCHEMA:" in prompt
    assert "headline" in prompt


def test_constrained_client_gets_the_schema_on_the_request_not_the_prompt():
    client = FakeClient(VALID, constrained=True)
    run("fn", Tiny, {"x": 1}, system="s", user="the material", client=client)
    assert "JSON SCHEMA:" not in client.calls[0].user
    assert client.calls[0].schema["properties"].keys() >= {"headline", "items"}


def test_fenced_json_is_accepted():
    client = FakeClient(f"```json\n{VALID}\n```")
    assert run("fn", Tiny, {"x": 1}, system="s", user="u", client=client).headline == "ok"
    assert len(client.calls) == 1


def test_retry_fires_exactly_once_and_then_succeeds():
    client = FakeClient(PROSE, VALID)
    result = run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    assert result.headline == "ok"
    assert len(client.calls) == 2
    retry_prompt = client.calls[1].user
    assert "VALIDATION ERROR" in retry_prompt
    assert "YOUR PREVIOUS RESPONSE" in retry_prompt


def test_retry_is_the_same_provider_and_model():
    """Section 7: the retry is the same path, not a provider substitution."""
    client = FakeClient(PROSE, VALID)
    run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    assert {c.fn_name for c in client.calls} == {"fn"}
    assert len(client.calls) == 2  # never a third, never a different client


def test_second_failure_raises_schema_violation_with_the_evidence():
    client = FakeClient(PROSE, PROSE)
    with pytest.raises(SchemaViolation) as excinfo:
        run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    assert len(client.calls) == 2
    error = excinfo.value
    assert error.attempts == 2
    assert error.schema == "Tiny"
    assert "point one" in error.raw
    assert error.as_error_partial().kind == "schema_violation"


def test_schema_violation_caches_nothing():
    client = FakeClient(PROSE, PROSE)
    with pytest.raises(SchemaViolation):
        run("fn", Tiny, {"x": 1}, system="s", user="u", client=client)
    assert cache.stats() == {}


# ---------------------------------------------------------------------------
# Fail loud
# ---------------------------------------------------------------------------


def test_unreachable_provider_never_returns_a_fixture():
    """The single most important behaviour in the package."""
    dead = DeadClient()
    with pytest.raises(ProviderUnreachable):
        run("prepare_session", Tiny, {"x": 1}, system="s", user="u", client=dead)
    assert dead.calls == 1  # one attempt, no retry, no second provider
    assert cache.stats() == {}


def test_transport_failure_maps_to_provider_unreachable(monkeypatch):
    def refuse(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", refuse)
    client = OllamaNativeClient(model="some-local-model:20b")
    with pytest.raises(ProviderUnreachable):
        client.complete(Request(fn_name="fn", system="s", user="u", schema={}))


def test_transport_timeout_maps_to_timeout(monkeypatch):
    def stall(*args, **kwargs):
        raise httpx.ReadTimeout("too slow")

    monkeypatch.setattr(httpx, "post", stall)
    client = OllamaNativeClient(model="some-local-model:20b")
    with pytest.raises(Timeout):
        client.complete(Request(fn_name="fn", system="s", user="u", schema={}))


def test_http_error_status_maps_to_provider_unreachable(monkeypatch):
    def server_error(*args, **kwargs):
        return httpx.Response(
            500, text="upstream failed", request=httpx.Request("POST", "http://x")
        )

    monkeypatch.setattr(httpx, "post", server_error)
    client = OllamaNativeClient(model="some-local-model:20b")
    with pytest.raises(ProviderUnreachable):
        client.complete(Request(fn_name="fn", system="s", user="u", schema={}))


def test_errors_render_as_the_frozen_error_contract():
    partial = ProviderUnreachable("ollama", "connection refused").as_error_partial(
        retry_href="/retry"
    )
    assert partial.kind == "provider_unreachable"
    assert partial.retry_href == "/retry"
    assert "connection refused" in partial.detail


# ---------------------------------------------------------------------------
# The fourteen functions and their schemas
# ---------------------------------------------------------------------------


def test_registry_covers_the_functions_the_spec_names():
    assert len(REGISTRY) == 14
    assert len({fn.spec_name for fn in REGISTRY.values()}) == 14


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_every_schema_round_trips_its_fixture(name):
    """A mock fixture that no longer validates is a build error, not a warning."""
    fn = REGISTRY[name]
    path = FIXTURES / f"{name}.json"
    assert path.exists(), (
        f"no mock fixture for '{name}'. "
        f"Run: .venv/Scripts/python -m app.ai._build_fixtures"
    )
    parsed = fn.schema.model_validate_json(path.read_text(encoding="utf-8"))
    assert json.loads(parsed.model_dump_json()) == json.loads(
        path.read_text(encoding="utf-8")
    )


def test_no_orphan_fixtures():
    on_disk = {p.stem for p in FIXTURES.glob("*.json")}
    assert on_disk == set(REGISTRY)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_mock_provider_serves_every_function(name):
    fn = REGISTRY[name]
    raw = MockClient().complete(
        Request(fn_name=name, system="s", user="u", schema={})
    )
    assert fn.schema.model_validate_json(raw)


def test_mock_provider_raises_for_an_unknown_function():
    with pytest.raises(ProviderUnreachable):
        MockClient().complete(
            Request(fn_name="no_such_function", system="s", user="u", schema={})
        )


def test_session_brief_matches_the_frozen_viewmodel():
    """B6 passes one straight to the other; keep the field names aligned."""
    from contracts.viewmodels import SessionBriefVM

    brief = REGISTRY["prepare_session"].schema
    assert set(brief.model_fields) == set(SessionBriefVM.model_fields)
    payload = json.loads((FIXTURES / "prepare_session.json").read_text(encoding="utf-8"))
    assert SessionBriefVM.model_validate(payload)


def test_synthesis_finding_kinds_match_the_vocabulary():
    from contracts.vocabulary import FindingKind

    synthesis = REGISTRY["analyze_session"].schema
    assert set(synthesis.model_fields) == {k.value for k in FindingKind}


def test_capability_levels_are_bounded_by_the_ladder():
    """An AI must not invent a level 7. The schema is the guard."""
    from app.ai.schemas import CapabilityFinding

    with pytest.raises(ValidationError):
        CapabilityFinding(
            person="x",
            capability="y",
            current_level=3,
            suggested_level=7,
            evidence="e",
            evidence_sources=["s"],
            confidence="high",
        )


def test_default_timeout_is_configurable(monkeypatch):
    monkeypatch.setenv("RELAY_AI_TIMEOUT", "5")
    assert default_timeout() == 5.0
