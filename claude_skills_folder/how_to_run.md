# How to Run — Tracing & Logging Guide

## Prerequisites

- Python 3.x installed (used by hooks for logging)
- Claude Code CLI installed (`claude` command available)
- Run all commands from the `claude_skills_folder/` directory

---

## 1. Hooks Logging (Always-On, Automatic)

Hooks are configured in `.claude/settings.local.json`. They fire on **every** tool call — no extra flags needed.

### How it works

- **PreToolUse hook** logs tool name + input before execution
- **PostToolUse hook** logs tool name + input + output preview after execution
- Each session creates its own file: `traces/hooks-<session-id>.jsonl`

### Interactive mode

```bash
cd claude_skills_folder
claude
```

Then type any skill command:

```
/research How to remember things like a pro
/pipeline Write about AI trends
/write Draft a blog post about productivity
```

### Headless mode

```bash
cd claude_skills_folder
claude -p "/research How to remember things like a pro"
```

Both modes produce the same hook trace files.

---

## 2. Stream-JSON Tracing (On-Demand, Deep Trace)

Use this when you want a **full event stream** — every token, every tool call, every result — saved to a file.

> **Note:** Token counts and cost data only appear when using an API key. On Pro subscription, these fields show 0. Hooks work the same on both.

### Use the convenience script

```bash
cd claude_skills_folder
bash trace-run.sh "/research How to remember things like a pro"
```

This creates a timestamped trace file like `traces/20260220-134500-stream.jsonl`.

### Or run manually

```bash
cd claude_skills_folder
claude -p "/research How to remember things like a pro" \
    --output-format stream-json \
    --verbose \
    | tee traces/my-trace.jsonl
```

---

## 3. Both Together (Recommended)

Run stream-json tracing — hooks fire automatically at the same time.

```bash
cd claude_skills_folder
bash trace-run.sh "/pipeline Write about AI trends"
```

After the run, you'll have two new files:

| File | What it contains |
|------|-----------------|
| `traces/<timestamp>-stream.jsonl` | Full event stream (tokens, tool calls, results) |
| `traces/hooks-<session-id>.jsonl` | Clean tool-only audit trail (one per session) |

---

## 4. Analyze Traces

```bash
# List all trace files (hooks + stream)
python analyze-trace.py

# --- Hooks ---
python analyze-trace.py hooks                                    # List all hook files
python analyze-trace.py hooks latest                             # Most recent session
python analyze-trace.py hooks traces/hooks-a1b2c3d4.jsonl        # Specific file
python analyze-trace.py latest                                   # Shortcut for hooks latest

# --- Stream ---
python analyze-trace.py stream                                   # List all stream files
python analyze-trace.py stream latest                            # Most recent stream
python analyze-trace.py stream traces/20260220-stream.jsonl      # Specific file

# --- Both ---
python analyze-trace.py both latest                              # Latest of each
python analyze-trace.py both <hook-file> <stream-file>           # Specific files
```

### What the analysis shows

**Hooks analysis:**
- Tool call counts — which tools were used and how many times
- Timeline — chronological sequence with `>>` (pre) and `<<` (post) markers
- Output previews — first 80 chars of each tool's result

**Stream analysis:**
- Event type breakdown — all stream event types and counts
- Tool call summary — tools used and frequency
- Token usage — input/output tokens (API key only, shows 0 on Pro)
- Cost — dollar cost of the run (API key only)

---

## 5. Clear Traces

```bash
# Delete all traces
rm traces/hooks-*.jsonl traces/*-stream.jsonl

# Delete hook traces only
rm traces/hooks-*.jsonl

# Delete stream traces only
rm traces/*-stream.jsonl
```

---

## 6. Interactive Session Commands (Bonus)

While inside an interactive `claude` session, you can also use:

| Command | What it shows |
|---------|--------------|
| `Ctrl+O` | Toggle verbose mode — see thinking + tool calls live |
| `/cost` | Total tokens, cost, and duration for the session |
| `/context` | Visual grid of context usage (skills, conversation, tools) |
| `/export session.json` | Export full conversation as JSON |
| `/export session.md` | Export full conversation as Markdown |

---

## File Structure

```
claude_skills_folder/
├── .claude/
│   ├── settings.local.json    ← hooks config lives here
│   ├── commands/              ← slash commands (/research, /write, etc.)
│   └── skills/                ← skill definitions (SKILL.md files)
├── traces/                    ← all trace output goes here
│   ├── hooks-<session>.jsonl  ← one per session (auto-created by hooks)
│   └── *-stream.jsonl         ← one per trace-run invocation
├── trace-run.sh               ← convenience script for stream-json runs
├── analyze-trace.py           ← trace analysis tool
└── how_to_run.md              ← this file
```
