---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples before writing. Triggers on requests like "research [topic]", "find information about", "gather facts on", or as the first step in content creation pipelines.
---

# Researcher Skill

## Purpose

Gather comprehensive, accurate information on a topic to serve as the foundation for content creation. Uses **parallel sub-agents** to research multiple sub-topics simultaneously for faster, more thorough research.

---

## Core Principle: Quality Over Agent Count

**NEVER compromise research quality to reduce the number of agents.**

Parallel sub-agents exist to **maximize quality while saving time** - not to minimize agent usage. Always spawn all necessary agents for comprehensive coverage.

**Rules:**
1. Always evaluate which tools each sub-topic requires (WebSearch, WebFetch, Bash)
2. Spawn separate agents per tool type when a sub-topic needs multiple tools
3. More agents = better coverage (parallel execution means no time penalty)

See [Parallel Invocation Reference](references/parallel-invocation.md) for decision process and examples.

---

## Workflow

### Phase 1: Topic Analysis

1. **Clarify scope** - Identify the core topic and any specific angles requested
2. **Break down into sub-topics** - Identify 3-6 distinct sub-topics that together provide comprehensive coverage:
   - Core concept/definition
   - Historical context or background
   - Current state/trends
   - Key players/stakeholders
   - Challenges/problems
   - Future outlook/predictions
   - Practical applications

### Phase 2: Parallel Sub-Agent Research

3. **Evaluate tools per sub-topic** - For each sub-topic, determine which tools are needed:
   - WebFetch: Known documentation URLs, official sources
   - WebSearch: Articles, tutorials, comparisons
   - Bash (gh CLI): GitHub repository data, stats

4. **Spawn parallel research agents** - Use the Task tool to launch multiple sub-agents simultaneously:

```
For each sub-topic, use the Task tool with:
- subagent_type: "general-purpose"
- run_in_background: false (to get results back)
- Launch ALL sub-agents in a SINGLE message for true parallelism
```

**Sub-agent prompt template:**
```
Research the following sub-topic thoroughly for a blog post:

Main Topic: [MAIN_TOPIC]
Sub-topic: [SUB_TOPIC]

Perform 2-3 targeted web searches to gather:
- Key facts and definitions
- Recent developments (2024-2025)
- Statistics or data points with sources
- Expert perspectives or quotes

Return your findings in this format:

## [SUB_TOPIC]

### Key Findings
- Finding 1 (Source: ...)
- Finding 2 (Source: ...)

### Statistics
- Stat 1 (Source, Year)

### Sources
- [Source Title 1](URL)
- [Source Title 2](URL)
```

See [Tool-Based Research Reference](references/tool-based-research.md) for tool-specific prompt templates.

### Phase 3: Compilation

5. **Compile all sub-agent results** - Gather outputs from all parallel agents
6. **Synthesize into unified brief** - Merge findings, remove duplicates, organize coherently
7. **Add cross-cutting insights** - Identify connections between sub-topics

---

## Output Format

Produce a structured research brief:

```markdown
# Research Brief: [Topic]

## Executive Summary
Brief overview synthesizing all sub-topic research (2-3 sentences)

## Sub-Topics Researched
1. [Sub-topic 1]
2. [Sub-topic 2]
3. [Sub-topic 3]

---

## [Sub-topic 1 Name]

### Key Facts
- Fact 1 (Source: ...)
- Fact 2 (Source: ...)

### Statistics & Data
- Stat 1 (Source, Year)

### Recent Developments
- Development 1 (Date, Source)

---

## [Sub-topic 2 Name]
[Same structure...]

---

## Cross-Cutting Insights
- Connection between sub-topic 1 and 3
- Emerging pattern across all sub-topics

## Interesting Angles for Writing
- Angle worth exploring 1
- Angle worth exploring 2

## Sources
- [Source Title](URL) - Brief description
- [Source Title](URL) - Brief description
```

**Note:** Format sources as a bulleted list with URLs. The Reviewer skill validates source formatting.

---

## References

- [Quality Criteria](references/quality-criteria.md) - Standards for research output
- [Tool-Based Research](references/tool-based-research.md) - Implementation details and prompt templates
- [Parallel Invocation](references/parallel-invocation.md) - Examples of spawning parallel agents
- [Sample Output](references/sample-output.md) - Complete example of expected output
