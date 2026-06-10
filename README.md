# Deep Research Agent — a Claude Code agent that doesn't hallucinate

A Claude Code plugin that researches **any subject** (a company, person, product, place,
or event) and writes an **in-depth, fully-cited report** where **every sentence is backed
by a quote that was verified to literally exist in a real source**. It produces a Markdown
report and a formatted PDF (roomy spacing, clickable links, page-numbered table of
contents).

The only keys it needs are for the web tools it uses to read the internet — **Serper**
(search) and **Firecrawl** (scraping). No Anthropic API key is required.

## How it works — "extract, then write"

Most research tools scrape some pages, stuff them into a prompt, and let the model
free-write a long report. When pushed for length, the model invents plausible-sounding
detail. This agent inverts that:

1. **Search** the web with Serper.
2. **Scrape** the top sources with Firecrawl.
3. **Extract** atomic facts, each stored as *(fact, verbatim quote, source URL)*.
4. **Validate** — a script checks that each quote *literally appears* in its source;
   anything that doesn't is discarded. (This is what makes hallucination impossible.)
5. **Write** each section using *only* the validated facts, citing every sentence.
6. **Verify** — every sentence is re-checked against its fact; unsupported or uncited
   sentences are deleted.
7. **Render** a styled PDF.

Depth follows the evidence: the report is as long as the validated facts honestly
support, and is never padded.

## Install

```
/plugin marketplace add MartinaBeg/deep-research-agent
/plugin install deep-research-agent
```
(or clone this repo and add it as a local plugin).

Then install the Python dependencies and set your web-tool keys:

```
pip install -r requirements.txt
cp .env.example .env      # then fill in SERPER_API_KEY and FIRECRAWL_API_KEY
```

- Get a **Serper** key at https://serper.dev
- Get a **Firecrawl** key at https://firecrawl.dev

## Use

Just ask Claude Code:

> Use the Deep Research Agent to write a report on **\<your topic\>**.

It will plan the sections, gather and verify sources, and produce
`research-<topic>/report.md` and `research-<topic>/report.pdf`.

## What's in the box

| Path | What it is |
|---|---|
| `agents/deep-research-agent.md` | The agent — the grounded extract-then-write methodology Claude Code follows |
| `scripts/search.py` | Serper web search → list of URLs |
| `scripts/scrape.py` | Firecrawl scraping → saved source text (cached) |
| `scripts/check_quotes.py` | Deterministic grounding gate: keeps only facts whose quote is real |
| `scripts/to_pdf.py` | Markdown → styled PDF (spacing, links, page-numbered TOC) |

## Notes

- The deterministic steps (search, scrape, quote-check, PDF) are plain Python and use no
  LLM. The reasoning steps (extract, write, verify) are performed by Claude Code itself.
- PDFs use a system Unicode font if available (set `REPORT_FONT` to a `.ttf` for best
  results); otherwise they fall back to a built-in font.
- Firecrawl can't scrape every site (some block scrapers); those sources are simply
  skipped, and the report stays grounded in what was actually fetched.

## License

MIT © 2026 Martina Beg
