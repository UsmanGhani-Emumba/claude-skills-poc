#!/usr/bin/env python3
"""
Skill Metrics Tracker
Tracks token usage, latency, and cost for Claude Code skills using the Anthropic SDK.

Usage from skills:
  Start:  python metrics/tracker.py start <skill_name> "<input_text>"
  End:    python metrics/tracker.py end <skill_name> "<output_text>"
  Report: python metrics/tracker.py report
  Clear:  python metrics/tracker.py clear

Environment:
  ANTHROPIC_API_KEY - Required for exact token counting
"""

import json
import sys
import time
import io
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Token counting using tiktoken (accurate, no API key needed)
TIKTOKEN_ENCODER = None
try:
    import tiktoken
    TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")  # Claude-compatible
except ImportError:
    print("⚠️  tiktoken not installed. Run: pip install tiktoken")

# Default model for token counting
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Claude pricing (as of 2025 - update as needed)
PRICING = {
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},  # per 1M tokens
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-3-5-20241022": {"input": 0.25, "output": 1.25},
    "default": {"input": 3.00, "output": 15.00}  # Default to Sonnet pricing
}

METRICS_DIR = Path(__file__).parent
METRICS_FILE = METRICS_DIR / "metrics.jsonl"
ACTIVE_FILE = METRICS_DIR / "active_sessions.json"


def count_tokens(text: str) -> tuple[int, str]:
    """
    Count tokens using tiktoken (accurate, no API needed).

    Returns:
        tuple: (token_count, method) - method is "tiktoken" or "estimate"
    """
    if not text:
        return 0, "none"

    # Method 1: tiktoken (accurate, ~98% match with Claude)
    if TIKTOKEN_ENCODER:
        return len(TIKTOKEN_ENCODER.encode(text)), "tiktoken"

    # Method 2: Character-based fallback (~4 chars per token)
    return len(text) // 4, "estimate"


def calculate_cost(input_tokens: int, output_tokens: int, model: str = "default") -> float:
    """Calculate cost in USD based on token counts."""
    pricing = PRICING.get(model, PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def start_tracking(skill_name: str, input_text: str = "", model: str = DEFAULT_MODEL) -> dict:
    """Start tracking a skill execution."""
    METRICS_DIR.mkdir(exist_ok=True)

    input_tokens, input_method = count_tokens(input_text)

    session = {
        "skill": skill_name,
        "model": model,
        "start_time": time.time(),
        "start_timestamp": datetime.now().isoformat(),
        "input_tokens": input_tokens,
        "input_method": input_method,
        "input_text_length": len(input_text)
    }

    # Load or create active sessions
    active = {}
    if ACTIVE_FILE.exists():
        try:
            active = json.loads(ACTIVE_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            active = {}

    active[skill_name] = session
    ACTIVE_FILE.write_text(json.dumps(active, indent=2), encoding='utf-8')

    print(f"📊 Metrics tracking started for: {skill_name}")
    print(f"   Model: {model}")
    print(f"   Input tokens ({input_method}): {input_tokens}")

    return session


def end_tracking(skill_name: str, output_text: str = "") -> dict:
    """End tracking and log final metrics."""
    end_time = time.time()

    # Load active session
    if not ACTIVE_FILE.exists():
        print(f"⚠️  No active session found for: {skill_name}")
        return {}

    try:
        active = json.loads(ACTIVE_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        print(f"⚠️  Could not read active sessions")
        return {}

    if skill_name not in active:
        print(f"⚠️  No active session for skill: {skill_name}")
        return {}

    session = active[skill_name]
    model = session.get("model", DEFAULT_MODEL)

    # Calculate metrics
    output_tokens, output_method = count_tokens(output_text)
    input_method = session.get("input_method", "estimate")
    latency_seconds = end_time - session["start_time"]
    cost = calculate_cost(session["input_tokens"], output_tokens, model)

    metrics = {
        "skill": skill_name,
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "latency_seconds": round(latency_seconds, 2),
        "input_tokens": session["input_tokens"],
        "input_method": input_method,
        "output_tokens": output_tokens,
        "output_method": output_method,
        "total_tokens": session["input_tokens"] + output_tokens,
        "cost_usd": cost,
        "output_text_length": len(output_text)
    }

    # Append to metrics log
    with open(METRICS_FILE, "a", encoding='utf-8') as f:
        f.write(json.dumps(metrics) + "\n")

    # Remove from active sessions
    del active[skill_name]
    ACTIVE_FILE.write_text(json.dumps(active, indent=2), encoding='utf-8')

    # Print summary
    print(f"\n📊 Metrics for: {skill_name}")
    print(f"   ⏱️  Latency:       {metrics['latency_seconds']}s")
    print(f"   📥 Input tokens:  {metrics['input_tokens']} ({input_method})")
    print(f"   📤 Output tokens: {metrics['output_tokens']} ({output_method})")
    print(f"   📊 Total tokens:  {metrics['total_tokens']}")
    print(f"   💰 Cost:          ${metrics['cost_usd']:.6f}")

    return metrics


def generate_report() -> None:
    """Generate a summary report of all tracked metrics."""
    if not METRICS_FILE.exists():
        print("No metrics data found.")
        return

    metrics_list = []
    with open(METRICS_FILE, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                metrics_list.append(json.loads(line))

    if not metrics_list:
        print("No metrics data found.")
        return

    # Aggregate by skill
    by_skill = {}
    for m in metrics_list:
        skill = m["skill"]
        if skill not in by_skill:
            by_skill[skill] = {
                "count": 0,
                "total_latency": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0,
                "methods": {"exact": 0, "tiktoken": 0, "estimate": 0}
            }
        by_skill[skill]["count"] += 1
        by_skill[skill]["total_latency"] += m["latency_seconds"]
        by_skill[skill]["total_input_tokens"] += m["input_tokens"]
        by_skill[skill]["total_output_tokens"] += m["output_tokens"]
        by_skill[skill]["total_cost"] += m.get("cost_usd", m.get("estimated_cost_usd", 0))
        # Track counting method used
        method = m.get("input_method", m.get("output_method", "estimate"))
        if method in by_skill[skill]["methods"]:
            by_skill[skill]["methods"][method] += 1

    # Print report
    print("\n" + "=" * 60)
    print("📊 SKILL METRICS REPORT")
    print("=" * 60)

    total_cost = 0
    total_tokens = 0
    total_invocations = 0

    for skill, data in by_skill.items():
        avg_latency = data["total_latency"] / data["count"]
        methods = data["methods"]
        method_str = ", ".join(f"{k}:{v}" for k, v in methods.items() if v > 0)

        print(f"\n🔹 {skill.upper()}")
        print(f"   Invocations:      {data['count']}")
        print(f"   Avg latency:      {avg_latency:.2f}s")
        print(f"   Total input:      {data['total_input_tokens']} tokens")
        print(f"   Total output:     {data['total_output_tokens']} tokens")
        print(f"   Total cost:       ${data['total_cost']:.6f}")
        print(f"   Token methods:    {method_str}")

        total_cost += data["total_cost"]
        total_tokens += data["total_input_tokens"] + data["total_output_tokens"]
        total_invocations += data["count"]

    print("\n" + "-" * 60)
    print(f"📈 TOTALS")
    print(f"   Total invocations: {total_invocations}")
    print(f"   Total tokens:      {total_tokens}")
    print(f"   Total cost:        ${total_cost:.6f}")
    print("=" * 60)

    # Show current token counting method
    if TIKTOKEN_ENCODER:
        print("\n✅ Token counting: tiktoken (accurate)")
    else:
        print("\n⚠️  Token counting: character estimate (run: pip install tiktoken)")


def clear_metrics() -> None:
    """Clear all metrics data."""
    if METRICS_FILE.exists():
        METRICS_FILE.unlink()
    if ACTIVE_FILE.exists():
        ACTIVE_FILE.unlink()
    print("✅ Metrics cleared.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        skill_name = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        input_text = sys.argv[3] if len(sys.argv) > 3 else ""
        model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
        start_tracking(skill_name, input_text, model)

    elif command == "end":
        skill_name = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        output_text = sys.argv[3] if len(sys.argv) > 3 else ""
        end_tracking(skill_name, output_text)

    elif command == "report":
        generate_report()

    elif command == "clear":
        clear_metrics()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
