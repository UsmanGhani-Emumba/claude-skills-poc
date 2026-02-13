import os
import re
from pathlib import Path

import phoenix as px
from openinference.instrumentation.anthropic import AnthropicInstrumentor
from phoenix.otel import register

_phoenix_launched = False
_anthropic_instrumented = False


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert a topic string into a URL-safe project slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)      # remove non-alphanumeric
    slug = re.sub(r"[\s_]+", "-", slug)        # spaces/underscores → hyphens
    slug = re.sub(r"-{2,}", "-", slug)         # collapse multiple hyphens
    slug = slug.strip("-")
    return slug[:max_length] or "orchestrator-agent"


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


def setup_observability(project_name: str = "orchestrator-agent"):
    """Register a tracer provider for the given project and instrument Anthropic."""
    global _anthropic_instrumented
    launch_phoenix()

    tracer_provider = register(
        project_name=project_name,
        auto_instrument=False,
    )

    if not _anthropic_instrumented:
        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
        _anthropic_instrumented = True

    return tracer_provider
