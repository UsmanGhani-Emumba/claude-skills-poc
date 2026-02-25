# Skills POC — Summary

A proof-of-concept for building reusable, multi-skill AI pipelines in both **Claude Code** and **Gemini CLI**. The same four skills and pipeline were implemented on each platform to compare capabilities and surface limitations.

---

## What Was Built

### Skills (Both Platforms)

Four reusable skills were created under `.claude/skills/` and `.gemini/skills/` respectively:

| Skill | What It Does |
|-------|-------------|
| **Researcher** | Decomposes a topic into 4–6 subtopics, assigns research approaches (web, academic, code, docs, video), invokes specialist sub-agents in parallel, and synthesizes a structured research brief |
| **Writer** | Writes polished, publish-ready articles from a research brief or raw topic; handles revisions based on reviewer feedback |
| **Reviewer** | Scores content out of 10, detects AI writing patterns (dash overuse, robotic transitions, missing contractions), and issues an `APPROVED` or `NEEDS_REVISION` verdict |
| **Publisher** | Converts approved content to Notion-compatible JSON block types and pushes it via `run_publisher.py` through a 3-phase Notion API pipeline |

### Commands (Both Platforms)

Five commands were created under `.claude/commands/` and `.gemini/commands/` to act as thin entry points into the skills:

| Command | Action |
|---------|--------|
| `/research <topic>` | Invokes the Researcher skill |
| `/write <topic>` | Invokes the Writer skill |
| `/review <content>` | Invokes the Reviewer skill |
| `/publish <content>` | Invokes the Publisher skill |
| `/pipeline <topic>` | Chains all four skills end-to-end automatically |

The `/pipeline` command is the most powerful — it runs Research → Write → Review → (Revise if needed) → Publish in a single invocation.

### Hooks & Tracing (Both Platforms)

Both platforms were configured with always-on hook logging and on-demand stream-JSON tracing:

- **Hook logging** fires on every tool call and writes structured JSONL files to `traces/`
- **Stream tracing** captures the full event stream (tokens, tool calls, results) via `trace-run.sh`
- **`analyze-trace.py`** provides CLI analysis of both trace types — tool call timelines, output previews, token usage, and cost

---

## Claude Code — Plus Points

### Invocation & Discoverability

- **Slash commands auto-registered** — any file placed in `.claude/commands/` immediately becomes a `/command` inside the CLI. No configuration, no file paths, no flags. Users type `/pipeline` and it works.
- **Skill auto-loading** — skills in `.claude/skills/` are automatically injected into context when a command references them. No explicit `@file` references needed.

### Agent & Execution Model

- **Native parallel sub-agents** — Claude has a first-class `Task` tool that spawns independent model invocations running simultaneously. The Researcher skill uses this to fire all `(subtopic, approach)` pairs in a single parallel batch. This is the single biggest capability advantage over Gemini.
- **True task decomposition** — sub-agents each get their own context window, tools, and result. The orchestrator collects all results and synthesizes them. This is genuine parallelism, not simulated role-playing.
- **Pipeline chaining** — the `/pipeline` command coordinates all four skills sequentially, passing full context from one step to the next, with the Reviewer verdict gating whether the Writer revises before publishing.

### Observability & Inspection

- **`/cost`** — shows total tokens, cost, and session duration at any point during an interactive run
- **`/context`** — visual grid showing how much of the context window is used by skills, conversation, and tools
- **`/export session.md` / `session.json`** — exports the full conversation in one command
- **`Ctrl+O`** — toggles verbose mode to see thinking and tool calls live as they happen
- **Stream-JSON cost data** — `--output-format stream-json` includes dollar cost and token breakdown per run (when using API key)

### Hooks

- **`PreToolUse` / `PostToolUse`** hooks in `settings.local.json` fire on every tool call with structured JSON payloads containing `session_id`, `tool_name`, `tool_input`, and `tool_output`
- **Granular permission controls** — `settings.local.json` supports fine-grained `allow`/`deny` rules per tool and per command pattern (e.g. `Bash(python:*)`)

---

## Gemini CLI — What Works

| Feature | Details |
|---------|---------|
| **Skills structure** | `.gemini/skills/<skill-name>/SKILL.md` pattern works; Gemini reads and follows skill instructions reliably |
| **Hooks** | `BeforeTool` / `AfterTool` hooks in `settings.json` fire on every tool call, producing the same JSONL audit trail |
| **Stream-JSON tracing** | `gemini --output_format stream-json` captures the full event stream including API latency metrics |
| **Agent files** | `.gemini/agents/` defines named specialist agents (e.g. `web-researcher.md`) with scoped tool access that Gemini can reference when executing a skill |
| **Headless mode** | `gemini "..."` runs a full prompt non-interactively |
| **Debug mode** | `gemini --debug` provides verbose internal logging for troubleshooting |

---

## Gemini CLI — Limitations

### 1. No Native Sub-Agent Concept

Claude Code's `Task` tool spawns true parallel sub-agents — independent model invocations with their own context windows running simultaneously. The Researcher skill relies on this to parallelize all `(subtopic, approach)` pairs in one batch.

Gemini CLI has no equivalent. The `.gemini/agents/` folder provides named agent _definitions_, but Gemini does not spawn them as independent parallel processes. They are processed sequentially within the same context window, making the Researcher skill slower and less scalable.

**Workaround used:** `.gemini/agents/` files were created (`web-researcher.md`, `academic-researcher.md`, `code-researcher.md`, `docs-researcher.md`, `video-researcher.md`) as scoped role definitions, but true parallel execution is not achieved.

### 2. Commands Are Not Auto-Loaded as Slash Commands

In Claude Code, files in `.claude/commands/` are automatically registered as slash commands. In Gemini CLI, files in `.gemini/commands/` are **not** auto-registered — there is no `/command` shorthand. Users must use the explicit `@file` syntax every time:

```bash
# Claude Code — clean slash command
/pipeline Write about AI trends

# Gemini CLI — must use full file reference
@.gemini/commands/pipeline.md Write about AI trends
```

This makes commands less discoverable and more verbose to invoke.

### 3. No Built-In Interactive Session Commands

Claude Code ships with in-session inspection commands. Gemini has none:

| Capability | Claude Code | Gemini CLI |
|-----------|-------------|------------|
| Check token usage + cost | `/cost` | Not available |
| Inspect context window | `/context` | Not available |
| Export conversation | `/export session.md` | Not available |
| Live tool call visibility | `Ctrl+O` verbose mode | `--debug` flag (pre-run only) |

### 4. Hook Event Names Are Not Portable

Hook configs use different event names, so they cannot be shared between platforms:

| Event | Claude Code | Gemini CLI |
|-------|-------------|------------|
| Before tool runs | `PreToolUse` | `BeforeTool` |
| After tool runs | `PostToolUse` | `AfterTool` |

### 5. Token and Cost Data Omitted on Subscription Plans

Stream traces on both platforms only include token/cost data when using an API key. On subscription plans, Gemini's trace omits these fields entirely. Claude Code's `/cost` command still shows session-level usage under a subscription.

---

## Key Differences — Claude vs Gemini

| Area | Claude Code | Gemini CLI |
|------|-------------|------------|
| **Command invocation** | `/pipeline <topic>` — auto-registered slash command | `@.gemini/commands/pipeline.md <topic>` — explicit file reference required |
| **Sub-agents** | Native `Task` tool — true parallel independent invocations | No native support — `.gemini/agents/` are sequential role definitions in shared context |
| **Researcher skill execution** | Fires all subtopic/approach pairs simultaneously in one batch | Processes sub-agents one at a time in the same context window |
| **Skill loading** | Auto-injected into context when a command references the skill folder | Must be read explicitly via file path in the skill instructions |
| **Pipeline automation** | `/pipeline` chains all 4 skills with context passed automatically between steps | Same logic works but must be invoked as `@.gemini/commands/pipeline.md` |
| **Hook event names** | `PreToolUse` / `PostToolUse` | `BeforeTool` / `AfterTool` |
| **Hook config file** | `settings.local.json` (local, gitignored by default) | `settings.json` |
| **Permission model** | Fine-grained `allow`/`deny` per tool and command pattern | `allowAllCommands: true/false` — coarser control |
| **In-session inspection** | `/cost`, `/context`, `/export`, `Ctrl+O` | `--debug` flag only |
| **Stream tracing flag** | `--output-format stream-json` | `--output_format stream-json` (underscore) |
| **Headless invocation** | `claude -p "..."` | `gemini "..."` |
| **Cost data in traces** | Included when using API key; `/cost` available on subscription too | Only available with API key; omitted on subscription |

---

## Folder Structure

```
claude-code-skills-poc/
  claude_skills_folder/
    .claude/
      commands/            ← 5 slash commands (auto-registered as /research, /pipeline, etc.)
      skills/              ← researcher, writer, reviewer, publisher
      settings.local.json  ← PreToolUse/PostToolUse hooks + fine-grained permissions
    traces/                ← hook + stream trace output
    analyze-trace.py
    trace-run.sh

  gemini_skills_folder/
    .gemini/
      commands/            ← 5 command files (NOT auto-registered; must use @file syntax)
      skills/              ← researcher, writer, reviewer, publisher
      agents/              ← web, academic, code, docs, video researcher role definitions
      settings.json        ← BeforeTool/AfterTool hooks + tool config
    traces/                ← hook + stream trace output
    analyze-trace.py
    trace-run.sh
```
