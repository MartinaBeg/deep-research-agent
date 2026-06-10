"""Web tools: Serper search + Firecrawl scraping (with a simple on-disk cache)."""
import os
import json

import requests
from firecrawl import FirecrawlApp

from . import config

_fc = None


def _firecrawl():
    global _fc
    if _fc is None:
        _fc = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
    return _fc


def serper(query, n=10):
    try:
        r = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"},
            data=json.dumps({"q": query, "num": n}), timeout=20,
        )
        return [o["link"] for o in r.json().get("organic", []) if o.get("link")]
    except Exception:
        return []


def load_cache(path):
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            return {}
    return {}


def save_cache(path, cache):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(cache, open(path, "w"))


def scrape(url, cache):
    """Return (url, markdown_text). Uses cache to avoid re-spending Firecrawl credits."""
    if url in cache and cache[url]:
        return url, cache[url]
    try:
        r = _firecrawl().scrape(url=url, formats=["markdown"])
        bad = r.metadata and getattr(r.metadata, "error", None)
        content = "" if bad else (r.markdown or "")
    except Exception:
        content = ""
    cache[url] = content
    return url, content
