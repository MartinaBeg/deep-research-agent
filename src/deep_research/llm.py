"""LLM wrapper with pluggable providers.

Default provider is **ollama** (a local model on your machine) — free, no API key, no
credits. Other providers (anthropic, openai-compatible) are available by setting
LLM_PROVIDER. The grounding gate works the same regardless of model, so even a small
local model cannot hallucinate.

    complete(prompt, max_tokens, fast=False) -> str
    complete_json(prompt, max_tokens, fast=False) -> parsed JSON or None

`fast=True` picks the cheaper/smaller model where the provider distinguishes them.
"""
import re
import json

import requests

from . import config


# ----------------------------------------------------------------- providers
def _ollama(prompt, max_tokens):
    r = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "num_ctx": config.OLLAMA_NUM_CTX,
                        "temperature": 0},
        },
        timeout=900,
    )
    r.raise_for_status()
    return r.json().get("response", "")


_anthropic_client = None


def _anthropic(prompt, max_tokens, fast):
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, max_retries=12)
    model = config.ANTHROPIC_FAST if fast else config.ANTHROPIC_SMART
    resp = _anthropic_client.messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _openai(prompt, max_tokens, fast):
    """OpenAI-compatible chat endpoint (OpenAI, Groq, or any compatible server)."""
    r = requests.post(
        f"{config.OPENAI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}",
                 "Content-Type": "application/json"},
        json={"model": config.OPENAI_MODEL, "max_tokens": max_tokens,
              "temperature": 0, "messages": [{"role": "user", "content": prompt}]},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def complete(prompt, max_tokens=4000, fast=False):
    p = config.LLM_PROVIDER
    if p == "ollama":
        return _ollama(prompt, max_tokens)
    if p == "anthropic":
        return _anthropic(prompt, max_tokens, fast)
    if p == "openai":
        return _openai(prompt, max_tokens, fast)
    raise SystemExit(f"Unknown LLM_PROVIDER '{p}' (use: ollama | anthropic | openai)")


def complete_json(prompt, max_tokens=4000, fast=False):
    raw = complete(prompt, max_tokens, fast=fast)
    m = re.search(r"(\[.*\]|\{.*\})", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None
