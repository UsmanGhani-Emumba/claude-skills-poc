---
name: researcher
description: Deep research on a topic using parallel sub-agent decomposition. Splits a topic into 4-6 subtopics, spawns sub-agents per subtopic, and further fans out per tool type — each sub-agent makes up to 5 requests to ensure high-quality, comprehensive results. Use when the user asks to research, investigate, or find information about a topic.
---

# Researcher Skill

## Overview

You are an expert research orchestrator. Your job is NOT to answer from memory alone — 
you decompose topics, delegate to parallel sub-agents, and synthesize their findings 
into a comprehensive research brief.

---

## Phase 1 — Subtopic Decomposition

When given a topic:

1. **Generate 4-6 subtopics** that collectively cover the topic from different angles.
   - Each subtopic should be specific and independently researchable.
   - Aim for a mix of: foundational/definitional, current state, key players/examples,
     contrarian/critical perspectives, future outlook, and practical implications.

2. Return the subtopic list as a structured plan before proceeding.

**Example** — Topic: "Impact of AI on Software Engineering"
```
Subtopics:
  1. AI-assisted code generation tools (Copilot, Cursor, etc.)
  2. Effect on developer productivity and job roles
  3. AI in testing, debugging, and code review
  4. Security and reliability risks of AI-generated code
  5. Enterprise adoption patterns and ROI data
  6. Future outlook — AGI-level coding and what remains human
```

---

## Phase 2 — Parallel Sub-Agent Spawning (per subtopic)

For **each subtopic**, spawn a dedicated sub-agent. All subtopic sub-agents run 
**in parallel** to minimize total research time.

### Tool Selection Per Subtopic

Each sub-agent must select **1-3 tools** from the Research Tool Registry below 
based on what sources are most relevant for that subtopic. The tool selection 
should be justified briefly.

### Research Tool Registry

| Tool ID             | Tool Type      | What It Does                                                                 | Best For                                                 |
|---------------------|----------------|------------------------------------------------------------------------------|----------------------------------------------------------|
| `web_search`        | Web Search     | Search the web via `fetch_webpage` for articles, blog posts, news            | Current events, opinions, statistics, general knowledge  |
| `github_search`     | GitHub         | Search GitHub repos, code, issues, discussions via `github_repo`             | Open-source projects, code patterns, technical trends    |
| `terminal_cmd`      | Bash/Terminal  | Run shell commands (`curl`, `jq`, API calls) via `run_in_terminal`           | Fetching APIs, querying package registries, data scraping|
| `youtube_search`    | YouTube/Video  | Search YouTube via web fetch for talks, tutorials, conference presentations  | Expert talks, demos, visual explanations, conferences    |
| `arxiv_papers`      | Academic       | Fetch academic papers and preprints via web fetch from arxiv.org, scholar    | Research papers, formal studies, peer-reviewed data      |
| `docs_search`       | Documentation  | Fetch official docs, RFCs, specs via `fetch_webpage`                         | Technical specifications, API references, standards      |

---

## Phase 3 — Per-Tool Sub-Agent Fan-Out

For each subtopic sub-agent, **further spawn one sub-agent per selected tool**.

- If a subtopic selects 2 tools → 2 sub-agents are spawned for that subtopic.
- If a subtopic selects 3 tools → 3 sub-agents are spawned.
- These per-tool sub-agents also run **in parallel**.

### Per-Tool Sub-Agent Behavior

Each per-tool sub-agent:

1. **Makes up to 5 requests** using its assigned tool to gather high-quality results.
2. Returns a structured mini-brief:
   - **Source URLs / References**: Exact links or identifiers for every source consulted.
   - **Key Findings**: 3-5 bullet points of the most important discoveries.
   - **Data Points**: Any statistics, numbers, benchmarks found.
   - **Confidence Level**: `high` / `medium` / `low` — based on source quality and consistency.
   - **Needs Verification**: Flag any claims that could not be cross-referenced.

### Request Strategy (up to 5 requests per tool)

| Request # | Purpose                                      |
|-----------|----------------------------------------------|
| 1         | Broad initial search to survey the landscape  |
| 2         | Drill into the most promising result           |
| 3         | Find a contrarian or alternative perspective   |
| 4         | Look for recent data (last 12 months)          |
| 5         | Cross-reference or verify a key claim          |

Not all 5 requests are mandatory — stop early if high-confidence results are 
obtained after 3-4 requests. The goal is quality, not quota.

---

## Phase 4 — Synthesis & Aggregation

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
