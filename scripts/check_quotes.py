#!/usr/bin/env python3
"""Deterministic grounding gate: keep only facts whose quote LITERALLY appears in the
cited source. This is what makes the report impossible to hallucinate. No LLM.

Usage:
    python check_quotes.py facts_raw.json index.json > facts.json

  facts_raw.json : [{"fact": "...", "quote": "...", "url": "...", "section": "..."}, ...]
  index.json     : {url: path_to_scraped_source_file}
"""
import os
import re
import sys
import json


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("usage: check_quotes.py facts_raw.json index.json\n"); sys.exit(1)
    facts = json.load(open(sys.argv[1]))
    index = json.load(open(sys.argv[2]))

    src_cache = {}
    def source_text(url):
        if url not in src_cache:
            p = index.get(url)
            src_cache[url] = norm(open(p).read()) if (p and os.path.exists(p)) else ""
        return src_cache[url]

    kept = []
    for f in facts:
        q = norm(f.get("quote", ""))
        if len(q) >= 15 and q in source_text(f.get("url", "")):
            kept.append(f)
    for i, f in enumerate(kept):
        f["id"] = i

    print(json.dumps(kept, indent=2))
    sys.stderr.write(f"validated {len(kept)}/{len(facts)} facts "
                     f"({len(facts)-len(kept)} dropped as ungrounded)\n")


if __name__ == "__main__":
    main()
