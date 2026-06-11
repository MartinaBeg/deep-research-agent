"""The grounded extract-then-write pipeline.

plan -> search -> scrape -> extract(+quote-validate) -> write -> verify -> assemble -> PDF.
Every sentence that survives is backed by a quote that literally appears in a source.
"""
import os
import re
import concurrent.futures as cf
from collections import defaultdict

from . import config, llm, web, pdf

SOURCE_CHARS = config.SOURCE_CHARS
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
MARK = re.compile(r"\[F(\d+)\]")


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


# ------------------------------------------------------------------- 0. PLAN
PLAN_PROMPT = """You are planning an in-depth, well-structured research report about:
"{topic}"

Propose the report's sections, adapted to what this subject actually IS (a company,
a person, a product, an event, a place, etc.) — do not force a company template onto
a person, or vice versa.

Return ONLY JSON:
{{"sections": [
   {{"key": "<short_snake_case>",
     "title": "<readable section title>",
     "queries": ["<google search query>", "<another>", "<another>"]}},
   ... 6 to 8 sections ...
]}}

- Cover the most important dimensions of THIS subject comprehensively.
- Each section needs 2-3 effective web-search queries to find sources for it.
"""


def plan_report(topic):
    data = llm.complete_json(PLAN_PROMPT.format(topic=topic), max_tokens=1500)
    secs = (data or {}).get("sections") if isinstance(data, dict) else None
    plan = []
    if secs:
        for s in secs:
            key = re.sub(r"[^a-z0-9]+", "_", (s.get("key") or "").lower()).strip("_")
            title = s.get("title") or key.replace("_", " ").title()
            queries = [q for q in (s.get("queries") or []) if q] or [f"{topic} {title}"]
            if key:
                plan.append({"key": key, "title": title, "queries": queries})
    if not plan:
        plan = [{"key": "overview", "title": "Overview",
                 "queries": [f"{topic} overview", f"{topic} about"]}]
    return plan


# ------------------------------------------------------------------- 1. SEARCH
def gather_sources(plan):
    freq = defaultdict(int)
    for sec in plan:
        for query in sec["queries"]:
            for url in web.serper(query):
                freq[url.split("#")[0]] += 1
    ranked = sorted(freq, key=lambda u: (-freq[u], len(u)))
    return ranked[:config.MAX_SOURCES]


# ------------------------------------------------------------------- 3. EXTRACT
EXTRACT_PROMPT = """Extract atomic, verifiable facts about "{topic}" from the SOURCE below.

Return ONLY a JSON list. Each item:
{{"fact": "<one factual sentence about {topic}>",
  "quote": "<a SHORT verbatim span copied EXACTLY from the source that supports the fact>",
  "section": "<one of: {sections}>"}}

Rules:
- The "quote" MUST be copied character-for-character from the source text.
- Only include facts the source actually states. Do not infer or generalize.
- Skip navigation, ads, and unrelated content.
- Be EXHAUSTIVE: extract EVERY distinct, substantive fact the source supports
  (aim for 15-40 facts on a rich page). Capture specifics — product names,
  features, numbers, customers, problems addressed, use cases, technical details.

SOURCE ({url}):
\"\"\"
{source}
\"\"\"
"""


def extract_facts(topic, url, content, section_keys):
    data = llm.complete_json(
        EXTRACT_PROMPT.format(topic=topic, url=url, sections=", ".join(section_keys),
                              source=content[:SOURCE_CHARS]),
        max_tokens=4000, fast=True,
    )
    if not isinstance(data, list):
        return []
    nsrc = _norm(content)
    out = []
    for d in data:
        quote = (d.get("quote") or "").strip()
        fact = (d.get("fact") or "").strip()
        sec = d.get("section") if d.get("section") in section_keys else section_keys[0]
        if not fact or len(quote) < 15:
            continue
        if _norm(quote) not in nsrc:          # HARD grounding check
            continue
        out.append({"fact": fact, "quote": quote, "url": url, "section": sec})
    return out


# ------------------------------------------------------------------- 4. WRITE
WRITE_PROMPT = """You are writing the "{title}" section of an in-depth report about "{topic}".

You may use ONLY the numbered FACTS below. Write a thorough, well-organized section
(multiple paragraphs; use ### sub-headings and bulleted lists where helpful).

ABSOLUTE RULES:
- Every sentence that states information MUST end with a citation marker naming the
  fact id(s) it draws from, e.g. [F12] or [F12][F7].
- Do NOT state anything that is not contained in the facts. No outside knowledge.
- Be comprehensive: use as many of the relevant facts as you reasonably can, and
  group related facts into coherent prose. Do not pad or repeat.

FACTS:
{facts}

Write the section now (start with "## {title}"). Markdown only.
"""


def write_section(topic, title, facts):
    if not facts:
        return ""
    listing = "\n".join(f"[F{f['id']}] {f['fact']}" for f in facts)
    return llm.complete(WRITE_PROMPT.format(title=title, topic=topic, facts=listing), max_tokens=4000)


# ------------------------------------------------------------------- 5. VERIFY
VERIFY_PROMPT = """For each numbered item, decide if the STATEMENT is supported by its FACT(S).
Return ONLY JSON: [{{"n": <int>, "ok": true|false}}]. Mark ok=false if the statement
claims more than the facts support.

{items}
"""


def verify_sentences(units, facts_by_id):
    if not units:
        return set()
    blocks = []
    for i, (sent, ids) in enumerate(units, 1):
        ev = " ".join(f'FACT[F{j}]: "{facts_by_id[j]["quote"]}"' for j in ids if j in facts_by_id)
        blocks.append(f"{i}. STATEMENT: {sent}\n   {ev}")
    data = llm.complete_json(VERIFY_PROMPT.format(items="\n".join(blocks)),
                             max_tokens=1500, fast=True)
    passed = set()
    if isinstance(data, list):
        for d in data:
            if d.get("ok") and isinstance(d.get("n"), int):
                passed.add(d["n"] - 1)
    return passed


def process_section(section_md, facts_by_id):
    """Verify each cited sentence; drop unsupported/uncited prose. Keep headings/tables."""
    out_lines = []
    for line in section_md.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("|") or not stripped:
            out_lines.append(("raw", line))
            continue
        bullet = ""
        mb = re.match(r"^([-*]\s+)", line)
        if mb:
            bullet = mb.group(1)
            line = line[len(bullet):]
        for sent in SENT_SPLIT.split(line):
            ids = [int(x) for x in MARK.findall(sent)]
            clean = MARK.sub("", sent).strip()
            if not clean or not ids:           # uncited prose -> drop
                continue
            out_lines.append(("sent", (bullet, clean, ids)))
            bullet = ""

    units = [(c, ids) for t, (_, c, ids) in ((t, v) for t, v in out_lines if t == "sent")]
    passed = verify_sentences(units, facts_by_id)

    result, si = [], 0
    for t, v in out_lines:
        if t == "raw":
            result.append(v)
        else:
            if si in passed:
                result.append(v)
            si += 1
    return result


# ------------------------------------------------------------------- ORCHESTRATE
def run(topic, make_pdf=True):
    config.require_keys()
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    cache_path = os.path.join(config.OUTPUT_DIR, "sources_cache.json")

    print(f"\n🔎 Grounded research on: {topic}\n")

    print("0) Planning report structure...")
    plan = plan_report(topic)
    sections = [(s["key"], s["title"]) for s in plan]
    section_keys = [s["key"] for s in plan]
    print(f"   {len(plan)} sections: {', '.join(section_keys)}")

    print("1) Searching (Serper)...")
    urls = gather_sources(plan)
    print(f"   {len(urls)} candidate sources")

    print("2) Scraping (Firecrawl)...")
    cache = web.load_cache(cache_path)
    texts = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for url, content in ex.map(lambda u: web.scrape(u, cache), urls):
            if content:
                texts[url] = content
    web.save_cache(cache_path, cache)
    print(f"   {len(texts)} sources fetched")

    print("3) Extracting + quote-validating facts (serialized)...")
    facts = []
    for n, (url, content) in enumerate(texts.items(), 1):
        fl = extract_facts(topic, url, content, section_keys)
        facts.extend(fl)
        print(f"   [{n}/{len(texts)}] {len(fl):>2} facts  {url[:60]}")
    for i, f in enumerate(facts):
        f["id"] = i
    facts_by_id = {f["id"]: f for f in facts}
    by_section = defaultdict(list)
    for f in facts:
        by_section[f["section"]].append(f)
    print(f"   {len(facts)} validated facts")

    def pooled_facts(key):
        prim = list(by_section.get(key, []))
        if len(prim) >= 10:
            return prim
        seen = {f["id"] for f in prim}
        out = list(prim)
        for b in sorted((k for k in by_section if k != key), key=lambda k: -len(by_section[k])):
            for f in by_section[b]:
                if f["id"] not in seen:
                    seen.add(f["id"])
                    out.append(f)
            if len(out) >= 16:
                break
        return out

    print("4) Writing sections from facts...")
    written = {}
    for key, title in sections:
        written[key] = write_section(topic, title, pooled_facts(key))
        print(f"   wrote {key} ({len(written[key].split())} words pre-verify)")

    print("5) Verifying every sentence; dropping unsupported/uncited...")
    ref_no = {}
    def ref(url):
        if url not in ref_no:
            ref_no[url] = len(ref_no) + 1
        return ref_no[url]

    body_parts, kept = [], 0
    for key, title in sections:
        if not written.get(key):
            continue
        lines = []
        for item in process_section(written[key], facts_by_id):
            if isinstance(item, str):
                lines.append(item)
            else:
                bullet, clean, ids = item
                urls_c = []
                for j in ids:
                    if j in facts_by_id and facts_by_id[j]["url"] not in urls_c:
                        urls_c.append(facts_by_id[j]["url"])
                cites = ", ".join(f"[{ref(u)}]({u})" for u in urls_c)
                lines.append(f"{bullet}{clean} ({cites})")
                kept += 1
        body_parts.append("\n".join(lines))
    print(f"   kept {kept} grounded sentences")

    refs = "\n".join(f"{n}. [{u}]({u})" for u, n in sorted(ref_no.items(), key=lambda x: x[1]))
    note = ("_Every statement in this report is cited to a source that was fetched and "
            "quote-checked; sentences that could not be grounded were removed._\n")
    report = (f"# {topic}: A Source-Grounded Research Report\n\n{note}\n"
              + "\n\n".join(body_parts) + "\n\n---\n\n## References\n\n" + refs + "\n")

    slug = (re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:40]) or "report"
    out_md = os.path.join(config.OUTPUT_DIR, f"report_{slug}.md")
    with open(out_md, "w") as f:
        f.write(report)
    words = len(report.split())
    print(f"\n✅ Report: {out_md}  ({words:,} words, {len(ref_no)} sources cited)")

    out_pdf = None
    if make_pdf:
        print("6) Rendering PDF...")
        out_pdf = os.path.join(config.OUTPUT_DIR, f"report_{slug}.pdf")
        pdf.render(out_md, out_pdf)
        print(f"✅ PDF: {out_pdf}")

    return {"markdown": out_md, "pdf": out_pdf, "words": words,
            "facts": len(facts), "sentences": kept, "sources": len(ref_no)}
