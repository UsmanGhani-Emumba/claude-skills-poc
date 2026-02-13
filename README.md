# Orchestrator Agent

A content pipeline agent that manages specialized AI skills using the Anthropic API with Claude Opus 4.6. The orchestrator intelligently routes user prompts to individual skills or executes the full pipeline, with all invocations traced via Arize Phoenix.

## Pipeline

```
User Prompt → Intent Detection → Skill Routing
                                      │
        ┌─────────────┬───────────────┼───────────────┬──────────────┐
        ▼             ▼               ▼               ▼              ▼
   Researcher      Writer         Reviewer        Publisher     Full Pipeline
   (research)     (draft)         (review)       (Notion)      (all skills)
```

**Full Pipeline Flow:**
```
Researcher → Writer → Reviewer → Writer (revision if needed) → Publisher (Notion)
```

## Skills

| Skill | Purpose | Trigger Keywords |
|-------|---------|-----------------|
| **Researcher** | Gathers facts, statistics, multiple perspectives | "research", "find info", "investigate" |
| **Writer** | Produces polished articles, handles revisions | "write", "draft", "compose" |
| **Reviewer** | Evaluates quality, returns APPROVED/NEEDS_REVISION | "review", "edit", "feedback" |
| **Publisher** | Formats and publishes to Notion via MCP | "publish", "post to Notion" |

## Project Structure

```
.claude/
  agents/orchestrator.md          # Orchestrator subagent definition
  skills/
    base.py                       # Shared base skill class
    researcher/
      SKILL.md                    # Skill prompt definition
      references/researcher.py    # Python implementation
    writer/
      SKILL.md
      references/writer.py
    reviewer/
      SKILL.md
      references/reviewer.py
    publisher/
      SKILL.md
      references/publisher.py
      scripts/notion_publish.py   # Standalone Notion publishing script
  commands/                       # Slash commands (/research, /write, /review, /publish, /pipeline)
src/
  main.py                         # CLI entry point
  config.py                       # Environment configuration
  orchestrator/
    agent.py                      # Core orchestrator logic
    intent.py                     # Intent classification
    pipeline.py                   # Full pipeline execution
  observability/
    tracer.py                     # Arize Phoenix setup
    metrics.py                    # Token/cost/latency tracking
  mcp/
    notion_client.py              # MCP client for Notion
tests/                            # Unit tests
```

## Stack

- **Python 3.11+**
- **Anthropic SDK** with Claude Opus 4.6 (`claude-opus-4-6`)
- **Arize Phoenix** for observability (traces at http://localhost:6006)
- **OpenTelemetry** for instrumentation
- **MCP** for Notion publishing
- **Rich** for CLI output

## Observability

Every skill invocation is auto-traced. After execution, the agent displays:

- Input/output tokens per skill
- Latency per skill
- Cost per skill
- Total pipeline metrics

View detailed traces at the Phoenix dashboard: http://localhost:6006
