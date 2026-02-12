"""
Instrumented Gemini Sub-Agent with Arize Phoenix Tracing.

Used by ALL Gemini skills (.gemini) to run instrumented sub-agents
with full observability metrics for Google Gemini models.

Supports skill-level session tracking:
  - start-session: Begin tracking a skill invocation
  - run (default): Execute an agent within an optional session
  - end-session: Aggregate and log session-level metrics

Metrics captured:
  - Input/Output tokens
  - Context used (peak and total)
  - Cost (USD)
  - Latency
  - Distinct tools used
  - API calls made
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
import random
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ─── Tracing Setup ───────────────────────────────────────────────────────────

def setup_tracing(project_name=None):
    """Initialize Arize Phoenix tracing for Gemini if available."""
    try:
        from phoenix.otel import register

        arize_api_key = os.getenv("ARIZE_API_KEY", "")
        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "https://app.phoenix.arize.com/v1/traces",
        )
        final_project_name = project_name or os.getenv("ARIZE_PROJECT_NAME", "gemini-skills")

        headers = {}
        if arize_api_key:
            headers["api_key"] = arize_api_key

        import contextlib
        with contextlib.redirect_stdout(None):
            tracer_provider = register(
                project_name=final_project_name,
                endpoint=endpoint,
                headers=headers if headers else None,
            )

        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        GoogleGenAIInstrumentor().instrument(tracer_provider=tracer_provider)

        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[WARN] Tracing setup failed: {e}", file=sys.stderr)
        return False

def get_tracer():
    """Get OpenTelemetry tracer for manual span creation."""
    try:
        from opentelemetry import trace
        return trace.get_tracer("gemini-skills-agent")
    except ImportError:
        return None

# ─── Session Management ─────────────────────────────────────────────────────

SESSIONS_DIR = Path(".gemini/logs/sessions")
SESSIONS_LOG = Path(".gemini/logs/arize_skill_sessions.jsonl")

def start_skill_session(skill_name, model, project_name=None):
    session_id = f"{skill_name}-{uuid.uuid4().hex[:8]}"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_info = {
        "session_id": session_id,
        "skill": skill_name,
        "model": model,
        "project_name": project_name or os.getenv("ARIZE_PROJECT_NAME", "gemini-skills"),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }

    session_file = SESSIONS_DIR / f"{session_id}.json"
    session_file.write_text(json.dumps(session_info, indent=2), encoding="utf-8")
    return session_id

def end_skill_session(session_id):
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return {"error": f"Session not found: {session_id}"}

    session_info = json.loads(session_file.read_text(encoding="utf-8"))
    metrics_file = Path(".gemini/logs/arize_metrics.jsonl")
    agents = []
    if metrics_file.exists():
        for line in metrics_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip(): continue
            entry = json.loads(line)
            if entry.get("session_id") == session_id:
                agents.append(entry)

    total_input = sum(a.get("input_tokens", 0) for a in agents)
    total_output = sum(a.get("output_tokens", 0) for a in agents)
    total_cost = sum(a.get("cost_usd", 0) for a in agents)
    total_api_calls = sum(a.get("api_calls", 0) for a in agents)
    peak_context = max((a.get("context_tokens_peak", 0) for a in agents), default=0)
    total_agent_latency = sum(a.get("latency_seconds", 0) for a in agents)
    all_tools = set()
    for a in agents:
        all_tools.update(a.get("tools_used", []))

    start_time = datetime.fromisoformat(session_info["start_time"])
    end_time = datetime.now(timezone.utc)
    wall_latency = round((end_time - start_time).total_seconds(), 2)
    context_limit = get_context_limit(session_info.get("model", ""))

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
                },
            ) as span:
                span.set_status(StatusCode.OK)
        except Exception as e:
            print(f"[WARN] Failed to create session summary span: {e}", file=sys.stderr)

    session_summary = {
        **session_info,
        "status": "completed",
        "end_time": end_time.isoformat(),
        "wall_latency_seconds": wall_latency,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": round(total_cost, 6),
        "tools_used": sorted(all_tools),
    }

    session_file.write_text(json.dumps(session_summary, indent=2), encoding="utf-8")
    SESSIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(session_summary) + "\n")

    return session_summary

# ─── Tool Definitions ────────────────────────────────────────────────────────

# ─── Tool Dispatcher ──────────────────────────────────────────────────────────

def call_skill_tool(tool_name: str, skill_name: str, **kwargs):
    """
    Generic dispatcher that runs tools defined in a skill's references folder.
    Supports .py and .js scripts.
    """
    ref_dir = Path(f".gemini/skills/{skill_name}/references")
    
    # Check for .py script
    py_script = ref_dir / f"{tool_name}.py"
    if py_script.exists():
        args = [sys.executable, str(py_script)] + [str(v) for v in kwargs.values()]
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=60)
            return result.stdout or result.stderr or "No output"
        except Exception as e:
            return f"Error running {tool_name}.py: {e}"

    # Check for .js script
    js_script = ref_dir / f"{tool_name}.js"
    if js_script.exists():
        env = os.environ.copy()
        # Specialized env handling for Notion
        if "notion" in tool_name.lower():
            token = get_notion_token()
            if token: env["NOTION_TOKEN"] = token
            if "parent_id" in kwargs: env["NOTION_PARENT_ID"] = kwargs["parent_id"]
        
        # If it's notion_publish, it needs the content file
        content_file = None
        if tool_name == "notion_publish" and "blog_json_content" in kwargs:
            content_file = f"temp_blog_{uuid.uuid4().hex[:8]}.json"
            Path(content_file).write_text(kwargs["blog_json_content"], encoding="utf-8")
            env["CONTENT_FILE"] = content_file

        args = ["node", str(js_script)]
        try:
            result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
            return result.stdout or result.stderr or "No output"
        except Exception as e:
            return f"Error running {tool_name}.js: {e}"
        finally:
            if content_file and os.path.exists(content_file):
                os.remove(content_file)

    return f"Error: Tool '{tool_name}' not found in {ref_dir}"

def bash(command: str, **kwargs):
    """Run a generic bash/powershell command."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = (result.stdout or "") + (result.stderr or "")
        return output[:5000] if output else "No output"
    except Exception as e:
        return f"Error running command: {e}"

def web_search(query: str, **kwargs):
    """Search the web for a query."""
    return f"Search results for: {query}\n[Note: Use web_fetch on specific URLs found.]"

def get_notion_token():
    """Extract Notion token from .mcp.json."""
    mcp_path = Path(".mcp.json")
    if mcp_path.exists():
        try:
            mcp_data = json.loads(mcp_path.read_text())
            return mcp_data.get("mcpServers", {}).get("notion", {}).get("env", {}).get("NOTION_TOKEN")
        except: pass
    return os.getenv("NOTION_TOKEN")

TOOL_FUNCTIONS = {
    "bash": bash,
    "web_search": web_search,
}

# ─── Pricing ─────────────────────────────────────────────────────────────────

PRICING = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}

CONTEXT_LIMITS = {
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-2.0-flash": 1_000_000,
}

def get_context_limit(model):
    return CONTEXT_LIMITS.get(model, 1_000_000)

def calculate_cost(model, input_tokens, output_tokens):
    pricing = PRICING.get(model, PRICING["gemini-1.5-flash"])
    if "flash" in model.lower(): pricing = PRICING["gemini-2.0-flash"]
    elif "pro" in model.lower(): pricing = PRICING["gemini-1.5-pro"]
    return round((input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"], 6)

# ─── Agent Loop ──────────────────────────────────────────────────────────────

def run_gemini(task, tool_names, model_name, skill_name, agent_id, session_id=None, max_tokens=4096):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    # 1. Load Skill Instructions
    skill_path = Path(f".gemini/skills/{skill_name}/SKILL.md")
    system_instruction = ""
    if skill_path.exists():
        system_instruction = skill_path.read_text(encoding="utf-8").strip()

    # 2. Dynamic Tool Loading
    # If no tool_names provided, auto-discover from tools.json
    if not tool_names or (len(tool_names) == 1 and not tool_names[0]):
        ref_dir = Path(f".gemini/skills/{skill_name}/references")
        t_json = ref_dir / "tools.json"
        if t_json.exists():
            try:
                tool_names = list(json.loads(t_json.read_text()).keys())
                # Add core tools by default for researcher
                if skill_name == "researcher":
                    tool_names.extend(["bash", "web_search"])
            except: pass

    declarations = []

    # Helper to add core tools
    if "bash" in tool_names:
        declarations.append(types.FunctionDeclaration(
            name="bash",
            description="Run a generic bash/powershell command.",
            parameters={
                "type": "OBJECT",
                "properties": {"command": {"type": "STRING", "description": "The command to run."}},
                "required": ["command"]
            }
        ))
    if "web_search" in tool_names:
        declarations.append(types.FunctionDeclaration(
            name="web_search",
            description="Search the web for a query.",
            parameters={
                "type": "OBJECT",
                "properties": {"query": {"type": "STRING", "description": "The search term."}},
                "required": ["query"]
            }
        ))

    # Add skill-specific tools from tools.json metadata
    ref_dir = Path(f".gemini/skills/{skill_name}/references")
    tools_config_path = ref_dir / "tools.json"
    
    if tools_config_path.exists():
        try:
            tools_config = json.loads(tools_config_path.read_text())
            for name, config in tools_config.items():
                if name in ["bash", "web_search"]: continue
                
                desc = config.get("description", "")
                params = config.get("parameters", {})
                
                # Convert simple params to JSON schema
                properties = {}
                required = []
                for p_name, p_type in params.items():
                    properties[p_name] = {"type": "STRING" if p_type == "string" else "OBJECT"}
                    required.append(p_name)
                
                declarations.append(types.FunctionDeclaration(
                    name=name,
                    description=desc,
                    parameters={
                        "type": "OBJECT",
                        "properties": properties,
                        "required": required
                    }
                ))
            print(f"[DEBUG] Enrolled tools for {skill_name}: {[d.name for d in declarations]}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to load tools.json for {skill_name}: {e}", file=sys.stderr)

    tools = [types.Tool(function_declarations=declarations)] if declarations else None

    config = types.GenerateContentConfig(
        system_instruction=system_instruction if system_instruction else None,
        tools=tools,
        max_output_tokens=max_tokens,
    )

    tracer = get_tracer()
    
    def execute_with_retries(task_content):
        # We handle multi-turn manual loop if tools are present
        history = [types.Content(role="user", parts=[types.Part(text=task_content)])]
        
        total_metrics = {"input_tokens": 0, "output_tokens": 0, "api_calls": 0, "tools_used": set(), "context_tokens_peak": 0}
        
        for turn in range(10): # Max 10 turns
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(model=model_name, contents=history, config=config)
                    total_metrics["api_calls"] += 1
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        delay = (2 ** attempt) * 5 + random.uniform(0, 2)
                        print(f"[WARN] 429 Rate Limit hit. Retrying turn {turn+1} in {delay:.1f}s...", file=sys.stderr)
                        time.sleep(delay)
                        continue
                    raise e
            
            # Parse metrics for this turn
            turn_metrics = parse_response_metrics(response)
            total_metrics["input_tokens"] += turn_metrics["input_tokens"]
            total_metrics["output_tokens"] += turn_metrics["output_tokens"]
            total_metrics["context_tokens_peak"] = max(total_metrics["context_tokens_peak"], turn_metrics["input_tokens"])
            
            # Add model response to history
            cand = response.candidates[0]
            history.append(cand.content)
            
            # Check for tool calls
            tool_calls = [p.function_call for p in cand.content.parts if p.function_call]
            if not tool_calls:
                return response.text, total_metrics
            
            # Execute tool calls
            tool_results = []
            for call in tool_calls:
                total_metrics["tools_used"].add(call.name)
                print(f"[TOOL] Executing: {call.name}({call.args})", file=sys.stderr)
                # Dispatch
                if call.name in ["bash", "web_search"]:
                    res = TOOL_FUNCTIONS[call.name](**call.args)
                else:
                    res = call_skill_tool(call.name, skill_name, **call.args)
                
                tool_results.append(types.Part(
                    function_response=types.FunctionResponse(name=call.name, response={"result": res})
                ))
            
            # Add tool results to history
            history.append(types.Content(role="user", parts=tool_results))
            
        return history[-1].parts[0].text, total_metrics

    if tracer:
        from opentelemetry.trace import StatusCode
        span_attrs = {"openinference.span.kind": "AGENT", "agent.id": agent_id, "skill.name": skill_name, "model": model_name}
        if session_id: span_attrs["session.id"] = session_id
        
        with tracer.start_as_current_span(name=f"skill:{skill_name}/agent:{agent_id}", attributes=span_attrs) as span:
            res_text, metrics = execute_with_retries(task)
            span.set_attribute("tokens.input", metrics["input_tokens"])
            span.set_attribute("tokens.output", metrics["output_tokens"])
            span.set_status(StatusCode.OK)
            return res_text, metrics
    else:
        return execute_with_retries(task)

def parse_response_metrics(response):
    metrics = {"input_tokens": 0, "output_tokens": 0, "api_calls": 1, "tools_used": set(), "context_tokens_peak": 0}
    if response.usage_metadata:
        metrics["input_tokens"] = response.usage_metadata.prompt_token_count or 0
        metrics["output_tokens"] = response.usage_metadata.candidates_token_count or 0
        metrics["context_tokens_peak"] = response.usage_metadata.prompt_token_count or 0
    if response.candidates:
        for c in response.candidates:
            if c.content and c.content.parts:
                for p in c.content.parts:
                    if p.function_call: metrics["tools_used"].add(p.function_call.name)
    return metrics

# ─── Local Metrics Logging ───────────────────────────────────────────────────

def log_metrics_locally(metrics):
    log_path = Path(".gemini/logs")
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "arize_metrics.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metrics) + "\n")

# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instrumented Gemini Sub-Agent")
    parser.add_argument("--action", default="run", choices=["run", "start-session", "end-session"])
    parser.add_argument("--task", help="Task prompt")
    parser.add_argument("--task-file", help="Path to task prompt file")
    parser.add_argument("--tools", default="", help="Comma-separated tools")
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Model ID")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--skill", default="researcher")
    parser.add_argument("--agent-id", default="unknown")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--project-name", default=None)
    args = parser.parse_args()

    def resolve_project_name(session_id):
        if not session_id: return None
        s_file = SESSIONS_DIR / f"{session_id}.json"
        return json.loads(s_file.read_text()).get("project_name") if s_file.exists() else None

    if args.action == "start-session":
        setup_tracing(args.project_name)
        sid = start_skill_session(args.skill, args.model, args.project_name)
        print(sid)
        return

    if args.action == "end-session":
        project_name = args.project_name or resolve_project_name(args.session_id)
        setup_tracing(project_name)
        print(json.dumps(end_skill_session(args.session_id), indent=2))
        return

    # Run
    task = args.task
    if not task and args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8").strip()
    
    project_name = args.project_name or resolve_project_name(args.session_id)
    setup_tracing(project_name)

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    start_time = time.time()

    try:
        result, p_metrics = run_gemini(task, tools, args.model, args.skill, args.agent_id, session_id=args.session_id, max_tokens=args.max_tokens)
        metrics = {
            "agent_id": args.agent_id, "skill": args.skill, "provider": "gemini", "model": args.model,
            "latency_seconds": round(time.time() - start_time, 2),
            "cost_usd": calculate_cost(args.model, p_metrics["input_tokens"], p_metrics["output_tokens"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **p_metrics
        }
        metrics["tools_used"] = sorted(metrics["tools_used"])
        if args.session_id: metrics["session_id"] = args.session_id
    except Exception as e:
        metrics = {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
        result = f"Error: {e}"

    log_metrics_locally(metrics)
    print(json.dumps({"result": result, "metrics": metrics}, indent=2))

if __name__ == "__main__":
    main()
