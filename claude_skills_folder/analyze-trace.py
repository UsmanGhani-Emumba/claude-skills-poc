"""
analyze-trace.py — Analyze Claude Code trace files (hooks + stream-json)

Usage:
    python analyze-trace.py                                          # List all trace files
    python analyze-trace.py hooks                                    # List all hook trace files
    python analyze-trace.py hooks latest                             # Analyze most recent hook trace
    python analyze-trace.py hooks traces/hooks-a1b2c3d4.jsonl        # Analyze specific hook trace
    python analyze-trace.py stream                                   # List all stream trace files
    python analyze-trace.py stream latest                            # Analyze most recent stream trace
    python analyze-trace.py stream traces/20260220-stream.jsonl      # Analyze specific stream trace
    python analyze-trace.py both latest                              # Analyze latest of both
"""

import json
import sys
from pathlib import Path
from collections import Counter

TRACES_DIR = Path("traces")


def load_jsonl(filepath):
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def find_latest(pattern):
    """Find the most recently modified file matching the pattern."""
    files = sorted(TRACES_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return None
    return files[0]


def list_trace_files(pattern, label):
    """List all trace files matching a pattern."""
    files = sorted(TRACES_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        print(f"  No {label} files found in {TRACES_DIR}/")
        return
    print(f"  {label} files ({len(files)} found):")
    print("  " + "-" * 56)
    for f in files:
        size_kb = f.stat().st_size / 1024
        lines = sum(1 for _ in open(f, encoding="utf-8"))
        print(f"    {f.name:40s} {size_kb:6.1f} KB  {lines:>5} events")


def resolve_file(arg, pattern):
    """Resolve 'latest' keyword or a direct path."""
    if arg == "latest":
        f = find_latest(pattern)
        if not f:
            print(f"  No files matching {pattern} in {TRACES_DIR}/")
            sys.exit(1)
        print(f"  Resolved 'latest' -> {f.name}")
        return f
    return Path(arg)


def analyze_hooks(filepath):
    if not filepath.exists():
        print(f"  File not found: {filepath}")
        return

    entries = load_jsonl(filepath)
    if not entries:
        print("  Hook trace is empty.")
        return

    pre_events = [e for e in entries if e.get("event") == "pre"]
    post_events = [e for e in entries if e.get("event") == "post"]

    # Count tools
    tool_counts = Counter(e.get("tool", "unknown") for e in pre_events)

    # Session info
    session_ids = set(e.get("session", "?") for e in entries)

    print("=" * 60)
    print("  HOOK TRACE ANALYSIS")
    print(f"  File: {filepath.name}")
    print("=" * 60)
    print(f"  Session(s):      {', '.join(s[:12] + '...' for s in session_ids)}")
    print(f"  Total events:    {len(entries)}")
    print(f"  Pre-tool calls:  {len(pre_events)}")
    print(f"  Post-tool calls: {len(post_events)}")
    print()
    print("  Tool Usage:")
    for tool, count in tool_counts.most_common():
        print(f"    {tool:30s} {count:>4}x")

    print()
    print("  Timeline (last 30 events):")
    print("  " + "-" * 56)
    for e in entries[-30:]:
        event = e.get("event", "?")
        tool = e.get("tool", "?")
        ts = e.get("ts", "?")[11:19]  # HH:MM:SS
        marker = ">>" if event == "pre" else "<<"
        preview = ""
        if event == "post":
            out = e.get("output_preview", "")
            if out:
                preview = f" | {out[:80]}..."
        print(f"  {ts} {marker} {tool}{preview}")

    print("=" * 60)


def analyze_stream(filepath):
    if not filepath.exists():
        print(f"  File not found: {filepath}")
        return

    entries = load_jsonl(filepath)
    if not entries:
        print("  Stream trace is empty.")
        return

    # Categorize events
    types = Counter(e.get("type", "unknown") for e in entries)
    tool_uses = [e for e in entries if e.get("type") == "tool_use"]

    # Extract tool names
    tool_names = Counter(e.get("tool_name", e.get("name", "unknown")) for e in tool_uses)

    print("=" * 60)
    print("  STREAM-JSON TRACE ANALYSIS")
    print(f"  File: {filepath.name}")
    print("=" * 60)
    print(f"  Total events:    {len(entries)}")
    print()
    print("  Event Types:")
    for etype, count in types.most_common():
        print(f"    {etype:30s} {count:>4}x")

    print()
    print("  Tool Calls:")
    if tool_names:
        for tool, count in tool_names.most_common():
            print(f"    {tool:30s} {count:>4}x")
    else:
        print("    (none found)")

    # Token accumulation across all events
    print()
    print("  Token Usage per Turn (accumulated):")
    print("  " + "-" * 56)
    prev_input = 0
    prev_output = 0
    pending_tools = []
    turn_num = 0
    total_cost = None
    session_id = None
    duration = None

    for e in entries:
        etype = e.get("type", "unknown")

        if etype == "tool_use":
            tool_name = e.get("tool_name", e.get("name", "unknown"))
            pending_tools.append(tool_name)

        usage = e.get("usage")
        if usage:
            inp = int(usage.get("input_tokens") or 0)
            out = int(usage.get("output_tokens") or 0)
            delta_in = inp - prev_input
            delta_out = out - prev_output
            if delta_in > 0 or delta_out > 0:
                turn_num += 1
                tools_str = ", ".join(pending_tools) if pending_tools else "(no tool call)"
                print(f"  Turn {turn_num}: [{tools_str}]")
                print(f"    +{delta_in:>6} input  +{delta_out:>6} output  (running total: {inp:,} / {out:,})")
                pending_tools = []
                prev_input = inp
                prev_output = out

        if "cost" in e:
            total_cost = e["cost"]
        if "session_id" in e:
            session_id = e["session_id"]
        if "duration" in e:
            duration = e["duration"]

    print()
    print("  " + "=" * 56)
    if prev_input > 0 or prev_output > 0:
        print(f"  GRAND TOTAL:  {prev_input:,} input tokens / {prev_output:,} output tokens")
    else:
        print("  GRAND TOTAL:  (no token data — requires API key, shows 0 on Pro)")
    if total_cost is not None:
        print(f"  Total cost:   ${total_cost}")
    if session_id:
        print(f"  Session ID:   {session_id}")
    if duration:
        print(f"  Duration:     {duration}")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print()
        print("Available trace files:")
        print()
        list_trace_files("hooks-*.jsonl", "Hook traces")
        print()
        list_trace_files("*-stream.jsonl", "Stream traces")
        sys.exit(0)

    mode = sys.argv[1]

    if mode == "hooks":
        if len(sys.argv) < 3:
            list_trace_files("hooks-*.jsonl", "Hook traces")
            return
        filepath = resolve_file(sys.argv[2], "hooks-*.jsonl")
        analyze_hooks(filepath)

    elif mode == "stream":
        if len(sys.argv) < 3:
            list_trace_files("*-stream.jsonl", "Stream traces")
            return
        filepath = resolve_file(sys.argv[2], "*-stream.jsonl")
        analyze_stream(filepath)

    elif mode == "both":
        if len(sys.argv) < 3:
            print("Usage: python analyze-trace.py both latest")
            sys.exit(1)
        if sys.argv[2] == "latest":
            hook_file = find_latest("hooks-*.jsonl")
            stream_file = find_latest("*-stream.jsonl")
            if hook_file:
                analyze_hooks(hook_file)
                print()
            else:
                print("  No hook traces found.")
            if stream_file:
                analyze_stream(stream_file)
            else:
                print("  No stream traces found.")
        elif len(sys.argv) >= 4:
            analyze_hooks(Path(sys.argv[2]))
            print()
            analyze_stream(Path(sys.argv[3]))
        else:
            analyze_hooks(Path(sys.argv[2]))

    elif mode == "latest":
        # Shortcut: analyze latest hook trace
        filepath = find_latest("hooks-*.jsonl")
        if not filepath:
            print("  No hook trace files found in traces/")
            sys.exit(1)
        print(f"  Resolved 'latest' -> {filepath.name}")
        analyze_hooks(filepath)

    else:
        # Treat as a direct file path
        p = Path(mode)
        if p.exists():
            if "hooks" in p.name:
                analyze_hooks(p)
            elif "stream" in p.name:
                analyze_stream(p)
            else:
                analyze_hooks(p)
        else:
            print(f"  Unknown command or file not found: {mode}")
            print(__doc__)
            sys.exit(1)


if __name__ == "__main__":
    main()
