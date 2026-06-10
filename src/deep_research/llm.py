"""Thin LLM wrapper (Anthropic Claude). Serialized calls + automatic 429 back-off."""
import re
import json

import anthropic

from . import config

_client = None


def _client_():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, max_retries=12)
    return _client


def claude(prompt, max_tokens=4000, model=None):
    model = model or config.SMART_MODEL
    resp = _client_().messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def claude_json(prompt, max_tokens=4000, model=None):
    raw = claude(prompt, max_tokens, model=model)
    m = re.search(r"(\[.*\]|\{.*\})", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None
