import os
import re
from pathlib import Path

import phoenix as px
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
from phoenix.otel import register

_phoenix_launched = False
_gemini_instrumented = False


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert a topic string into a URL-safe project slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)      # remove non-alphanumeric
    slug = re.sub(r"[\s_]+", "-", slug)        # spaces/underscores → hyphens
    slug = re.sub(r"-{2,}", "-", slug)         # collapse multiple hyphens
    slug = slug.strip("-")
    return slug[:max_length] or "gemini-orchestrator"


def launch_phoenix():
    """Launch Phoenix UI once. Safe to call multiple times."""
    global _phoenix_launched
    if _phoenix_launched:
        return
    phoenix_dir = Path(".phoenix_data")
    phoenix_dir.mkdir(exist_ok=True)
    os.environ.setdefault("PHOENIX_WORKING_DIR", str(phoenix_dir.resolve()))
    px.launch_app()
    _phoenix_launched = True


def setup_observability(project_name: str = "gemini-orchestrator"):
    """Register a tracer provider for the given project and instrument Gemini."""
    global _gemini_instrumented
    launch_phoenix()

    tracer_provider = register(
        project_name=project_name,
        auto_instrument=False,
    )

    if not _gemini_instrumented:
        GoogleGenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        _gemini_instrumented = True

    return tracer_provider
