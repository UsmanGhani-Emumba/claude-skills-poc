# Parallel Instrumented Sub-Agent Invocation Reference

This document provides examples of how to spawn parallel sub-agents using the instrumented Python agent (`scripts/arize_agent.py`) with full Arize observability.

## Decision Process

Before spawning agents, evaluate each sub-topic:

```
For each sub-topic, ask:
├── Are there official docs/URLs to fetch? → web_fetch agent
├── Do we need articles/tutorials/comparisons? → web_search agent
└── Do we need GitHub repo data (stars, issues)? → github_cli agent
```

## Workflow: Write Tasks → Spawn Agents

### Step 1: Write task prompt files

Use the Write tool to create a task file for each agent:

```
.claude/logs/tasks/1a.txt  →  "Research AI Diagnostics using web search..."
.claude/logs/tasks/1b.txt  →  "Fetch FDA AI guidance documents from..."
.claude/logs/tasks/2a.txt  →  "Search for Drug Discovery AI articles..."
```

### Step 2: Launch ALL agents in ONE message

Use multiple Bash calls in a **single message** for true parallelism:

```
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1a.txt --tools web_search --agent-id 1a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_fetch  --agent-id 1b --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/2a.txt --tools web_search --agent-id 2a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/3a.txt --tools web_search --agent-id 3a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/3b.txt --tools github_cli --agent-id 3b --skill researcher
```

Each Bash call runs independently. All agents execute in parallel.

### Step 3: Parse JSON outputs

Each agent outputs JSON to stdout:

```json
{
  "result": "## AI Diagnostics\n\n### Key Findings\n- Finding 1...",
  "metrics": {
    "agent_id": "1a",
    "skill": "researcher",
    "model": "claude-sonnet-4-5-20250929",
    "input_tokens": 2100,
    "output_tokens": 450,
    "cost_usd": 0.0138,
    "latency_seconds": 8.2,
    "distinct_tools_count": 1,
    "tools_used": ["web_search"],
    "tool_calls_count": 3,
    "api_calls": 1,
    "context_tokens": 2100,
    "timestamp": "2025-06-15T10:30:00Z"
  }
}
```

Extract `result` for research compilation and `metrics` for the summary table.

## Example: AI in Healthcare

### Step 1: Identify Sub-topics

```
Identified Sub-topics:
1. AI Diagnostics & Medical Imaging
2. Drug Discovery & Development
3. Administrative & Operational AI
4. Patient Care & Monitoring
5. Regulatory & Ethical Considerations
```

### Step 2: Evaluate Tools Per Sub-topic

| Sub-topic | web_search | web_fetch | github_cli | Total |
|-----------|-----------|----------|-----------|-------|
| AI Diagnostics | Yes (articles) | Yes (FDA docs) | No | 2 |
| Drug Discovery | Yes (articles) | Yes (research papers) | No | 2 |
| Administrative AI | Yes (articles) | No | No | 1 |
| Patient Care | Yes (articles) | Yes (medical guidelines) | No | 2 |
| Regulatory | Yes (articles) | Yes (FDA/WHO docs) | No | 2 |

**Total: 9 agents** (not 5!)

### Step 3: Write Task Files & Spawn All Agents

Write 9 task files, then launch 9 Bash calls in ONE message:

```
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1a.txt --tools web_search --agent-id 1a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_fetch  --agent-id 1b --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/2a.txt --tools web_search --agent-id 2a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/2b.txt --tools web_fetch  --agent-id 2b --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/3a.txt --tools web_search --agent-id 3a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/4a.txt --tools web_search --agent-id 4a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/4b.txt --tools web_fetch  --agent-id 4b --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/5a.txt --tools web_search --agent-id 5a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/5b.txt --tools web_fetch  --agent-id 5b --skill researcher
```

### Step 4: Aggregate Metrics

After all agents complete, build the metrics table from their JSON outputs:

```markdown
## Research Metrics

| Agent | Tool | Input Tokens | Output Tokens | Cost | Latency |
|-------|------|-------------|---------------|------|---------|
| 1a | web_search | 2,100 | 450 | $0.0138 | 8.2s |
| 1b | web_fetch | 3,200 | 600 | $0.0186 | 12.1s |
| 2a | web_search | 1,800 | 380 | $0.0111 | 7.5s |
| ... | ... | ... | ... | ... | ... |
| **Total** | | **22,400** | **4,200** | **$0.1302** | **9.1s avg** |

- **Sub-agents spawned:** 9
- **Distinct tools used:** 2 (web_search, web_fetch)
```

## Common Mistakes

| Approach | Agents | Quality | Observability |
|----------|--------|---------|---------------|
| Wrong: 1 web_search per sub-topic | 5 | Low - misses official docs | Partial |
| Correct: Tool-based per sub-topic | 9+ | High - comprehensive coverage | Full per-agent |

## Key Principles

1. **More agents = better coverage** — parallel execution means no time penalty for thoroughness
2. **Every agent is instrumented** — tokens, cost, latency tracked automatically via Arize
3. **Metrics logged locally AND to Arize** — `.claude/logs/arize_metrics.jsonl` always has the data
4. **View aggregated metrics** — run `python scripts/metrics_summary.py --detail` after research
