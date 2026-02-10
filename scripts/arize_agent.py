"""
Instrumented Anthropic Sub-Agent with Arize Phoenix Tracing.

Used by ALL Claude Code skills to run instrumented sub-agents
with full observability metrics.

Metrics captured:
  - Input/Output tokens
  - Context used (total input tokens across all API calls)
  - Cost (USD, approximate)
  - Latency (seconds)
  - Distinct tools used
  - API calls made

Tracing levels:
  1. Arize Cloud  — if ARIZE_API_KEY is set, sends traces to Arize Phoenix cloud
  2. Local Phoenix — if phoenix installed but no ARIZE_API_KEY, sends to local Phoenix
  3. Local file    — always logs metrics to .claude/logs/arize_metrics.jsonl

Usage:
  # Researcher sub-agents (with tools)
  python scripts/arize_agent.py --task "Research AI diagnostics" --tools web_search --agent-id 1a --skill researcher
  python scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_fetch --agent-id 1b --skill researcher

  # Writer / Reviewer / Publisher (no tools, pure LLM generation)
  python scripts/arize_agent.py --task-file .claude/logs/tasks/writer.txt --tools none --skill writer --agent-id writer-1
  python scripts/arize_agent.py --task-file .claude/logs/tasks/reviewer.txt --tools none --skill reviewer --agent-id reviewer-1
  python scripts/arize_agent.py --task-file .claude/logs/tasks/publisher.txt --tools none --skill publisher --agent-id publisher-1 --max-tokens 8192
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


# ─── Tracing Setup ───────────────────────────────────────────────────────────


def setup_tracing():
    """Initialize Arize Phoenix tracing if available."""
    try:
        from phoenix.otel import register
        from openinference.instrumentation.anthropic import AnthropicInstrumentor

        arize_api_key = os.getenv("ARIZE_API_KEY", "")
        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "https://app.phoenix.arize.com/v1/traces",
        )
        project_name = os.getenv("ARIZE_PROJECT_NAME", "claude-skills")

        headers = {}
        if arize_api_key:
            headers["api_key"] = arize_api_key

        tracer_provider = register(
            project_name=project_name,
            endpoint=endpoint,
            headers=headers if headers else None,
        )

        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
        return True
    except ImportError:
        print(
            "[WARN] phoenix/openinference not installed — metrics logged locally only.",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(f"[WARN] Tracing setup failed: {e} — metrics logged locally only.", file=sys.stderr)
        return False


# ─── Tool Definitions ────────────────────────────────────────────────────────

# Server-side tools (executed by Anthropic API, no client-side handling needed)
SERVER_TOOLS = {
    "web_search": {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
    },
}

# Custom tools (executed client-side in the tool loop)
CUSTOM_TOOLS = {
    "web_fetch": {
        "name": "web_fetch",
        "description": (
            "Fetch and extract the main text content from a URL. "
            "Use this to read documentation pages, articles, blog posts, or any web content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch content from",
                },
            },
            "required": ["url"],
        },
    },
    "github_cli": {
        "name": "github_cli",
        "description": (
            "Run GitHub CLI (gh) commands to get repository data, issues, PRs, "
            "contributor stats, and other GitHub information. "
            "The 'gh' prefix is added automatically — just provide the subcommand."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "The gh CLI command without the 'gh' prefix. "
                        "Example: 'api repos/facebook/react --jq .stargazers_count'"
                    ),
                },
            },
            "required": ["command"],
        },
    },
}


# ─── Tool Execution ──────────────────────────────────────────────────────────


def execute_tool(tool_name, tool_input):
    """Execute a custom tool and return the result string."""
    executors = {
        "web_fetch": _execute_web_fetch,
        "github_cli": _execute_github_cli,
    }
    executor = executors.get(tool_name)
    if executor:
        return executor(tool_input)
    return f"Unknown tool: {tool_name}"


def _execute_web_fetch(input_data):
    """Fetch a URL and extract readable text content."""
    url = input_data.get("url", "")
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


def _execute_github_cli(input_data):
    """Run a gh CLI command and return output."""
    command = input_data.get("command", "")
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


# ─── Pricing ─────────────────────────────────────────────────────────────────

# Per-million-token pricing (USD) as of early 2025
MODEL_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
}


def calculate_cost(model, input_tokens, output_tokens):
    """Calculate approximate cost in USD."""
    pricing = MODEL_PRICING.get(model, {"input": 3.0, "output": 15.0})
    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


# ─── Agent Loop ──────────────────────────────────────────────────────────────


def run_agent(task, tools, model, skill_name, agent_id, max_tokens=4096):
    """Run an instrumented agent with the specified tools. Returns result + metrics."""
    client = anthropic.Anthropic()

    # Build the tools list for the API (filter out "none" placeholder)
    api_tools = []
    for tool_name in tools:
        if tool_name in ("none", ""):
            continue
        if tool_name in SERVER_TOOLS:
            api_tools.append(SERVER_TOOLS[tool_name])
        elif tool_name in CUSTOM_TOOLS:
            api_tools.append(CUSTOM_TOOLS[tool_name])

    messages = [{"role": "user", "content": task}]

    # ── Metrics accumulator ──
    metrics = {
        "agent_id": agent_id,
        "skill": skill_name,
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "api_calls": 0,
        "tools_used": set(),
        "tool_calls_count": 0,
    }

    start_time = time.time()
    last_response = None
    max_iterations = 25  # safety limit

    for _ in range(max_iterations):
        kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if api_tools:
            kwargs["tools"] = api_tools

        response = client.messages.create(**kwargs)
        last_response = response

        # Accumulate token usage
        metrics["api_calls"] += 1
        metrics["input_tokens"] += response.usage.input_tokens
        metrics["output_tokens"] += response.usage.output_tokens

        # Track which tools appeared in the response
        for block in response.content:
            btype = getattr(block, "type", "")
            if btype in ("tool_use", "server_tool_use"):
                metrics["tools_used"].add(block.name)
                metrics["tool_calls_count"] += 1

        # If the model wants to use a custom tool, execute it and loop
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") == "tool_use" and block.name in CUSTOM_TOOLS:
                    result = execute_tool(block.name, block.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
                    )

            if tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Only server-side tool uses — response is already complete
                break
        else:
            # end_turn or max_tokens — we're done
            break

    # ── Finalize metrics ──
    metrics["latency_seconds"] = round(time.time() - start_time, 2)
    metrics["tools_used"] = sorted(metrics["tools_used"])
    metrics["distinct_tools_count"] = len(metrics["tools_used"])
    metrics["cost_usd"] = calculate_cost(model, metrics["input_tokens"], metrics["output_tokens"])
    metrics["context_tokens"] = metrics["input_tokens"]
    metrics["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Extract the final text response
    text_parts = []
    if last_response:
        for block in last_response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

    return {"result": "\n".join(text_parts), "metrics": metrics}


# ─── Local Metrics Logging ────────────────────────────────────────────────────


def log_metrics_locally(metrics, log_dir=".claude/logs"):
    """Append metrics to a local JSONL file (always runs, independent of Arize)."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "arize_metrics.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics) + "\n")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Instrumented Anthropic sub-agent with Arize Phoenix tracing"
    )
    parser.add_argument("--task", help="Research task prompt (inline)")
    parser.add_argument("--task-file", help="Path to a file containing the task prompt")
    parser.add_argument(
        "--tools",
        default="web_search",
        help="Comma-separated tools: web_search, web_fetch, github_cli",
    )
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929", help="Model ID")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max output tokens (default 4096)")
    parser.add_argument("--skill", default="researcher", help="Skill name (for logging)")
    parser.add_argument("--agent-id", default="unknown", help="Agent identifier (e.g. 1a, 2b)")

    args = parser.parse_args()

    # Resolve the task prompt
    task = args.task
    if not task and args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    if not task and not sys.stdin.isatty():
        task = sys.stdin.read().strip()
    if not task:
        print("Error: provide a task via --task, --task-file, or stdin.", file=sys.stderr)
        sys.exit(1)

    # Setup Arize tracing (best-effort)
    setup_tracing()

    # Parse tool list
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    # Run the agent
    try:
        output = run_agent(
            task=task,
            tools=tools,
            model=args.model,
            skill_name=args.skill,
            agent_id=args.agent_id,
            max_tokens=args.max_tokens,
        )
    except Exception as e:
        output = {
            "result": f"Agent error: {e}",
            "metrics": {
                "agent_id": args.agent_id,
                "skill": args.skill,
                "model": args.model,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        log_metrics_locally(output["metrics"])
        print(json.dumps(output, indent=2))
        sys.exit(1)

    # Log metrics locally (always, regardless of Arize)
    log_metrics_locally(output["metrics"])

    # Output JSON to stdout for Claude Code to consume
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
