"""Decisive test: which model+path reliably produces RELAY's hardest schema?

Diagnosis established (scripts/spike_diagnose.py):
  - gemma4:31b-cloud IGNORES constrained decoding entirely (format= is a no-op
    on cloud-routed models). It only produces JSON when *asked* to in the
    prompt -- obedience, not a guarantee.
  - Local models (gpt-oss:20b, qwen3.5) DO bind to format=<json schema>.

So the real question is whether prompt-obedience survives a 4-way nested
schema, versus a genuinely constrained local model.
"""

from __future__ import annotations

import json
import statistics
import time

import httpx
from pydantic import ValidationError

from spike_structured_output import SYSTEM, USER, RUNS, SessionSynthesis

OLLAMA = "http://localhost:11434"
SCHEMA = SessionSynthesis.model_json_schema()
TIMEOUT = 300.0

INSTRUCTION = (
    "\n\nRespond with ONLY a single JSON object conforming to this JSON Schema. "
    "No prose, no markdown, no code fences.\n" + json.dumps(SCHEMA)
)


def trial(label: str, model: str, constrained: bool, instructed: bool) -> None:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER + (INSTRUCTION if instructed else "")},
        ],
        "stream": False,
    }
    if constrained:
        body["format"] = SCHEMA

    lat, ok, first_err = [], 0, None
    for _ in range(RUNS):
        t0 = time.perf_counter()
        try:
            r = httpx.post(f"{OLLAMA}/api/chat", json=body, timeout=TIMEOUT)
            r.raise_for_status()
            SessionSynthesis.model_validate_json(r.json()["message"]["content"])
            ok += 1
        except (httpx.HTTPError, ValidationError, KeyError) as e:
            first_err = first_err or f"{type(e).__name__}: {str(e)[:90]}"
        lat.append(time.perf_counter() - t0)

    p50 = statistics.median(lat)
    print(f"{label:46} {ok}/{RUNS} valid  p50 {p50:6.1f}s  max {max(lat):6.1f}s")
    if first_err:
        print(f"{'':46} first error: {first_err}")


if __name__ == "__main__":
    print(f"SessionSynthesis -- 4 nested findings, {RUNS} runs each\n")
    trial("cloud gemma4:31b + instruction (unconstrained)", "gemma4:31b-cloud", False, True)
    trial("gpt-oss:20b  constrained format=<schema>", "gpt-oss:20b", True, False)
    trial("qwen3.5      constrained format=<schema>", "qwen3.5:latest", True, False)
