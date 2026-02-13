import os
from pathlib import Path

import phoenix as px
from openinference.instrumentation.anthropic import AnthropicInstrumentor
from phoenix.otel import register


def setup_observability():
    """Initialize Arize Phoenix and auto-instrument the Anthropic SDK."""
    # Use a persistent directory for Phoenix storage instead of temp files.
    # This avoids Windows PermissionError on temp file cleanup at exit.
    phoenix_dir = Path(".phoenix_data")
    phoenix_dir.mkdir(exist_ok=True)
    os.environ.setdefault("PHOENIX_WORKING_DIR", str(phoenix_dir.resolve()))

    # Launch Phoenix locally at http://localhost:6006
    px.launch_app()

    # Register tracer with Phoenix
    tracer_provider = register(
        project_name="orchestrator-agent",
        auto_instrument=False,
    )

    # Auto-instrument all Anthropic API calls
    # This captures: input/output tokens, latency, model name, prompts/completions
    AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)

    return tracer_provider
