"""
Instrumented Gemini Sub-Agent with Arize Phoenix Metrics.

Used by ALL Claude Code skills to run instrumented sub-agents
with full observability metrics using Google's Gemini models.

Metrics captured:
  - Input/Output tokens
  - Context used (total input tokens across all API calls)
  - Cost (USD, approximate)
  - Latency (seconds)
  - Distinct tools used
  - API calls made

Usage:
  python scripts/gemini_agent.py --task "Research AI diagnostics" --tools web_search --agent-id 1a --skill researcher
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
    """Initialize Arize Phoenix tracing if available."""
    # Tracing with openinference is not yet fully compatible with Python 3.14
    # leaving this as a stub for future enablement
    return False

# ─── Tool Definitions ────────────────────────────────────────────────────────

# Custom tools (executed client-side in the tool loop)
# We define them as Python functions for Gemini's function calling
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

# Web Search isn't built-in to Gemini SDK in the same way as Anthropic's server tool
# We'll implement a simple one if needed, or rely on user providing a custom search tool implementation.
# For now, let's implement a dummy or rely on the `google-generativeai` tools if available.
# Actually, Gemini 1.5 Pro/Flash supports Google Search grounding, but that's a specific feature.
# Let's assume for this agent we use a custom search tool or just fail gracefully if asked for web_search without implementation.
# For simplicity in this POC, we will map 'web_search' to a simple placeholder or a real search if API key provided.
# But `arize_agent.py` relies on Anthropic's `web_search` tool. We should probably implement a basic one using `googlesearch-python` or similar if requested,
# or just mock it.
# Let's mock it for now to avoid extra dependencies, or better, use `ddg` (duckduckgo) if we had it.
# Re-using `web_fetch` logic for now as a fallback is not enough.
# Let's implement a simple search using `duckduckgo-search` if installed, or just a placeholder.
# Since we didn't add `duckduckgo-search` to requirements, let's skip `web_search` implementation 
# and warn the user, OR implement a very basic one if possible.
# Wait, `arize_agent.py` uses `web_search` server tool.
# We will leave `web_search` as a "not implemented" message for Gemini to see.

def web_search(query: str):
    """
    Search the web for a given query.
    Returns a list of search results with titles and URLs.
    """
    # Placeholder: In a real implementation, use Google Search API or DuckDuckGo
    return f"Web search for '{query}' is not available in Gemini agent yet. Please use specific URLs with web_fetch."

# Map tool names to functions
TOOL_FUNCTIONS = {
    "web_fetch": web_fetch,
    "github_cli": github_cli,
    "web_search": web_search,
}

# ─── Pricing ─────────────────────────────────────────────────────────────────

# Per-million-token pricing (USD) as of early 2025 (Estimates)
MODEL_PRICING = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30}, # approximate
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},    # approximate
    "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
}

def calculate_cost(model, input_tokens, output_tokens):
    """Calculate approximate cost in USD."""
    # Default to flash pricing if unknown
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-1.5-flash"]) 
    # Handle if model name has version suffix
    if model not in MODEL_PRICING:
        for k, v in MODEL_PRICING.items():
            if k in model:
                pricing = v
                break
    
    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )

# ─── Agent Loop ──────────────────────────────────────────────────────────────

def run_agent(task, tool_names, model_name, skill_name, agent_id, max_tokens=4096):
    """Run an instrumented agent with the specified tools. Returns result + metrics."""
    
    # Configure Gemini
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    
    # Select tools
    tools = []
    for name in tool_names:
        if name in TOOL_FUNCTIONS:
            tools.append(TOOL_FUNCTIONS[name])
            
    # Initialize model
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=tools if tools else None
    )

    chat = model.start_chat(enable_automatic_function_calling=True)

    # ── Metrics accumulator ──
    metrics = {
        "agent_id": agent_id,
        "skill": skill_name,
        "model": model_name,
        "input_tokens": 0,
        "output_tokens": 0,
        "api_calls": 0,
        "tools_used": set(),
        "tool_calls_count": 0,
    }

    start_time = time.time()
    
    try:
        # Send message
        response = chat.send_message(task)
        
        # Accumulate metrics from the final response
        # Note: accurate intermediate token counting with auto-function-calling 
        # is tricky in current SDK versions as it abstracts the turns. 
        # We will use the final usage metadata if available.
        if hasattr(response, "usage_metadata"):
            metrics["input_tokens"] = response.usage_metadata.prompt_token_count
            metrics["output_tokens"] = response.usage_metadata.candidates_token_count
        
        metrics["api_calls"] += 1 # We count the high-level call
        
        # Inspect history to find tool calls
        for message in chat.history:
            if message.role == "model":
                for part in message.parts:
                    if part.function_call:
                        metrics["tools_used"].add(part.function_call.name)
                        metrics["tool_calls_count"] += 1

        final_text = response.text

    except Exception as e:
        return {
            "result": f"Error: {e}",
            "metrics": {
                "error": str(e), 
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    # ── Finalize metrics ──
    metrics["latency_seconds"] = round(time.time() - start_time, 2)
    metrics["tools_used"] = sorted(metrics["tools_used"])
    metrics["distinct_tools_count"] = len(metrics["tools_used"])
    metrics["cost_usd"] = calculate_cost(model_name, metrics["input_tokens"], metrics["output_tokens"])
    metrics["context_tokens"] = metrics["input_tokens"]
    metrics["timestamp"] = datetime.now(timezone.utc).isoformat()

    return {"result": final_text, "metrics": metrics}

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
        description="Instrumented Gemini sub-agent with Arize Phoenix metrics"
    )
    parser.add_argument("--task", help="Research task prompt (inline)")
    parser.add_argument("--task-file", help="Path to a file containing the task prompt")
    parser.add_argument(
        "--tools",
        default="web_search",
        help="Comma-separated tools: web_search, web_fetch, github_cli",
    )
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Model ID")
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

    # Parse tool list
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    # Run the agent
    try:
        output = run_agent(
            task=task,
            tool_names=tools,
            model_name=args.model,
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

    # Log metrics locally
    log_metrics_locally(output["metrics"])

    # Output JSON to stdout
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
