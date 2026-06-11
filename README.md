# Deep Research Agent

A research agent that writes an **in-depth, fully-cited report** on any subject (a company,
person, product, place, or event) where **every sentence is backed by a quote verified to
literally exist in a real source**. It outputs a Markdown report and a formatted PDF (roomy
spacing, clickable links, page-numbered table of contents).

**It runs inside your coding-agent tool** — Claude Code, Codex, Cursor, and others — and
uses **that tool's own model** to do the reasoning. So there's **no LLM API key and no
credits**: the host already has a brain. The only keys it needs are for reading the web:
**Serper** (search) and **Firecrawl** (scraping).

## How it works — "extract, then write"

Most research tools scrape some pages, stuff them into a prompt, and let the model
free-write — which invents detail when pushed for length. This agent inverts that:

1. **Plan** sections for the subject.
2. **Search** (Serper) and **scrape** (Firecrawl) the sources.
3. **Extract** atomic facts, each as *(fact, verbatim quote, source URL)*.
4. **Validate** — `scripts/check_quotes.py` keeps only facts whose quote *literally
   appears* in its source. (This is what makes hallucination impossible.)
5. **Write** each section from validated facts, citing every sentence.
6. **Verify** — delete any sentence not supported by its fact, or with no citation.
7. **Render** a styled PDF.

The reasoning steps are done by your tool's model; the mechanical steps are plain Python
scripts (no model). Depth follows the evidence — the report is never padded.

## Use it (any agent tool)

1. Clone the repo and install the script dependencies:
   ```bash
   git clone https://github.com/MartinaBeg/deep-research-agent.git
   cd deep-research-agent
   pip install -r requirements.txt
   cp .env.example .env        # fill in SERPER_API_KEY and FIRECRAWL_API_KEY
   ```
2. Open the folder in your agent tool and ask it to research something:
   > Research **Sydney Sweeney** using the deep research agent.

   - **Claude Code** reads `CLAUDE.md` → `AGENTS.md`.
   - **Codex / Cursor / others** read `AGENTS.md` directly.

   The tool follows the procedure, runs the scripts, and produces
   `research-<topic>/report.md` and `research-<topic>/report.pdf`.

No model API key is required — your agent tool's own model does the thinking.

## What's in the box

| Path | What it is |
|---|---|
| `AGENTS.md` | The agent — the grounded procedure your tool's model follows |
| `CLAUDE.md` | Points Claude Code at `AGENTS.md` |
| `scripts/search.py` | Serper web search → URLs |
| `scripts/scrape.py` | Firecrawl scraping → saved source text (cached) |
| `scripts/check_quotes.py` | Grounding gate: keeps only facts whose quote is real |
| `scripts/to_pdf.py` | Markdown → styled PDF (spacing, links, page-numbered TOC) |

## Notes

- The scripts use no model. The reasoning is your agent tool's own model — so the agent
  is portable across tools and needs no LLM credits.
- The grounding gate runs regardless of which model reasons, so even a smaller model
  can't hallucinate — it just writes a little less elegantly.
- Firecrawl can't scrape every site (some block scrapers); those are skipped and the
  report stays grounded in what was actually fetched.

## License

MIT © 2026 Martina Beg
