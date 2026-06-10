"""Configuration, loaded from environment / .env. No decisions required at runtime."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Required service keys ---
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# --- Models (the agent's reasoning). Sensible defaults; override only if you want to. ---
SMART_MODEL = os.environ.get("DR_SMART_MODEL", "claude-sonnet-4-6")        # writing
FAST_MODEL = os.environ.get("DR_FAST_MODEL", "claude-haiku-4-5-20251001")  # extract/verify

# --- Tuning ---
MAX_SOURCES = int(os.environ.get("DR_MAX_SOURCES", "55"))
SOURCE_CHARS = int(os.environ.get("DR_SOURCE_CHARS", "24000"))
OUTPUT_DIR = os.environ.get("DR_OUTPUT_DIR", "reports")


def require_keys():
    """Fail early with a clear message if a required key is missing."""
    missing = [k for k, v in {
        "SERPER_API_KEY": SERPER_API_KEY,
        "FIRECRAWL_API_KEY": FIRECRAWL_API_KEY,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    }.items() if not v]
    if missing:
        raise SystemExit(
            "Missing required environment variable(s): " + ", ".join(missing) +
            "\nCopy .env.example to .env and fill them in (see the README)."
        )
