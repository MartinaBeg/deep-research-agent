# Deep Research Agent

A standalone command-line agent that researches **any subject** (a company, person,
product, place, or event) and writes an **in-depth, fully-cited report** where **every
sentence is backed by a quote verified to literally exist in a real source**. It outputs
a Markdown report and a formatted PDF (roomy spacing, clickable links, page-numbered
table of contents).

It runs **anywhere** — a terminal, a server, CI, Docker — like any Python program.

## How it works — "extract, then write"

Most research tools scrape some pages, stuff them into a prompt, and let the model
free-write a long report. When pushed for length, the model invents plausible-sounding
detail. This agent inverts that:

1. **Plan** sections appropriate to the subject.
2. **Search** the web (Serper).
3. **Scrape** the top sources (Firecrawl).
4. **Extract** atomic facts, each stored as *(fact, verbatim quote, source URL)*.
5. **Validate** — every quote is checked to *literally appear* in its source; anything
   that doesn't is discarded. (This is what makes hallucination impossible.)
6. **Write** each section using *only* validated facts, citing every sentence.
7. **Verify** — each sentence is re-checked against its fact; unsupported or uncited
   sentences are deleted.
8. **Render** a styled PDF.

Depth follows the evidence: the report is as long as the validated facts honestly
support, and is never padded.

## Install

```bash
git clone https://github.com/MartinaBeg/deep-research-agent.git
cd deep-research-agent
python3.11 -m venv .venv && source .venv/bin/activate
pip install .
cp .env.example .env
```

## Configure

**Web tools** (always needed) — set in `.env`:

| Key | What for | Get one at |
|---|---|---|
| `SERPER_API_KEY` | web search | https://serper.dev |
| `FIRECRAWL_API_KEY` | web scraping | https://firecrawl.dev |

**The brain** (reasoning) — by default the agent uses a **free local model** via
[Ollama](https://ollama.com), so it needs **no LLM API key and no credits**:

```bash
# install Ollama from https://ollama.com, then:
ollama pull qwen2.5:7b
```

That's it — `LLM_PROVIDER=ollama` is the default. Prefer a cloud model? Set
`LLM_PROVIDER=anthropic` (with `ANTHROPIC_API_KEY`) or `LLM_PROVIDER=openai`
(with `OPENAI_API_KEY`; also works with Groq via `OPENAI_BASE_URL`). The grounding
gate keeps every model honest, so the local model can't hallucinate either.

## Run

```bash
deep-research "Sydney Sweeney"
# or, equivalently:
python -m deep_research "Abaka AI (abaka.ai), a data company"
```

Output is written to `reports/report_<slug>.md` and `reports/report_<slug>.pdf`.
Add `--no-pdf` for Markdown only.

### Docker

```bash
docker build -t deep-research-agent .
docker run --rm --env-file .env -v "$PWD/reports:/app/reports" \
  deep-research-agent "Sydney Sweeney"
```

## Project layout

| Path | What it is |
|---|---|
| `src/deep_research/pipeline.py` | The grounded extract-then-write pipeline (orchestration) |
| `src/deep_research/web.py` | Serper search + Firecrawl scraping (cached) |
| `src/deep_research/llm.py` | LLM wrapper (Claude) with rate-limit back-off |
| `src/deep_research/pdf.py` | Markdown → styled PDF (spacing, links, page-numbered TOC) |
| `src/deep_research/config.py` | Settings from `.env` |
| `src/deep_research/__main__.py` | CLI entry point |

## Notes

- The deterministic steps (search, scrape, quote-check, PDF) use no LLM. The reasoning
  steps (extract, write, verify) call whichever model `LLM_PROVIDER` selects (a free local
  Ollama model by default).
- Firecrawl can't scrape every site (some block scrapers); those sources are skipped and
  the report stays grounded in what was actually fetched.
- PDFs use a system Unicode font if available (set `REPORT_FONT` to a `.ttf` for best
  results); otherwise they fall back to a built-in font.

## License

MIT © 2026 Martina Beg
