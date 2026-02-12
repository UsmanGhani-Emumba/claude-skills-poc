"""
Instrumented Anthropic Sub-Agent with Arize Phoenix Tracing.

Used by ALL Claude skills (.claude) to run instrumented sub-agents
with full observability metrics for Anthropic models.

Supports skill-level session tracking for multi-agent observability:
  - start-session: Begin tracking a skill invocation (returns session_id)
  - run (default): Execute an agent within an optional session
  - end-session: Aggregate and log session-level metrics

Metrics captured:
  - Input/Output tokens
  - Context used (peak and total input tokens across all API calls)
  - Cost (USD, approximate)
  - Latency (seconds)
  - Distinct tools used
  - API calls made
  - Session-level aggregates per skill

Usage:
  # Session-aware workflow:
  python scripts/arize_agent.py --action start-session --skill researcher
  python scripts/arize_agent.py --task-file .claude/logs/tasks/1a.txt --tools web_search --session-id <id> --agent-id 1a --skill researcher
  python scripts/arize_agent.py --action end-session --session-id <session-id>

  # Standalone (backward compatible):
  python scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_fetch
  python scripts/arize_agent.py --task "Research AI" --model claude-sonnet-4-5-20250929
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


# ─── Tracing Setup ───────────────────────────────────────────────────────────


def setup_tracing(project_name=None):
    """Initialize Arize Phoenix tracing for Anthropic if available.

    Args:
        project_name: Arize project name. If None, falls back to
                      ARIZE_PROJECT_NAME env var, then "claude-skills".
    """
    try:
        from phoenix.otel import register

        arize_api_key = os.getenv("ARIZE_API_KEY", "")
        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "https://app.phoenix.arize.com/v1/traces",
        )
        final_project_name = project_name or os.getenv("ARIZE_PROJECT_NAME", "claude-skills")

        headers = {}
        if arize_api_key:
            headers["api_key"] = arize_api_key

        tracer_provider = register(
            project_name=final_project_name,
            endpoint=endpoint,
            headers=headers if headers else None,
        )

        from openinference.instrumentation.anthropic import AnthropicInstrumentor
        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)

        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[WARN] Tracing setup failed: {e}", file=sys.stderr)
        return False


def get_tracer():
    """Get OpenTelemetry tracer for manual span creation. Returns None if unavailable."""
    try:
        from opentelemetry import trace
        return trace.get_tracer("claude-skills-agent")
    except ImportError:
        return None


# ─── Session Management ─────────────────────────────────────────────────────

SESSIONS_DIR = Path(".claude/logs/sessions")
SESSIONS_LOG = Path(".claude/logs/arize_skill_sessions.jsonl")


def start_skill_session(skill_name, model, project_name=None):
    """Create a new skill session and return session_id.

    Creates a session metadata file to track the lifecycle of a skill
    invocation (researcher, writer, reviewer, publisher). All agents
    spawned within this session pass --session-id to link their metrics.
    The project_name is stored so subsequent agents and end-session
    can use the same Arize project.
    """
    session_id = f"{skill_name}-{uuid.uuid4().hex[:8]}"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_info = {
        "session_id": session_id,
        "skill": skill_name,
        "model": model,
        "project_name": project_name or os.getenv("ARIZE_PROJECT_NAME", "claude-skills"),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }

    session_file = SESSIONS_DIR / f"{session_id}.json"
    session_file.write_text(json.dumps(session_info, indent=2), encoding="utf-8")

    return session_id


def end_skill_session(session_id):
    """Close a skill session: aggregate metrics, create summary span, log results.

    Reads all agent metrics with matching session_id from arize_metrics.jsonl,
    aggregates them into a session-level summary, creates an Arize summary span,
    and logs the session to arize_skill_sessions.jsonl.
    """
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return {"error": f"Session not found: {session_id}"}

    session_info = json.loads(session_file.read_text(encoding="utf-8"))

    # Collect all agent metrics for this session
    metrics_file = Path(".claude/logs/arize_metrics.jsonl")
    agents = []
    if metrics_file.exists():
        for line in metrics_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("session_id") == session_id:
                agents.append(entry)

    # Aggregate metrics
    total_input = sum(a.get("input_tokens", 0) for a in agents)
    total_output = sum(a.get("output_tokens", 0) for a in agents)
    total_cost = sum(a.get("cost_usd", 0) for a in agents)
    total_api_calls = sum(a.get("api_calls", 0) for a in agents)
    peak_context = max((a.get("context_tokens_peak", 0) for a in agents), default=0)
    total_agent_latency = sum(a.get("latency_seconds", 0) for a in agents)
    all_tools = set()
    for a in agents:
        all_tools.update(a.get("tools_used", []))

    # Calculate wall-clock latency (start-session to end-session)
    start_time = datetime.fromisoformat(session_info["start_time"])
    end_time = datetime.now(timezone.utc)
    wall_latency = round((end_time - start_time).total_seconds(), 2)

    context_limit = get_context_limit(session_info.get("model", ""))

    # Create summary span in Arize Phoenix
    tracer = get_tracer()
    if tracer:
        try:
            from opentelemetry.trace import StatusCode

            with tracer.start_as_current_span(
                name=f"skill-session:{session_info['skill']}",
                attributes={
                    "openinference.span.kind": "CHAIN",
                    "session.id": session_id,
                    "skill.name": session_info["skill"],
                    "model": session_info.get("model", ""),
                    "session.status": "completed",
                    "session.agents_count": len(agents),
                    "session.total_input_tokens": total_input,
                    "session.total_output_tokens": total_output,
                    "session.total_cost_usd": round(total_cost, 6),
                    "session.total_api_calls": total_api_calls,
                    "session.peak_context_tokens": peak_context,
                    "session.context_limit": context_limit,
                    "session.context_utilization": round((peak_context / context_limit) * 100, 2) if context_limit else 0,
                    "session.wall_latency_seconds": wall_latency,
                    "session.agent_latency_seconds": round(total_agent_latency, 2),
                    "session.tools_used": str(sorted(all_tools)),
                    "session.agent_ids": str([a.get("agent_id") for a in agents]),
                },
            ) as span:
                span.set_status(StatusCode.OK)
        except Exception as e:
            print(f"[WARN] Failed to create session summary span: {e}", file=sys.stderr)

    # Build session summary
    session_summary = {
        **session_info,
        "status": "completed",
        "end_time": end_time.isoformat(),
        "wall_latency_seconds": wall_latency,
        "agent_latency_seconds": round(total_agent_latency, 2),
        "agents_count": len(agents),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": round(total_cost, 6),
        "total_api_calls": total_api_calls,
        "peak_context_tokens": peak_context,
        "context_limit": context_limit,
        "context_utilization": round((peak_context / context_limit) * 100, 2) if context_limit else 0,
        "tools_used": sorted(all_tools),
        "agent_ids": [a.get("agent_id") for a in agents],
    }

    # Update session file
    session_file.write_text(json.dumps(session_summary, indent=2), encoding="utf-8")

    # Append to session-level log
    SESSIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(session_summary) + "\n")

    return session_summary


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


# ─── Pricing ─────────────────────────────────────────────────────────────────

PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-latest": {"input": 0.25, "output": 1.25},
    "claude-3-opus-latest": {"input": 15.0, "output": 75.0},
}

# Model context window sizes (max input tokens)
CONTEXT_LIMITS = {
    "claude-sonnet-4-5-20250929": 200_000,
    "claude-3-5-sonnet-latest": 200_000,
    "claude-3-5-haiku-latest": 200_000,
    "claude-3-opus-latest": 200_000,
}

def get_context_limit(model):
    """Get the max context window for a model."""
    return CONTEXT_LIMITS.get(model, 200_000)

def calculate_cost(model, input_tokens, output_tokens):
    """Calculate approximate cost in USD."""
    pricing = PRICING.get(model, next(iter(PRICING.values())))
    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


# ─── Agent Loop ──────────────────────────────────────────────────────────────

def _run_agent_loop(task, tools, model, max_tokens):
    """Core agentic loop — called within an OTel span context if available."""
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


def run_anthropic(task, tools, model, skill_name, agent_id, max_tokens, session_id=None):
    """Run the agent loop, optionally wrapped in an OTel span for Arize tracing.

    When a tracer is available, creates a parent span that groups all
    auto-instrumented Anthropic API calls as children. Span attributes
    include session_id, skill, agent_id, and post-run metrics.
    """
    tracer = get_tracer()

    if tracer:
        from opentelemetry.trace import StatusCode

        span_attrs = {
            "openinference.span.kind": "AGENT",
            "agent.id": agent_id,
            "skill.name": skill_name,
            "model": model,
        }
        if session_id:
            span_attrs["session.id"] = session_id

        with tracer.start_as_current_span(
            name=f"skill:{skill_name}/agent:{agent_id}",
            attributes=span_attrs,
        ) as span:
            text, metrics = _run_agent_loop(task, tools, model, max_tokens)
            # Enrich the span with post-run metrics
            span.set_attribute("tokens.input", metrics["input_tokens"])
            span.set_attribute("tokens.output", metrics["output_tokens"])
            span.set_attribute("api_calls", metrics["api_calls"])
            span.set_attribute("context.peak", metrics["context_tokens_peak"])
            span.set_attribute("tools_used", str(sorted(metrics["tools_used"])))
            span.set_status(StatusCode.OK)
            return text, metrics
    else:
        return _run_agent_loop(task, tools, model, max_tokens)


# ─── Local Metrics Logging ───────────────────────────────────────────────────

def log_metrics_locally(metrics):
    """Log metrics to .claude/logs directory."""
    log_path = Path(".claude/logs")
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / "arize_metrics.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics) + "\n")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instrumented Anthropic Sub-Agent")
    parser.add_argument("--action", default="run", choices=["run", "start-session", "end-session"],
                        help="Action: run (default), start-session, or end-session")
    parser.add_argument("--task", help="Task prompt")
    parser.add_argument("--task-file", help="Path to task prompt file")
    parser.add_argument("--tools", default="web_search,web_fetch", help="Comma-separated tools")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929", help="Model ID")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max tokens")
    parser.add_argument("--skill", default="researcher", help="Skill name")
    parser.add_argument("--agent-id", default="unknown", help="Agent identifier")
    parser.add_argument("--session-id", default=None, help="Session ID to link agent to a skill session")
    parser.add_argument("--project-name", default=None,
                        help="Arize project name (e.g., 'my_topic_claude_skills'). Stored in session and reused by all agents.")
    args = parser.parse_args()

    # ── Helper: resolve project name from session file ──────────────────────

    def resolve_project_name_from_session(session_id):
        """Read project_name from session file if available."""
        if not session_id:
            return None
        session_file = SESSIONS_DIR / f"{session_id}.json"
        if session_file.exists():
            info = json.loads(session_file.read_text(encoding="utf-8"))
            return info.get("project_name")
        return None

    # ── Handle session actions ──────────────────────────────────────────────

    if args.action == "start-session":
        project_name = args.project_name
        setup_tracing(project_name=project_name)
        session_id = start_skill_session(args.skill, args.model, project_name=project_name)
        # Print just the session_id for easy capture in bash
        print(session_id)
        return

    if args.action == "end-session":
        if not args.session_id:
            print("Error: --session-id required for end-session", file=sys.stderr)
            sys.exit(1)
        project_name = args.project_name or resolve_project_name_from_session(args.session_id)
        setup_tracing(project_name=project_name)
        summary = end_skill_session(args.session_id)
        print(json.dumps(summary, indent=2))
        return

    # ── Handle run action (default, backward compatible) ────────────────────

    # Resolve task
    task = args.task
    if not task and args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    if not task:
        print("Error: No task provided.", file=sys.stderr)
        sys.exit(1)

    # Resolve project name: explicit flag > session file > env var > default
    project_name = args.project_name or resolve_project_name_from_session(args.session_id)
    setup_tracing(project_name=project_name)

    # Run Agent
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    start_time = time.time()

    try:
        result, p_metrics = run_anthropic(
            task, tools, args.model, args.skill, args.agent_id, args.max_tokens,
            session_id=args.session_id,
        )

        # Finalize metrics
        context_limit = get_context_limit(args.model)
        metrics = {
            "agent_id": args.agent_id,
            "skill": args.skill,
            "provider": "anthropic",
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

        # Include session_id in metrics if provided
        if args.session_id:
            metrics["session_id"] = args.session_id

    except Exception as e:
        metrics = {
            "agent_id": args.agent_id, "skill": args.skill, "provider": "anthropic",
            "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if args.session_id:
            metrics["session_id"] = args.session_id
        result = f"Agent error: {e}"

    log_metrics_locally(metrics)
    print(json.dumps({"result": result, "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
