"""Why did the schema get ignored? Isolate the cause before choosing a fix.

Hypotheses:
  H1 cloud-routed models ignore constrained decoding (format/response_format)
  H2 the schema is too complex, and simpler schemas do bind
  H3 no instruction in the prompt, so the model free-forms regardless
"""

from __future__ import annotations

import json

import httpx
from pydantic import BaseModel

OLLAMA = "http://localhost:11434"
T = 120.0


class Tiny(BaseModel):
    person: str
    level: int


TINY_SCHEMA = Tiny.model_json_schema()
ASK = "Report that the learner is at capability level 3."


def probe(label: str, model: str, body_extra: dict, prompt: str, native: bool) -> None:
    if native:
        url, body = f"{OLLAMA}/api/chat", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            **body_extra,
        }
    else:
        url, body = f"{OLLAMA}/v1/chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **body_extra,
        }
    try:
        r = httpx.post(url, json=body, timeout=T)
        if r.status_code != 200:
            print(f"{label:52} HTTP {r.status_code}  {r.text[:120]}")
            return
        d = r.json()
        content = (
            d["message"]["content"] if native else d["choices"][0]["message"]["content"]
        )
        head = content[:70].replace("\n", " ")
        try:
            json.loads(content)
            verdict = "JSON OK"
        except json.JSONDecodeError:
            verdict = "NOT JSON"
        print(f"{label:52} {verdict:9} | {head}")
    except httpx.HTTPError as e:
        print(f"{label:52} ERROR {type(e).__name__}: {str(e)[:80]}")


if __name__ == "__main__":
    print("H1/H2 -- tiny schema, does constrained decoding bind at all?\n")
    probe("cloud  native format=<tiny schema>", "gemma4:31b-cloud", {"format": TINY_SCHEMA}, ASK, True)
    probe("cloud  native format='json'", "gemma4:31b-cloud", {"format": "json"}, ASK, True)
    probe("local  native format=<tiny schema>", "gemma4:26b", {"format": TINY_SCHEMA}, ASK, True)
    probe("local  native format='json'", "gemma4:26b", {"format": "json"}, ASK, True)
    probe("qwen   native format=<tiny schema>", "qwen3.5:latest", {"format": TINY_SCHEMA}, ASK, True)
    probe("gptoss native format=<tiny schema>", "gpt-oss:20b", {"format": TINY_SCHEMA}, ASK, True)

    print("\nH3 -- does an explicit JSON instruction rescue the cloud model?\n")
    instructed = ASK + "\n\nRespond with ONLY a JSON object matching this schema, no prose, no markdown:\n" + json.dumps(TINY_SCHEMA)
    probe("cloud  format=<schema> + instruction", "gemma4:31b-cloud", {"format": TINY_SCHEMA}, instructed, True)
    probe("cloud  instruction only, no format", "gemma4:31b-cloud", {}, instructed, True)
