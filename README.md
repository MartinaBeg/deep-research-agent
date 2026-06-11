# Deep Research Agent

A research agent that writes an **in-depth, fully-cited report** on any subject (a company,
person, product, place, or event) where **every sentence is backed by a quote verified to
literally exist in a real source**. It outputs a Markdown report and a formatted PDF.

It reads the web with **Serper** (search) and **Firecrawl** (scraping), and is driven by
your coding-agent tool (Claude Code, Codex, Cursor, …).

## How it works — "extract, then write"

Use it whenever research needs to be trusted, not just read — company due diligence, a
journalist's background file, competitive or investor research, a briefing memo. Its
advantage is traceability: every sentence is tied to a specific quote from a real source,
and anything that can't be is dropped — so the report arrives already fact-checked and
auditable line by line, rather than as a fluent draft you still have to verify.

It achieves this by extracting facts *before* it writes:

1. **Plan** sections for the subject.
2. **Search** (Serper) and **scrape** (Firecrawl) the sources.
3. **Extract** atomic facts, each as *(fact, verbatim quote, source URL)*.
4. **Validate** — `scripts/check_quotes.py` keeps only facts whose quote *literally
   appears* in its source. (This is what makes hallucination impossible.)
5. **Write** each section from validated facts, citing every sentence.
6. **Verify** — delete any sentence not supported by its fact, or with no citation.
7. **Render** a styled PDF.

Depth follows the evidence — the report is never padded.

## Use it

1. Clone the repo and install the script dependencies:
   ```bash
   git clone https://github.com/MartinaBeg/deep-research-agent.git
   cd deep-research-agent
   pip install -r requirements.txt
   cp .env.example .env        # fill in SERPER_API_KEY and FIRECRAWL_API_KEY
   ```
2. Open the folder in your agent tool and ask it to research something:
   > Research **Sydney Sweeney** using the deep research agent.

   It follows the procedure in `AGENTS.md` (Claude Code reads `CLAUDE.md` → `AGENTS.md`),
   runs the scripts, and produces `research-<topic>/report.md` and `report.pdf`.

## What's in the box

| Path | What it is |
|---|---|
| `AGENTS.md` | The agent — the grounded procedure to follow |
| `CLAUDE.md` | Points Claude Code at `AGENTS.md` |
| `scripts/search.py` | Serper web search → URLs |
| `scripts/scrape.py` | Firecrawl scraping → saved source text (cached) |
| `scripts/check_quotes.py` | Grounding gate: keeps only facts whose quote is real |
| `scripts/to_pdf.py` | Markdown → styled PDF (spacing, links, page-numbered TOC) |

## Notes

- The scripts are plain Python; the reasoning (extract, write, verify) is done by your
  agent tool's model.
- The grounding gate runs regardless of which model reasons, so even a smaller model
  can't hallucinate — it just writes a little less elegantly.
- Firecrawl can't scrape every site (some block scrapers); those are skipped and the
  report stays grounded in what was actually fetched.

## License

MIT © 2026 Martina Beg
