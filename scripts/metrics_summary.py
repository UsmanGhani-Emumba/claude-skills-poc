"""
Metrics Summary — aggregates and displays metrics from instrumented sub-agent runs.

Reads from: .claude/logs/arize_metrics.jsonl
Usage:       python scripts/metrics_summary.py
             python scripts/metrics_summary.py --last 10
             python scripts/metrics_summary.py --skill researcher
"""

import argparse
import json
from pathlib import Path

LOG_FILE = Path(".claude/logs/arize_metrics.jsonl")


def load_metrics(skill_filter=None, last_n=None):
    """Load metrics entries from the JSONL log file."""
    if not LOG_FILE.exists():
        return []

    entries = []
    with open(LOG_FILE, encoding="utf-8") as f:
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
        print(f"Expected log file: {LOG_FILE}")
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

    print(f"\n{'Agent':<8} {'Skill':<12} {'In Tok':>8} {'Out Tok':>8} {'Cost':>9} {'Latency':>8} {'Tools'}")
    print("-" * 72)
    for e in entries:
        agent_id = e.get("agent_id", "?")
        skill = e.get("skill", "?")
        inp = e.get("input_tokens", 0)
        out = e.get("output_tokens", 0)
        cost = e.get("cost_usd", 0)
        latency = e.get("latency_seconds", 0)
        tools = ", ".join(e.get("tools_used", []))
        print(f"{agent_id:<8} {skill:<12} {inp:>8,} {out:>8,} ${cost:>8.4f} {latency:>7.1f}s {tools}")


def main():
    parser = argparse.ArgumentParser(description="Display Arize agent metrics summary")
    parser.add_argument("--skill", help="Filter by skill name")
    parser.add_argument("--last", type=int, help="Show only the last N entries")
    parser.add_argument("--detail", action="store_true", help="Show per-agent detail table")
    args = parser.parse_args()

    entries = load_metrics(skill_filter=args.skill, last_n=args.last)
    print_summary(entries)
    if args.detail:
        print_detail(entries)


if __name__ == "__main__":
    main()
