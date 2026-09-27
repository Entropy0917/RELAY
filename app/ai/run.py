"""The one execution path: cache -> live -> RAISE.

Every AI function in RELAY goes through `run()`. That is what makes the
fail-loud policy checkable in one place rather than fourteen.

  1. CACHE. Hit returns immediately, so a rehearsed demo is deterministic and
     never touches the network (planv0.2.md risks 2 and 8).
  2. LIVE. Miss calls the configured provider. One call.
  3. VALIDATE. Pydantic, on our side, always -- including when the provider
     claims to have constrained decoding. An unvalidated response never
     reaches a caller, a template or the database.
  4. RETRY, EXACTLY ONCE. On a validation failure, the same provider and the
     same model are called again with the validation error appended to the
     prompt. Section 7 approved this precisely because it is a retry of the
     *same* path: it is not a provider substitution and not a fallback.
  5. RAISE. Second failure -> SchemaViolation carrying the validation error
     and the raw response. Nothing is cached, nothing is saved, nothing
     placeholder is returned. Provider down -> ProviderUnreachable.

What this module will never do: return a fixture, degrade to a mock, retry on
a different provider, or invent a partial answer. `mock` is reachable only
when a human sets RELAY_AI_PROVIDER=mock.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai import cache
from app.ai.errors import SchemaViolation
from app.ai.provider import Client, Request, get_client

M = TypeVar("M", bound=BaseModel)

MAX_ATTEMPTS = 2  # one call, one corrective retry. Not a tunable.

# Models fence JSON about half the time even when told not to. Cheaper to
# tolerate here than to spend a retry on it.
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)

JSON_INSTRUCTION = """
Return ONLY a single JSON object matching this JSON Schema. No prose, no
markdown, no code fence, no explanation before or after. Every required
property must be present. Use only information supported by the material
above; if something is not supported, say so inside a field rather than
inventing it.

JSON SCHEMA:
{schema}
""".strip()

RETRY_INSTRUCTION = """
Your previous response did not validate against the required schema.

VALIDATION ERROR:
{error}

YOUR PREVIOUS RESPONSE:
{raw}

Return the corrected object now: a single JSON object, schema-valid, nothing
else. Keep the analysis you already produced where it was valid.
""".strip()


def default_timeout() -> float:
    return float(os.environ.get("RELAY_AI_TIMEOUT", "180"))


def run(
    fn_name: str,
    model_cls: type[M],
    inputs: Mapping[str, Any],
    *,
    system: str,
    user: str,
    client: Client | None = None,
    timeout: float | None = None,
    use_cache: bool = True,
) -> M:
    """Execute one AI function and return validated, typed data.

    `inputs` is the engagement context the caller passed in -- it is the cache
    key, so it must contain everything that should change the answer and
    nothing that should not (no model name, no timestamps).

    Raises ProviderUnreachable / Timeout / SchemaViolation. Never returns None.
    """
    key = cache.cache_key(inputs)
    if use_cache:
        cached = cache.get(fn_name, key)
        if cached is not None:
            try:
                return model_cls.model_validate_json(cached)
            except ValidationError:
                # A schema changed under a warm row. Evict rather than serve
                # data the caller's type says is impossible.
                cache.drop(fn_name, key)

    client = client or get_client()
    schema = model_cls.model_json_schema()
    timeout = timeout if timeout is not None else default_timeout()

    # Constrained clients bind the schema at the sampler; unconstrained ones
    # only ever see it if we put it in the prompt (section 7).
    prompt = user if client.constrained else _with_schema(user, schema)

    raw = client.complete(
        Request(
            fn_name=fn_name, system=system, user=prompt, schema=schema, timeout=timeout
        )
    )
    try:
        result = _validate(model_cls, raw)
    except ValidationError as first:
        retry_prompt = _with_correction(prompt, first, raw)
        raw = client.complete(
            Request(
                fn_name=fn_name,
                system=system,
                user=retry_prompt,
                schema=schema,
                timeout=timeout,
            )
        )
        try:
            result = _validate(model_cls, raw)
        except ValidationError as second:
            raise SchemaViolation(
                fn_name,
                model_cls.__name__,
                str(second),
                raw,
                attempts=MAX_ATTEMPTS,
            ) from second

    if use_cache:
        cache.put(
            fn_name,
            key,
            result.model_dump_json(),
            model=client.model,
            provider=client.provider,
        )
    return result


def _with_schema(user: str, schema: dict[str, Any]) -> str:
    return f"{user}\n\n{JSON_INSTRUCTION.format(schema=json.dumps(schema, indent=2))}"


def _with_correction(prompt: str, error: ValidationError, raw: str) -> str:
    return (
        f"{prompt}\n\n"
        + RETRY_INSTRUCTION.format(error=str(error)[:2000], raw=raw[:4000])
    )


def _validate(model_cls: type[M], raw: str) -> M:
    """Parse and validate. Malformed JSON surfaces as ValidationError too, so
    the retry path covers prose responses as well as wrong-shape ones."""
    return model_cls.model_validate_json(_strip_fence(raw))


def _strip_fence(raw: str) -> str:
    match = _FENCE.match(raw or "")
    if match:
        return match.group(1)
    # Some models prepend a sentence. If there is an object in there, take it.
    text = (raw or "").strip()
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return text[start : end + 1]
    return text
