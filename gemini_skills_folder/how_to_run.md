# How to Run — Tracing & Logging Guide

## Prerequisites

- Python 3.x installed (used by hooks for logging)
- Gemini CLI installed (`gemini` command available)
- Run all commands from the `gemini_skills_folder/` directory

---

## 1. Hooks Logging (Always-On, Automatic)

Hooks are configured in `.gemini/settings.json`. They fire on **every** tool call — no extra flags needed.

### How it works

- **BeforeTool hook** logs tool name + input before execution
- **AfterTool hook** logs tool name + input + output preview after execution
- Each session creates its own file: `traces/hooks-<session-id>.jsonl`

### Interactive mode

```bash
cd gemini_skills_folder
gemini
```

Then type any skill command:

```
@.gemini/commands/research.md How to remember things like a pro
@.gemini/commands/pipeline.md How to remember things like a pro
@.gemini/commands/write.md How to remember things like a pro
```

### Headless mode

```bash
cd gemini_skills_folder
gemini "@.gemini/commands/research.md How to remember things like a pro"
```

Both modes produce the same hook trace files.

---

## 2. Stream-JSON Tracing (On-Demand, Deep Trace)

Use this when you want a **full event stream** — every token, every tool call, every result — saved to a file.

### Use the convenience script

Run stream-json tracing — hooks fire automatically at the same time.

```bash
cd gemini_skills_folder
bash trace-run.sh "@.gemini/commands/research.md How to remember things like a pro"
```

```bash
cd gemini_skills_folder
bash trace-run.sh "@.gemini/commands/pipeline.md How to remember things like a pro"
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
- Token usage — input/output tokens from the `result` event's stats
- Latency — API latency metrics

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

## 6. Debug Mode

For extra verbose output during a run, use the `--debug` flag:

```bash
gemini --debug "/research How to remember things like a pro"
```

This shows additional internal logging from the Gemini CLI.

---
