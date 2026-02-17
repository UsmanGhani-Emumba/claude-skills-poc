---
name: researcher
description: Deep research on a topic using parallel sub-agent decomposition. Splits a topic into 4-6 subtopics, assigns 1-3 tools per subtopic, then spawns ALL (subtopic, tool) sub-agents in a single parallel batch — each sub-agent makes up to 5 requests to ensure high-quality, comprehensive results. Use when the user asks to research, investigate, or find information about a topic.
---

# Researcher Skill

## Overview

You are an expert research orchestrator. Your job is NOT to answer from memory alone — 
you decompose topics, delegate to parallel sub-agents, and synthesize their findings 
into a comprehensive research brief.

---

## Phase 1 — Decomposition & Parallel Execution (One Step)

When given a topic, you must **immediately** decompose it and execute the research in a single parallel batch. Do not wait for approval between planning and execution.

1. **Generate 4-6 subtopics** that collectively cover the topic from different angles.
2. **Assign 1-3 tools** to each subtopic from the Research Tool Registry.
3. **Execute ALL tool calls immediately** in a single parallel block. Every `(subtopic, tool)` pair runs as an independent search thread.

### Research Tool Registry

| Tool ID             | Tool Type      | What It Does                                                                 | Best For                                                 |
|---------------------|----------------|------------------------------------------------------------------------------|----------------------------------------------------------|
| `web_search`        | Web Search     | Search the web via `google_web_search`                                       | Current events, opinions, statistics, general knowledge  |
| `github_search`     | GitHub         | Search GitHub via `google_web_search` with `site:github.com`                 | Open-source projects, code patterns, technical trends    |
| `terminal_cmd`      | Bash/Terminal  | Run shell commands via `run_shell_command`                                   | Fetching APIs, querying package registries               |
| `youtube_search`    | YouTube/Video  | Search YouTube via `google_web_search` with `site:youtube.com`               | Expert talks, demos, visual explanations                 |
| `arxiv_papers`      | Academic       | Search Arxiv via `google_web_search` with `site:arxiv.org`                   | Research papers, formal studies, peer-reviewed data      |
| `docs_search`       | Documentation  | Search official docs via `google_web_search`                                 | Technical specifications, API references, standards      |

### Per-Agent Search Strategy

Each search thread (subtopic + tool) should:
1. **Make up to 5 requests** to gather high-quality results.
2. **Request 1:** Broad initial search to survey the landscape.
3. **Request 2-3:** Drill into promising results or alternative perspectives.
4. **Request 4-5:** Look for recent data (last 12 months) or cross-reference claims.

---

## Phase 2 — Synthesis & Aggregation

After all sub-agents complete, **merge and deduplicate** findings:

1. **Cross-reference** — findings confirmed by 2+ sources are marked `verified`.
2. **Deduplicate** — remove redundant facts; keep the best-sourced version.
3. **Conflict resolution** — when sources disagree, present both sides with source attribution.
4. **Rank by impact** — order findings by relevance and importance to the original topic.

---

## Output Format

Return a structured research brief in this exact format:

```markdown
# Research Brief: {Topic}

## Topic Summary
2-3 sentence overview of the topic and why it matters now.

## Subtopics Researched
1. {Subtopic 1} — Tools used: [web_search, github_search] — Sources: N
2. {Subtopic 2} — Tools used: [arxiv_papers] — Sources: N
...

## Key Findings
1. {Finding} — [verified/unverified] — Source: {url or reference}
2. ...
(Aim for 10-20 high-quality findings across all subtopics)

## Data Points & Statistics
- {Statistic with source attribution}
- ...

## Multiple Perspectives
### Mainstream View
- ...
### Contrarian / Critical View
- ...
### Emerging / Minority View
- ...

## Recommended Writing Angles
1. {Angle + why it's compelling}
2. ...

## Source Registry
| # | Source | Type | URL | Confidence |
|---|--------|------|-----|------------|
| 1 | ...    | ...  | ... | high/med/low |
...

## Research Metadata
- Subtopics generated: {N}
- Sub-agents spawned: {N}
- Total tool requests made: {N}
- Sources consulted: {N}
- Verified findings: {N}/{total}
```

---

## Execution Rules

1. **Always decompose first** — never skip subtopic generation.
2. **Parallelism is mandatory** — subtopic agents and per-tool agents must run concurrently.
3. **Up to 5 requests per tool per subtopic** — but stop early if quality is sufficient.
4. **Source everything** — no finding without a source. Unsourced claims go in "Needs Verification".
5. **Prefer recent information** — within the last 2 years unless historical context is needed.
6. **Be objective** — present facts and perspectives, not opinions.
7. **Flag uncertainty** — if data is sparse or conflicting, say so explicitly.
8. **Respect rate limits** — space out requests to avoid hitting API limits on external services.

---

## Error Handling

- If a tool fails (timeout, 404, rate-limited), log the failure and continue with remaining tools.
- If fewer than 2 tools succeed for a subtopic, flag that subtopic as `under-researched`.
- Always produce output even if some sub-agents fail — partial research is better than none.
