"""
Metrics Summary — aggregates and displays metrics from instrumented sub-agent runs.

Reads from: .claude/logs/arize_metrics.jsonl (agent-level)
            .claude/logs/arize_skill_sessions.jsonl (session-level)

Usage:       python scripts/metrics_summary.py
             python scripts/metrics_summary.py --last 10
             python scripts/metrics_summary.py --skill researcher
             python scripts/metrics_summary.py --session researcher-a1b2c3d4
             python scripts/metrics_summary.py --sessions
             python scripts/metrics_summary.py --sessions --skill writer
"""

import argparse
import json
from pathlib import Path

METRICS_LOG = Path(".claude/logs/arize_metrics.jsonl")
SESSIONS_LOG = Path(".claude/logs/arize_skill_sessions.jsonl")


def load_metrics(skill_filter=None, last_n=None, session_filter=None):
    """Load metrics entries from the JSONL log file."""
    if not METRICS_LOG.exists():
        return []

    entries = []
    with open(METRICS_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if skill_filter and entry.get("skill") != skill_filter:
                continue
            if session_filter and entry.get("session_id") != session_filter:
                continue
            entries.append(entry)

    if last_n:
        entries = entries[-last_n:]
    return entries


def load_sessions(skill_filter=None, last_n=None):
    """Load session entries from the session-level JSONL log file."""
    if not SESSIONS_LOG.exists():
        return []

    entries = []
    with open(SESSIONS_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if skill_filter and entry.get("skill") != skill_filter:
                continue
            entries.append(entry)

    if last_n:
        entries = entries[-last_n:]
    return entries


def print_summary(entries):
    """Print a formatted metrics summary."""
    if not entries:
        print("No metrics logged yet.")
        print(f"Expected log file: {METRICS_LOG}")
        return

    # Group by skill
    skills = {}
    for e in entries:
        skill = e.get("skill", "unknown")
        skills.setdefault(skill, []).append(e)

    print("=" * 64)
    print("  ARIZE METRICS SUMMARY")
    print("=" * 64)

    grand_input = 0
    grand_output = 0
    grand_cost = 0.0
    grand_agents = len(entries)

    for skill, runs in skills.items():
        s_input = sum(r.get("input_tokens", 0) for r in runs)
        s_output = sum(r.get("output_tokens", 0) for r in runs)
        s_cost = sum(r.get("cost_usd", 0) for r in runs)
        s_latency = sum(r.get("latency_seconds", 0) for r in runs)
        s_tool_calls = sum(r.get("tool_calls_count", 0) for r in runs)
        all_tools = set()
        for r in runs:
            all_tools.update(r.get("tools_used", []))

        print(f"\n  ── {skill.upper()} ({'─' * (50 - len(skill))})")
        print(f"  Sub-agents:       {len(runs)}")
        print(f"  Input tokens:     {s_input:,}")
        print(f"  Output tokens:    {s_output:,}")
        print(f"  Total cost:       ${s_cost:.4f}")
        print(f"  Total latency:    {s_latency:.1f}s")
        print(f"  Tool calls:       {s_tool_calls}")
        print(f"  Distinct tools:   {len(all_tools)} ({', '.join(sorted(all_tools))})")

        grand_input += s_input
        grand_output += s_output
        grand_cost += s_cost

    print(f"\n{'=' * 64}")
    print(f"  TOTALS")
    print(f"  Sub-agents:       {grand_agents}")
    print(f"  Input tokens:     {grand_input:,}")
    print(f"  Output tokens:    {grand_output:,}")
    print(f"  Total cost:       ${grand_cost:.4f}")
    print(f"{'=' * 64}")


def print_detail(entries):
    """Print per-agent detail rows."""
    if not entries:
        return

    print(f"\n{'Agent':<8} {'Skill':<12} {'Session':<22} {'In Tok':>8} {'Out Tok':>8} {'Cost':>9} {'Latency':>8} {'Tools'}")
    print("-" * 95)
    for e in entries:
        agent_id = e.get("agent_id", "?")
        skill = e.get("skill", "?")
        session = e.get("session_id", "-")
        if len(session) > 20:
            session = session[:20] + ".."
        inp = e.get("input_tokens", 0)
        out = e.get("output_tokens", 0)
        cost = e.get("cost_usd", 0)
        latency = e.get("latency_seconds", 0)
        tools = ", ".join(e.get("tools_used", []))
        print(f"{agent_id:<8} {skill:<12} {session:<22} {inp:>8,} {out:>8,} ${cost:>8.4f} {latency:>7.1f}s {tools}")


def print_sessions(sessions):
    """Print session-level summary table."""
    if not sessions:
        print("No skill sessions logged yet.")
        print(f"Expected log file: {SESSIONS_LOG}")
        return

    print("=" * 80)
    print("  SKILL SESSION SUMMARY")
    print("=" * 80)

    print(f"\n{'Session ID':<28} {'Skill':<12} {'Agents':>6} {'In Tok':>9} {'Out Tok':>9} {'Cost':>9} {'Wall':>8} {'Tools'}")
    print("-" * 100)

    grand_input = 0
    grand_output = 0
    grand_cost = 0.0
    grand_agents = 0

    for s in sessions:
        sid = s.get("session_id", "?")
        if len(sid) > 26:
            sid = sid[:26] + ".."
        skill = s.get("skill", "?")
        agents = s.get("agents_count", 0)
        inp = s.get("total_input_tokens", 0)
        out = s.get("total_output_tokens", 0)
        cost = s.get("total_cost_usd", 0)
        wall = s.get("wall_latency_seconds", 0)
        tools = ", ".join(s.get("tools_used", []))

        print(f"{sid:<28} {skill:<12} {agents:>6} {inp:>9,} {out:>9,} ${cost:>8.4f} {wall:>7.1f}s {tools}")

        grand_input += inp
        grand_output += out
        grand_cost += cost
        grand_agents += agents

    print("-" * 100)
    print(f"{'TOTALS':<28} {'':<12} {grand_agents:>6} {grand_input:>9,} {grand_output:>9,} ${grand_cost:>8.4f}")
    print("=" * 80)


def print_session_detail(session_id, agents):
    """Print detail for a specific session."""
    if not agents:
        print(f"No agent metrics found for session: {session_id}")
        return

    # Load session metadata
    session_file = Path(f".claude/logs/sessions/{session_id}.json")
    if session_file.exists():
        session = json.loads(session_file.read_text(encoding="utf-8"))
        print("=" * 64)
        print(f"  SESSION: {session_id}")
        print("=" * 64)
        print(f"  Skill:            {session.get('skill', '?')}")
        print(f"  Status:           {session.get('status', '?')}")
        print(f"  Model:            {session.get('model', '?')}")
        print(f"  Agents:           {session.get('agents_count', len(agents))}")
        print(f"  Input tokens:     {session.get('total_input_tokens', 0):,}")
        print(f"  Output tokens:    {session.get('total_output_tokens', 0):,}")
        print(f"  Total cost:       ${session.get('total_cost_usd', 0):.4f}")
        print(f"  Wall latency:     {session.get('wall_latency_seconds', 0):.1f}s")
        print(f"  Agent latency:    {session.get('agent_latency_seconds', 0):.1f}s")
        print(f"  Peak context:     {session.get('peak_context_tokens', 0):,}")
        print(f"  Context util:     {session.get('context_utilization', 0):.1f}%")
        print(f"  Tools:            {', '.join(session.get('tools_used', []))}")
        print("-" * 64)

    print_detail(agents)


def main():
    parser = argparse.ArgumentParser(description="Display Arize agent metrics summary")
    parser.add_argument("--skill", help="Filter by skill name")
    parser.add_argument("--last", type=int, help="Show only the last N entries")
    parser.add_argument("--detail", action="store_true", help="Show per-agent detail table")
    parser.add_argument("--session", help="Show agents within a specific session ID")
    parser.add_argument("--sessions", action="store_true", help="Show session-level summary table")
    args = parser.parse_args()

    if args.sessions:
        sessions = load_sessions(skill_filter=args.skill, last_n=args.last)
        print_sessions(sessions)
        return

    if args.session:
        entries = load_metrics(session_filter=args.session)
        print_session_detail(args.session, entries)
        return

    entries = load_metrics(skill_filter=args.skill, last_n=args.last)
    print_summary(entries)
    if args.detail:
        print_detail(entries)


if __name__ == "__main__":
    main()
