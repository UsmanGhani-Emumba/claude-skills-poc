"""
Instrumented Multi-Provider Sub-Agent with Arize Phoenix Tracing.

Used by ALL skills (.gemini and .claude) to run instrumented sub-agents
with full observability metrics for both Anthropic and Google Gemini.

Metrics captured:
  - Input/Output tokens
  - Context used (total input tokens across all API calls)
  - Cost (USD, approximate)
  - Latency (seconds)
  - Distinct tools used
  - API calls made

Usage:
  # Auto-detects provider based on task/env
  python scripts/arize_agent.py --task-file .gemini/logs/tasks/1b.txt --tools web_fetch

  # Explicit provider
  python scripts/arize_agent.py --provider gemini --task "Research AI" --model gemini-3-flash-preview
  python scripts/arize_agent.py --provider anthropic --task "Research AI" --model claude-3-5-sonnet-latest
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Providers
import anthropic
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


# ─── Tracing Setup ───────────────────────────────────────────────────────────


def setup_tracing(provider="anthropic"):
    """Initialize Arize Phoenix tracing if available."""
    try:
        from phoenix.otel import register
        
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

        if provider == "anthropic":
            from openinference.instrumentation.anthropic import AnthropicInstrumentor
            AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
        elif provider == "gemini":
            from openinference.instrumentation.google_generativeai import GoogleGenerativeAIInstrumentor
            GoogleGenerativeAIInstrumentor().instrument(tracer_provider=tracer_provider)
            
        return True
    except ImportError:
        # Silently skip if openinference/phoenix not installed or incompatible (like on Python 3.14)
        return False
    except Exception as e:
        print(f"[WARN] Tracing setup failed: {e}", file=sys.stderr)
        return False


# ─── Tool Definitions (Shared) ───────────────────────────────────────────────

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
    # Placeholder for Gemini if NOT using Google Search grounding
    # For Anthropic, we use the server-side tool if available.
    return f"Web search for '{query}' is being performed. (Manual search logic placeholder)"


# Anthropic tool schemas
ANTHROPIC_SERVER_TOOLS = {
    "web_search": {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
    },
}

ANTHROPIC_CUSTOM_TOOLS = {
    "web_fetch": {
        "name": "web_fetch",
        "description": "Fetch and extract the main text content from a URL. Use this to read documentation pages, articles, blog posts, or any web content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The full URL to fetch content from"},
            },
            "required": ["url"],
        },
    },
    "github_cli": {
        "name": "github_cli",
        "description": "Run GitHub CLI (gh) commands to get repository data, issues, PRs, contributor stats, and other GitHub information. The 'gh' prefix is added automatically — just provide the subcommand.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The gh CLI command without the 'gh' prefix."},
            },
            "required": ["command"],
        },
    },
}

# Gemini tool functions
GEMINI_TOOLS = [web_fetch, github_cli, web_search]


# ─── Pricing ─────────────────────────────────────────────────────────────────

PRICING = {
    "anthropic": {
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-latest": {"input": 0.25, "output": 1.25},
        "claude-3-opus-latest": {"input": 15.0, "output": 75.0},
    },
    "gemini": {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-3-flash-preview": {"input": 0.10, "output": 0.40}, # estimate
    }
}

# Model context window sizes (max input tokens)
CONTEXT_LIMITS = {
    "anthropic": {
        "claude-sonnet-4-5-20250929": 200_000,
        "claude-3-5-sonnet-latest": 200_000,
        "claude-3-5-haiku-latest": 200_000,
        "claude-3-opus-latest": 200_000,
    },
    "gemini": {
        "gemini-1.5-flash": 1_000_000,
        "gemini-1.5-pro": 2_000_000,
        "gemini-2.0-flash": 1_000_000,
        "gemini-3-flash-preview": 1_000_000,
    }
}

def get_context_limit(provider, model):
    """Get the max context window for a model."""
    provider_limits = CONTEXT_LIMITS.get(provider, CONTEXT_LIMITS["anthropic"])
    return provider_limits.get(model, 200_000)

def calculate_cost(provider, model, input_tokens, output_tokens):
    """Calculate approximate cost in USD."""
    provider_pricing = PRICING.get(provider, PRICING["anthropic"])
    pricing = provider_pricing.get(model, next(iter(provider_pricing.values())))
    
    # Simple fuzzy match for Gemini version names
    if provider == "gemini" and model not in provider_pricing:
        if "flash" in model.lower(): pricing = provider_pricing["gemini-1.5-flash"]
        elif "pro" in model.lower(): pricing = provider_pricing["gemini-1.5-pro"]

    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


# ─── Provider Implementations ────────────────────────────────────────────────

def run_anthropic(task, tools, model, skill_name, agent_id, max_tokens):
    client = anthropic.Anthropic()
    api_tools = []
    for t in tools:
        if t in ANTHROPIC_SERVER_TOOLS: api_tools.append(ANTHROPIC_SERVER_TOOLS[t])
        elif t in ANTHROPIC_CUSTOM_TOOLS: api_tools.append(ANTHROPIC_CUSTOM_TOOLS[t])

    messages = [{"role": "user", "content": task}]
    metrics = {"input_tokens": 0, "output_tokens": 0, "api_calls": 0, "tools_used": set(), "context_tokens_peak": 0}

    for _ in range(25):
        kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if api_tools: kwargs["tools"] = api_tools

        response = client.messages.create(**kwargs)
        metrics["api_calls"] += 1
        metrics["input_tokens"] += response.usage.input_tokens
        metrics["output_tokens"] += response.usage.output_tokens
        # Track peak context: the highest input_tokens in any single API call
        metrics["context_tokens_peak"] = max(metrics["context_tokens_peak"], response.usage.input_tokens)
        
        for block in response.content:
            if getattr(block, "type", "") in ("tool_use", "server_tool_use"):
                metrics["tools_used"].add(block.name)
        
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    # Execute custom tool
                    if block.name == "web_fetch": res = web_fetch(**block.input)
                    elif block.name == "github_cli": res = github_cli(**block.input)
                    else: res = f"Unknown tool: {block.name}"
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(res)})
            
            if tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else: break
        else: break

    text = "\n".join([b.text for b in response.content if hasattr(b, "text") and b.text is not None])
    return text, metrics


def run_gemini(task, tool_names, model_name, skill_name, agent_id, max_tokens):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: raise ValueError("GOOGLE_API_KEY not set")
    genai.configure(api_key=api_key)
    
    # Filter tools
    active_tools = []
    for name in tool_names:
        for t in GEMINI_TOOLS:
            if t.__name__ == name: active_tools.append(t)
            
    model = genai.GenerativeModel(model_name=model_name, tools=active_tools if active_tools else None)
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    response = chat.send_message(task)
    
    metrics = {"input_tokens": 0, "output_tokens": 0, "api_calls": 1, "tools_used": set(), "context_tokens_peak": 0}
    if hasattr(response, "usage_metadata"):
        metrics["input_tokens"] = response.usage_metadata.prompt_token_count
        metrics["output_tokens"] = response.usage_metadata.candidates_token_count
        # For Gemini with auto function calling, peak = total (single send_message call)
        metrics["context_tokens_peak"] = response.usage_metadata.prompt_token_count
    
    for message in chat.history:
        if message.role == "model":
            for part in message.parts:
                if part.function_call: metrics["tools_used"].add(part.function_call.name)

    return response.text, metrics


# ─── Local Metrics Logging ───────────────────────────────────────────────────

def log_metrics_locally(metrics, provider):
    """Log metrics to the appropriate directory based on provider."""
    log_dir = ".gemini/logs" if provider == "gemini" else ".claude/logs"
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / "arize_metrics.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics) + "\n")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified Instrumented Sub-Agent (Anthropic/Gemini)")
    parser.add_argument("--provider", help="Provider: anthropic or gemini (auto-detected if omitted)")
    parser.add_argument("--task", help="Task prompt")
    parser.add_argument("--task-file", help="Path to task prompt file")
    parser.add_argument("--tools", default="web_search,web_fetch", help="Comma-separated tools")
    parser.add_argument("--model", help="Model ID")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max tokens")
    parser.add_argument("--skill", default="researcher", help="Skill name")
    parser.add_argument("--agent-id", default="unknown", help="Agent identifier")
    args = parser.parse_args()

    # Resolve task
    task = args.task
    task_source = args.task_file or ""
    if not task and args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    if not task:
        print("Error: No task provided.", file=sys.stderr)
        sys.exit(1)

    # Dynamic Provider Detection
    provider = args.provider
    if not provider:
        if ".gemini" in task_source or "GOOGLE_API_KEY" in os.environ and "ANTHROPIC_API_KEY" not in os.environ:
            provider = "gemini"
        else:
            provider = "anthropic"

    # Default Models
    model = args.model
    if not model:
        model = "gemini-3-flash-preview" if provider == "gemini" else "claude-sonnet-4-5-20250929"

    # Setup Tracing
    setup_tracing(provider)

    # Run Agent
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    start_time = time.time()
    
    try:
        if provider == "gemini":
            result, p_metrics = run_gemini(task, tools, model, args.skill, args.agent_id, args.max_tokens)
        else:
            result, p_metrics = run_anthropic(task, tools, model, args.skill, args.agent_id, args.max_tokens)
        
        # Finalize metrics
        metrics = {
            "agent_id": args.agent_id,
            "skill": args.skill,
            "provider": provider,
            "model": model,
            "latency_seconds": round(time.time() - start_time, 2),
            "cost_usd": calculate_cost(provider, model, p_metrics["input_tokens"], p_metrics["output_tokens"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **p_metrics
        }
        metrics["tools_used"] = sorted(metrics["tools_used"])
        metrics["tool_calls_count"] = len(metrics["tools_used"])
        # Context metrics
        context_limit = get_context_limit(provider, model)
        metrics["context_tokens_total"] = metrics["input_tokens"]  # sum across all API calls
        # context_tokens_peak already set per-call in run_anthropic/run_gemini
        metrics["context_limit"] = context_limit
        metrics["context_utilization"] = round((metrics["context_tokens_peak"] / context_limit) * 100, 2)
        
    except Exception as e:
        metrics = {"agent_id": args.agent_id, "skill": args.skill, "provider": provider, "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
        result = f"Agent error: {e}"

    log_metrics_locally(metrics, provider)
    print(json.dumps({"result": result, "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
