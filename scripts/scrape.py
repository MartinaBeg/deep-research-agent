#!/usr/bin/env python3
"""Scrape pages with Firecrawl and save their text. Prints a JSON {url: filepath} index.
No LLM.

Usage:
    python scrape.py <out_dir> "https://a.com" "https://b.com" ...
    echo "https://a.com" | python scrape.py <out_dir>
Each page's markdown is saved to <out_dir>/<hash>.md (cached). Needs FIRECRAWL_API_KEY.
"""
import os
import sys
import json
import hashlib

from firecrawl import FirecrawlApp
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: scrape.py <out_dir> [urls...]"})); sys.exit(1)
    out_dir = sys.argv[1]
    urls = sys.argv[2:] or [ln.strip() for ln in sys.stdin if ln.strip()]
    os.makedirs(out_dir, exist_ok=True)

    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        print(json.dumps({"error": "FIRECRAWL_API_KEY not set"})); sys.exit(1)
    fc = FirecrawlApp(api_key=key)

    index = {}
    for u in urls:
        path = os.path.join(out_dir, hashlib.md5(u.encode()).hexdigest()[:10] + ".md")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            index[u] = path
            continue
        try:
            content = (fc.scrape(url=u, formats=["markdown"]).markdown) or ""
        except Exception as e:
            sys.stderr.write(f"scrape error {u}: {e}\n")
            content = ""
        if content:
            with open(path, "w") as f:
                f.write(f"<!-- source: {u} -->\n\n{content}")
            index[u] = path

    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
