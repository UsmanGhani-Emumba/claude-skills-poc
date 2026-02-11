"""
Instrumented Gemini Sub-Agent with Arize Phoenix Tracing.

Used by ALL Gemini skills (.gemini) to run instrumented sub-agents
with full observability metrics for Google Gemini models.

Metrics captured:
  - Input/Output tokens
  - Context used (peak and total input tokens across all API calls)
  - Cost (USD, approximate)
  - Latency (seconds)
  - Distinct tools used
  - API calls made

Usage:
  python scripts/gemini_agent.py --task "Research AI diagnostics" --tools web_search --agent-id 1a --skill researcher
  python scripts/gemini_agent.py --task-file .gemini/logs/tasks/1b.txt --tools web_fetch
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


# ─── Tracing Setup ───────────────────────────────────────────────────────────


def setup_tracing():
    """Initialize Arize Phoenix tracing for Gemini if available."""
    try:
        from phoenix.otel import register

        arize_api_key = os.getenv("ARIZE_API_KEY", "")
        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "https://app.phoenix.arize.com/v1/traces",
        )
        project_name = os.getenv("ARIZE_PROJECT_NAME", "gemini-skills")

        headers = {}
        if arize_api_key:
            headers["api_key"] = arize_api_key

        tracer_provider = register(
            project_name=project_name,
            endpoint=endpoint,
            headers=headers if headers else None,
        )

        from openinference.instrumentation.google_generativeai import GoogleGenerativeAIInstrumentor
        GoogleGenerativeAIInstrumentor().instrument(tracer_provider=tracer_provider)

        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[WARN] Tracing setup failed: {e}", file=sys.stderr)
        return False


# ─── Tool Definitions ────────────────────────────────────────────────────────

def web_fetch(url: str):
    """
    Fetch and extract the main text content from a URL.
    Use this to read documentation pages, articles, blog posts, or any web content.
    """
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        if len(text) > 8000:
            text = text[:8000] + "\n\n[... content truncated at 8000 chars ...]"
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

def github_cli(command: str):
    """
    Run GitHub CLI (gh) commands to get repository data, issues, PRs,
    contributor stats, and other GitHub information.
    The 'gh' prefix is added automatically — just provide the subcommand.
    Example: 'api repos/facebook/react --jq .stargazers_count'
    """
    try:
        result = subprocess.run(
            f"gh {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout or result.stderr or "No output"
        return output[:5000]
    except subprocess.TimeoutExpired:
        return f"Command timed out: gh {command}"
    except Exception as e:
        return f"Error running gh {command}: {e}"

def web_search(query: str):
    """
    Search the web for a given query.
    Returns a list of search results with titles and URLs.
    """
    return f"Web search for '{query}' is not available in Gemini agent yet. Please use specific URLs with web_fetch."

# Map tool names to functions
TOOL_FUNCTIONS = {
    "web_fetch": web_fetch,
    "github_cli": github_cli,
    "web_search": web_search,
}


# ─── Pricing ─────────────────────────────────────────────────────────────────

PRICING = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-3-flash-preview": {"input": 0.10, "output": 0.40},
}

# Model context window sizes (max input tokens)
CONTEXT_LIMITS = {
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-2.0-flash": 1_000_000,
    "gemini-3-flash-preview": 1_000_000,
}

def get_context_limit(model):
    """Get the max context window for a model."""
    return CONTEXT_LIMITS.get(model, 1_000_000)

def calculate_cost(model, input_tokens, output_tokens):
    """Calculate approximate cost in USD."""
    pricing = PRICING.get(model, PRICING["gemini-1.5-flash"])
    # Simple fuzzy match for version names
    if model not in PRICING:
        if "flash" in model.lower(): pricing = PRICING["gemini-1.5-flash"]
        elif "pro" in model.lower(): pricing = PRICING["gemini-1.5-pro"]

    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


# ─── Agent Loop ──────────────────────────────────────────────────────────────

def run_gemini(task, tool_names, model_name, skill_name, agent_id, max_tokens=4096):
    """Run an instrumented Gemini agent with the specified tools. Returns result + metrics."""

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    genai.configure(api_key=api_key)

    # Select tools
    tools = []
    for name in tool_names:
        if name in TOOL_FUNCTIONS:
            tools.append(TOOL_FUNCTIONS[name])

    model = genai.GenerativeModel(
        model_name=model_name,
        tools=tools if tools else None
    )

    chat = model.start_chat(enable_automatic_function_calling=True)

    metrics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "api_calls": 0,
        "tools_used": set(),
        "context_tokens_peak": 0,
    }

    response = chat.send_message(task)
    metrics["api_calls"] += 1

    if hasattr(response, "usage_metadata"):
        metrics["input_tokens"] = response.usage_metadata.prompt_token_count
        metrics["output_tokens"] = response.usage_metadata.candidates_token_count
        # For Gemini with auto function calling, peak = total (single send_message call)
        metrics["context_tokens_peak"] = response.usage_metadata.prompt_token_count

    # Inspect history to find tool calls
    for message in chat.history:
        if message.role == "model":
            for part in message.parts:
                if part.function_call:
                    metrics["tools_used"].add(part.function_call.name)

    return response.text, metrics


# ─── Local Metrics Logging ───────────────────────────────────────────────────

def log_metrics_locally(metrics):
    """Log metrics to .gemini/logs directory."""
    log_path = Path(".gemini/logs")
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / "arize_metrics.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics) + "\n")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instrumented Gemini Sub-Agent")
    parser.add_argument("--task", help="Task prompt")
    parser.add_argument("--task-file", help="Path to task prompt file")
    parser.add_argument("--tools", default="web_search,web_fetch", help="Comma-separated tools")
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Model ID")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max tokens")
    parser.add_argument("--skill", default="researcher", help="Skill name")
    parser.add_argument("--agent-id", default="unknown", help="Agent identifier")
    args = parser.parse_args()

    # Resolve task
    task = args.task
    if not task and args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    if not task:
        print("Error: No task provided.", file=sys.stderr)
        sys.exit(1)

    # Setup Tracing
    setup_tracing()

    # Run Agent
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    start_time = time.time()

    try:
        result, p_metrics = run_gemini(task, tools, args.model, args.skill, args.agent_id, args.max_tokens)

        # Finalize metrics
        context_limit = get_context_limit(args.model)
        metrics = {
            "agent_id": args.agent_id,
            "skill": args.skill,
            "provider": "gemini",
            "model": args.model,
            "latency_seconds": round(time.time() - start_time, 2),
            "cost_usd": calculate_cost(args.model, p_metrics["input_tokens"], p_metrics["output_tokens"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **p_metrics
        }
        metrics["tools_used"] = sorted(metrics["tools_used"])
        metrics["tool_calls_count"] = len(metrics["tools_used"])
        metrics["context_tokens_total"] = metrics["input_tokens"]
        metrics["context_limit"] = context_limit
        metrics["context_utilization"] = round((metrics["context_tokens_peak"] / context_limit) * 100, 2)

    except Exception as e:
        metrics = {"agent_id": args.agent_id, "skill": args.skill, "provider": "gemini", "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
        result = f"Agent error: {e}"

    log_metrics_locally(metrics)
    print(json.dumps({"result": result, "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
