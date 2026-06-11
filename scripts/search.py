#!/usr/bin/env python3
"""Web search via Serper -> JSON list of result URLs (most-cited first). No LLM.

Usage:
    python search.py "query one" "query two" ...
    echo "query" | python search.py
Needs SERPER_API_KEY in the environment (or a .env in the working dir).
"""
import os
import sys
import json
from collections import defaultdict

import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def main():
    queries = sys.argv[1:] or [ln.strip() for ln in sys.stdin if ln.strip()]
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        print(json.dumps({"error": "SERPER_API_KEY not set"})); sys.exit(1)
    if not queries:
        print(json.dumps({"error": "no queries provided"})); sys.exit(1)

    freq = defaultdict(int)
    for q in queries:
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                data=json.dumps({"q": q, "num": 10}), timeout=20,
            )
            for o in r.json().get("organic", []):
                if o.get("link"):
                    freq[o["link"].split("#")[0]] += 1
        except Exception as e:
            sys.stderr.write(f"search error for {q!r}: {e}\n")

    print(json.dumps(sorted(freq, key=lambda u: (-freq[u], len(u))), indent=2))


if __name__ == "__main__":
    main()
