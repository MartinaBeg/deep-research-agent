This repository defines a **Deep Research Agent**. When asked to research a subject,
follow the procedure in [AGENTS.md](AGENTS.md) exactly: plan sections, search (Serper),
scrape (Firecrawl), extract facts with verbatim quotes, run `scripts/check_quotes.py` to
keep only facts whose quote literally appears in its source, write each section citing
every sentence, delete any unsupported/uncited sentence, then render the PDF.

You are the brain — do the reasoning with your own model. The scripts in `scripts/` handle
the mechanical steps and use no model. Only `SERPER_API_KEY` and `FIRECRAWL_API_KEY` are
needed (see `.env.example`); no LLM API key is required.
