"""Configuration, loaded from environment / .env.

By default the agent uses a FREE LOCAL model (Ollama) — no API key, no credits.
Set LLM_PROVIDER=anthropic or openai to use a cloud model instead.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Web tools (always required) ---
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# --- Which brain runs the reasoning ---
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower()   # ollama | anthropic | openai

# Ollama (local, free — the default)
OLLAMA_MODEL = os.environ.get("DR_OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_NUM_CTX = int(os.environ.get("DR_OLLAMA_NUM_CTX", "16384"))

# Anthropic (cloud, paid)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_SMART = os.environ.get("DR_SMART_MODEL", "claude-sonnet-4-6")
ANTHROPIC_FAST = os.environ.get("DR_FAST_MODEL", "claude-haiku-4-5-20251001")

# OpenAI-compatible (OpenAI, Groq, or any compatible server)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("DR_OPENAI_MODEL", "gpt-4o-mini")

# --- Tuning ---
MAX_SOURCES = int(os.environ.get("DR_MAX_SOURCES", "55"))
SOURCE_CHARS = int(os.environ.get("DR_SOURCE_CHARS", "24000"))
OUTPUT_DIR = os.environ.get("DR_OUTPUT_DIR", "reports")


def require_keys():
    """Fail early, with a clear message, if something required for this provider is missing."""
    missing = []
    if not SERPER_API_KEY:
        missing.append("SERPER_API_KEY")
    if not FIRECRAWL_API_KEY:
        missing.append("FIRECRAWL_API_KEY")
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise SystemExit(
            "Missing required environment variable(s): " + ", ".join(missing) +
            "\nCopy .env.example to .env and fill them in (see the README)."
        )

    if LLM_PROVIDER == "ollama":
        try:
            requests_get_ok = __import__("requests").get(
                f"{OLLAMA_HOST}/api/tags", timeout=3).ok
        except Exception:
            requests_get_ok = False
        if not requests_get_ok:
            raise SystemExit(
                f"LLM_PROVIDER=ollama but no Ollama server is reachable at {OLLAMA_HOST}.\n"
                "Install Ollama (https://ollama.com), then run:\n"
                f"    ollama pull {OLLAMA_MODEL}\n"
                "Ollama runs the server automatically once installed.\n"
                "(Or set LLM_PROVIDER=anthropic / openai to use a cloud model instead.)"
            )
