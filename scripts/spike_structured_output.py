"""SYNC-1 risk spike: can gemma4:31b-cloud hold RELAY's hardest schema?

Tests the SessionSynthesis model -- 4 heterogeneous nested findings -- which is
both the demo centerpiece and the most structurally demanding AI output in the
product. If this holds, every other schema is easier.

Two candidate paths, per planv0.2.md section 10:
  A. OpenAI-compatible endpoint + response_format json_schema  (one code path
     for ollama / xai / openai -- strongly preferred)
  B. Ollama native /api/chat + format=<json schema>            (fallback path)

Run:  .venv/Scripts/python scripts/spike_structured_output.py
"""

from __future__ import annotations

import json
import statistics
import time
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

MODEL = "gemma4:31b-cloud"
OLLAMA = "http://localhost:11434"
RUNS = 5
TIMEOUT = 180.0


# --------------------------------------------------------------------------
# The hardest schema in the product.
# NOTE: deliberately domain-neutral -- no engagement content (plan section 0.5).
# --------------------------------------------------------------------------
class CapabilityEvidence(BaseModel):
    kind: Literal["capability_evidence"]
    person: str
    capability: str
    evidence: str
    current_level: int = Field(ge=0, le=6)
    suggested_level: int = Field(ge=0, le=6)
    confidence: Literal["low", "medium", "high"]
    evidence_sources: list[str]


class TacitKnowledge(BaseModel):
    kind: Literal["tacit_knowledge"]
    title: str
    operating_model_area: str
    capability: str
    situation: str
    observed_signals: list[str]
    expert_reasoning: str
    recommended_response: str
    why_it_matters: str


class RemainingGap(BaseModel):
    kind: Literal["remaining_gap"]
    capability: str
    understands: str
    not_yet_demonstrated: list[str]


class NextActivity(BaseModel):
    kind: Literal["next_activity"]
    objective: str
    recommended_experience: str
    learner_responsibilities: list[str]
    expert_role: str


class SessionSynthesis(BaseModel):
    capability_evidence: CapabilityEvidence
    tacit_knowledge: TacitKnowledge
    remaining_gap: RemainingGap
    next_activity: NextActivity


SYSTEM = (
    "You are a knowledge-transfer analyst. Given a transfer-session transcript "
    "and debriefs, produce exactly four findings. Cite only what the material "
    "supports. Never invent evidence. Suggested capability levels are "
    "recommendations for human validation, never decisions."
)

# Neutral test payload -- real prompts take engagement context as parameters.
USER = """SESSION TRANSCRIPT
Expert and learner reviewed a replenishment decision for a regional site.
Formal rule: reorder when cover reaches 14 days. Site showed 18 days.
Learner flagged that consumption rose sharply over two weeks, seasonal demand
is beginning, the last physical count is several days stale, and supplier lead
times have lengthened. Learner concluded the static threshold was unreliable.
Expert agreed and added that she would first check whether nearby sites hold
genuine surplus before initiating emergency procurement.

EXPERT DEBRIEF
Q: What made you treat this site differently from the standard rule?
A: Four things together -- consumption trajectory, the season starting, the
count being stale, and lead times moving. Any one alone I might ignore.

LEARNER DEBRIEF
Q: Why was 18 days concerning when the threshold is 14?
A: Because 18 days assumes last month's consumption rate. If consumption is
climbing, 18 days of cover is really more like 11 or 12.
Q: What if redistribution were not possible?
A: I think we would escalate to emergency procurement, but I have not done
that myself.

PRIOR CAPABILITY STATE
Stockout Risk Identification: level 3 (Performed with Supervision)
Emergency Stock Redistribution: level 1 (Observed)
"""


def path_a() -> tuple[list[float], int, str | None]:
    """OpenAI-compatible endpoint with response_format=json_schema."""
    schema = SessionSynthesis.model_json_schema()
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "SessionSynthesis",
                "schema": schema,
                "strict": True,
            },
        },
    }
    lat, ok, err = [], 0, None
    for i in range(RUNS):
        t0 = time.perf_counter()
        try:
            r = httpx.post(
                f"{OLLAMA}/v1/chat/completions", json=body, timeout=TIMEOUT
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            SessionSynthesis.model_validate_json(content)
            ok += 1
        except (httpx.HTTPError, ValidationError, KeyError, json.JSONDecodeError) as e:
            err = err or f"{type(e).__name__}: {str(e)[:200]}"
        lat.append(time.perf_counter() - t0)
        print(f"  run {i + 1}/{RUNS}  {lat[-1]:6.1f}s  {'ok' if ok == i + 1 else 'FAIL'}")
    return lat, ok, err


def path_b() -> tuple[list[float], int, str | None]:
    """Ollama native /api/chat with format=<json schema>."""
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "format": SessionSynthesis.model_json_schema(),
        "stream": False,
    }
    lat, ok, err = [], 0, None
    for i in range(RUNS):
        t0 = time.perf_counter()
        try:
            r = httpx.post(f"{OLLAMA}/api/chat", json=body, timeout=TIMEOUT)
            r.raise_for_status()
            SessionSynthesis.model_validate_json(r.json()["message"]["content"])
            ok += 1
        except (httpx.HTTPError, ValidationError, KeyError, json.JSONDecodeError) as e:
            err = err or f"{type(e).__name__}: {str(e)[:200]}"
        lat.append(time.perf_counter() - t0)
        print(f"  run {i + 1}/{RUNS}  {lat[-1]:6.1f}s  {'ok' if ok == i + 1 else 'FAIL'}")
    return lat, ok, err


def report(name: str, lat: list[float], ok: int, err: str | None) -> None:
    p50 = statistics.median(lat) if lat else 0
    p95 = max(lat) if lat else 0
    print(f"\n{name}")
    print(f"  valid      {ok}/{RUNS}")
    print(f"  cold start {lat[0]:.1f}s" if lat else "  cold start n/a")
    print(f"  p50        {p50:.1f}s")
    print(f"  p95        {p95:.1f}s")
    if err:
        print(f"  first error {err}")


if __name__ == "__main__":
    print(f"model={MODEL}  runs={RUNS}\n")
    print("PATH A -- OpenAI-compatible response_format")
    a = path_a()
    print("\nPATH B -- Ollama native format=")
    b = path_b()
    report("PATH A (preferred: one code path for all providers)", *a)
    report("PATH B (ollama-only fallback)", *b)
