"""Provider-agnostic LLM client with a fallback chain (Google AI Studio, OpenRouter, Ollama).
Every call is logged with latency and token counts for the write-up's cost section."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import httpx

from .config import ROOT

LOG = ROOT / "data" / "llm_calls.jsonl"


class LLMError(Exception):
    pass


def chain() -> list[tuple[str, str]]:
    raw = os.getenv("LLM_CHAIN", "google:gemma-4-31b-it,google:gemma-4-26b-a4b-it,openrouter:nvidia/nemotron-3-super-120b-a12b:free")
    return [tuple(x.strip().split(":", 1)) for x in raw.split(",") if x.strip()]


def _google(model, system, prompt, temperature, max_tokens):
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise LLMError("GOOGLE_API_KEY missing")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                   headers={"x-goog-api-key": key}, json=body, timeout=120)
    if r.status_code != 200:
        raise LLMError(f"google {r.status_code}: {r.text[:200]}")
    j = r.json()
    parts = j.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    u = j.get("usageMetadata", {})
    return text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)


def _openai_compat(base, key, model, system, prompt, temperature, max_tokens):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    r = httpx.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                   json={"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}, timeout=120)
    if r.status_code != 200:
        raise LLMError(f"{base} {r.status_code}: {r.text[:200]}")
    j = r.json()
    u = j.get("usage", {})
    return j["choices"][0]["message"]["content"] or "", u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def complete(prompt: str, system: str = "", temperature: float = 0.1, max_tokens: int = 2048, purpose: str = "") -> str:
    errors = []
    for provider, model in chain():
        for attempt in range(2):
            t0 = time.time()
            try:
                if provider == "google":
                    text, tin, tout = _google(model, system, prompt, temperature, max_tokens)
                elif provider == "openrouter":
                    text, tin, tout = _openai_compat("https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY", ""),
                                                     model, system, prompt, temperature, max_tokens)
                elif provider == "ollama":
                    text, tin, tout = _openai_compat("http://localhost:11434/v1", "ollama", model, system, prompt, temperature, max_tokens)
                else:
                    raise LLMError(f"unknown provider {provider}")
                _log(provider, model, purpose, time.time() - t0, tin, tout, True)
                return text
            except (LLMError, httpx.HTTPError, KeyError, IndexError) as e:
                _log(provider, model, purpose, time.time() - t0, 0, 0, False, str(e)[:200])
                errors.append(f"{provider}:{model}: {e}")
                if any(c in str(e) for c in ("429", "500", "503")):
                    time.sleep(2 * (attempt + 1))
                    continue
                break
    raise LLMError(" | ".join(errors))


def complete_json(prompt: str, system: str = "", purpose: str = "", **kw) -> dict:
    text = complete(prompt, system, purpose=purpose, **kw)
    return parse_json(text)


def parse_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    s, e = t.find("{"), t.rfind("}")
    if s < 0 or e < 0:
        raise LLMError(f"no JSON in output: {text[:200]}")
    return json.loads(t[s:e + 1])


def _log(provider, model, purpose, secs, tin, tout, ok, err=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "provider": provider, "model": model, "purpose": purpose, "secs": round(secs, 2),
                            "in": tin, "out": tout, "ok": ok, "err": err}) + "\n")
