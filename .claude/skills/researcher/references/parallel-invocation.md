# Parallel Sub-Agent Invocation Reference

This document provides examples of how to spawn parallel sub-agents for research tasks.

## Decision Process

Before spawning agents, evaluate each sub-topic:

```
For each sub-topic, ask:
├── Are there official docs/URLs to fetch? → WebFetch agent
├── Do we need articles/tutorials/comparisons? → WebSearch agent
└── Do we need GitHub repo data (stars, issues)? → Bash (gh) agent
```

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

| Sub-topic | WebSearch | WebFetch | Bash (gh) | Total |
|-----------|-----------|----------|-----------|-------|
| AI Diagnostics | Yes (articles) | Yes (FDA docs) | No | 2 |
| Drug Discovery | Yes (articles) | Yes (research papers) | No | 2 |
| Administrative AI | Yes (articles) | No | No | 1 |
| Patient Care | Yes (articles) | Yes (medical guidelines) | No | 2 |
| Regulatory | Yes (articles) | Yes (FDA/WHO docs) | No | 2 |

**Total: 9 agents** (not 5!)

### Step 3: Spawn All Agents in ONE Message

```
Agent 1: WebSearch "AI Diagnostics & Medical Imaging"
Agent 2: WebFetch FDA AI guidance documents
Agent 3: WebSearch "Drug Discovery AI"
Agent 4: WebFetch research paper URLs
Agent 5: WebSearch "Administrative AI Healthcare"
Agent 6: WebSearch "Patient Care AI Monitoring"
Agent 7: WebFetch medical guidelines URLs
Agent 8: WebSearch "AI Healthcare Regulations"
Agent 9: WebFetch FDA/WHO regulatory documents
```

## Common Mistakes

| Approach | Agents | Quality |
|----------|--------|---------|
| Wrong: 1 WebSearch per sub-topic | 5 | Low - misses official docs |
| Correct: Tool-based per sub-topic | 9+ | High - comprehensive coverage |

## Key Principle

**More agents = better coverage.** Parallel execution means no time penalty for thoroughness. Never compromise research quality to reduce agent count.
