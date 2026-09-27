"""One `get_client()`, five providers, zero call-site changes.

planv0.2.md section 0: the `openai` SDK with a configurable `base_url` is a
single code path for ollama / xAI / OpenAI. Anthropic speaks a different wire
format, so it gets a thin adapter behind the same interface. Swapping provider
is `RELAY_AI_PROVIDER=...`; swapping model is `RELAY_MODEL=...`. No function
module and no route knows which one is live.

STRUCTURED OUTPUT (planv0.2.md section 7 -- measured, do not re-litigate).
Ollama's cloud routing drops constrained decoding: `response_format` and
`format=<schema>` are both no-ops on a cloud-routed model, which is why the
spike saw markdown prose rather than malformed JSON. Local models bind the
grammar correctly. So a client declares `constrained`:

  constrained = False -> run.py puts the schema in the prompt and validates
                         on our side, with one bounded retry.
  constrained = True  -> the schema goes to the sampler; validation still
                         runs, because a grammar does not guarantee semantics.

Cloud vs local is read off the selected model name, which is itself set by an
env var. Nothing here chooses a provider or a model on its own, ever: an
unreachable provider raises, and only a human switches paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.ai.errors import ProviderUnreachable, Timeout

DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "gemma4:31b-cloud"
DEFAULT_TIMEOUT = 180.0

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_CLOUD_HOST = "https://ollama.com"
XAI_BASE_URL = "https://api.x.ai/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

PROVIDERS = ("mock", "ollama", "xai", "anthropic", "openai")

# Ollama names cloud-routed models with this suffix. It is the one signal that
# tells us constrained decoding will be silently ignored (section 7).
CLOUD_SUFFIX = "-cloud"

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class Request:
    """Everything a provider needs for one completion.

    `schema` travels with the request even when the client cannot constrain
    decoding -- run.py has already folded it into `user` in that case, and the
    constrained clients need it here.
    """

    fn_name: str
    system: str
    user: str
    schema: dict[str, Any] = field(default_factory=dict)
    timeout: float = DEFAULT_TIMEOUT


@runtime_checkable
class Client(Protocol):
    """The whole provider surface. Keeping it this small is what makes the
    swap free -- there is nothing provider-shaped for a caller to depend on."""

    provider: str
    model: str
    constrained: bool

    def complete(self, request: Request) -> str:
        """Return the raw assistant text. Validation is run.py's job."""


def get_client(provider: str | None = None, model: str | None = None) -> Client:
    """Build the configured client. Env vars are read on every call.

    `mock` is reachable only because a human typed RELAY_AI_PROVIDER=mock. It
    is never selected as a consequence of another provider failing.
    """
    provider = (provider or os.environ.get("RELAY_AI_PROVIDER") or DEFAULT_PROVIDER).lower()
    model = model or os.environ.get("RELAY_MODEL") or DEFAULT_MODEL

    if provider not in PROVIDERS:
        raise ProviderUnreachable(
            provider,
            f"unknown provider; RELAY_AI_PROVIDER must be one of {', '.join(PROVIDERS)}",
        )
    if provider == "mock":
        return MockClient(model=model)
    if provider == "ollama":
        cloud_key = os.environ.get("OLLAMA_API_KEY")
        if cloud_key:
            # Direct Ollama cloud API: no local daemon. Model names there are
            # bare -- the `-cloud` suffix only tells a local daemon to proxy.
            host = os.environ.get("RELAY_AI_BASE_URL", OLLAMA_CLOUD_HOST).rstrip("/")
            bare = model[: -len(CLOUD_SUFFIX)] if is_cloud_model(model) else model
            return OpenAICompatClient(
                provider="ollama",
                model=bare,
                base_url=f"{host}/v1",
                api_key=cloud_key,
            )
        host = os.environ.get("RELAY_AI_BASE_URL", OLLAMA_HOST).rstrip("/")
        if is_cloud_model(model):
            # Cloud routing ignores the constraint, so do not pretend otherwise.
            return OpenAICompatClient(
                provider="ollama",
                model=model,
                base_url=f"{host}/v1",
                api_key="ollama",  # Ollama ignores it; the SDK requires one.
            )
        return OllamaNativeClient(model=model, host=host)
    if provider == "xai":
        return OpenAICompatClient(
            provider="xai",
            model=model,
            base_url=os.environ.get("RELAY_AI_BASE_URL", XAI_BASE_URL),
            api_key=_require_key("xai", "XAI_API_KEY"),
        )
    if provider == "openai":
        return OpenAICompatClient(
            provider="openai",
            model=model,
            base_url=os.environ.get("RELAY_AI_BASE_URL") or None,
            api_key=_require_key("openai", "OPENAI_API_KEY"),
        )
    return AnthropicClient(
        model=model,
        base_url=os.environ.get("RELAY_AI_BASE_URL", ANTHROPIC_BASE_URL),
        api_key=_require_key("anthropic", "ANTHROPIC_API_KEY"),
    )


def is_cloud_model(model: str) -> bool:
    return model.strip().lower().endswith(CLOUD_SUFFIX)


def _require_key(provider: str, var: str) -> str:
    key = os.environ.get(var)
    if not key:
        raise ProviderUnreachable(provider, f"{var} is not set")
    return key


# ---------------------------------------------------------------------------
# openai SDK -- ollama (cloud) / xai / openai
# ---------------------------------------------------------------------------


class OpenAICompatClient:
    """`/v1/chat/completions`, unconstrained, schema carried in the prompt.

    Section 7 settled that the endpoint itself is fine against Ollama; it is
    the `response_format` field the cloud route ignores. We therefore do not
    send it at all -- putting the schema in the prompt and validating locally
    is provider-portable anyway, and it is what measured 5/5.
    """

    constrained = False

    def __init__(
        self, *, provider: str, model: str, base_url: str | None, api_key: str
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self._api_key = api_key

    def complete(self, request: Request) -> str:
        try:
            from openai import (
                APIConnectionError,
                APIStatusError,
                APITimeoutError,
                OpenAI,
            )
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise ProviderUnreachable(
                self.provider, f"openai SDK not importable: {exc}"
            ) from exc

        kwargs: dict[str, Any] = {"api_key": self._api_key, "timeout": request.timeout}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        client = OpenAI(**kwargs)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
            )
        except APITimeoutError as exc:
            raise Timeout(
                self.provider, request.timeout, fn_name=request.fn_name
            ) from exc
        except APIConnectionError as exc:
            raise ProviderUnreachable(
                self.provider, str(exc), fn_name=request.fn_name
            ) from exc
        except APIStatusError as exc:
            raise ProviderUnreachable(
                self.provider,
                f"HTTP {exc.status_code}: {str(exc)[:300]}",
                fn_name=request.fn_name,
            ) from exc
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Ollama native -- local models only, genuinely constrained
# ---------------------------------------------------------------------------


class OllamaNativeClient:
    """`/api/chat` with `format=<json schema>`.

    Used when RELAY_MODEL names a local model. Section 7's offline path: much
    slower, but the grammar actually binds, so it is strictly better *there*.
    Selecting it is an env-var decision by a human, not a fallback.
    """

    constrained = True
    provider = "ollama"

    def __init__(self, *, model: str, host: str = OLLAMA_HOST) -> None:
        self.model = model
        self.host = host.rstrip("/")

    def complete(self, request: Request) -> str:
        import httpx

        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "stream": False,
        }
        if request.schema:
            body["format"] = request.schema
        try:
            response = httpx.post(
                f"{self.host}/api/chat", json=body, timeout=request.timeout
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise Timeout(
                self.provider, request.timeout, fn_name=request.fn_name
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnreachable(
                self.provider,
                f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
                fn_name=request.fn_name,
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnreachable(
                self.provider, str(exc), fn_name=request.fn_name
            ) from exc
        return response.json().get("message", {}).get("content", "")


# ---------------------------------------------------------------------------
# Anthropic -- different wire format, same interface
# ---------------------------------------------------------------------------


class AnthropicClient:
    """Thin adapter: system is a top-level field and content comes back as
    blocks. Deliberately raw httpx so the package does not gain a dependency
    for a provider the demo does not use."""

    constrained = False
    provider = "anthropic"

    def __init__(self, *, model: str, base_url: str, api_key: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key

    def complete(self, request: Request) -> str:
        import httpx

        try:
            response = httpx.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": request.system,
                    "messages": [{"role": "user", "content": request.user}],
                },
                timeout=request.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise Timeout(
                self.provider, request.timeout, fn_name=request.fn_name
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnreachable(
                self.provider,
                f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
                fn_name=request.fn_name,
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnreachable(
                self.provider, str(exc), fn_name=request.fn_name
            ) from exc
        blocks = response.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


# ---------------------------------------------------------------------------
# Mock -- human-selected only
# ---------------------------------------------------------------------------


class MockClient:
    """Replays app/ai/fixtures/<fn_name>.json.

    Exists for template work and for tests, and is reachable ONLY under
    RELAY_AI_PROVIDER=mock. Nothing in run.py routes here after a failure --
    that would be the silent fallback the whole design exists to prevent. The
    fixtures are sector-neutral by rule (planv0.2.md section 0.5): they must
    never read as the demo engagement.
    """

    constrained = False
    provider = "mock"

    def __init__(self, *, model: str = "fixtures", root: Path | None = None) -> None:
        self.model = model
        self.root = root or FIXTURES

    def complete(self, request: Request) -> str:
        path = self.root / f"{request.fn_name}.json"
        if not path.exists():
            raise ProviderUnreachable(
                self.provider,
                f"no fixture for '{request.fn_name}' at {path}",
                fn_name=request.fn_name,
            )
        return path.read_text(encoding="utf-8")
