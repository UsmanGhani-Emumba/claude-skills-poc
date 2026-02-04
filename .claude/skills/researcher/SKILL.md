---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples before writing. Triggers on requests like "research [topic]", "find information about", "gather facts on", or as the first step in content creation pipelines.
---

# Researcher Skill

## Purpose

Gather comprehensive, accurate information on a topic to serve as the foundation for content creation. Uses **parallel sub-agents** to research multiple sub-topics simultaneously for faster, more thorough research.

## Workflow

### Phase 1: Topic Analysis & Sub-topic Identification

1. **Clarify scope** - Identify the core topic and any specific angles requested
2. **Break down into sub-topics** - Analyze the main topic and identify 3-6 distinct sub-topics that together provide comprehensive coverage. Consider:
   - Core concept/definition
   - Historical context or background
   - Current state/trends
   - Key players/stakeholders
   - Challenges/problems
   - Future outlook/predictions
   - Practical applications

### Phase 2: Parallel Sub-Agent Research

3. **Spawn parallel research agents** - Use the Task tool to launch multiple sub-agents simultaneously, one for each sub-topic:

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
- [Source Title 3](URL)
```

⚠️ **IMPORTANT: Sources must be formatted as a BULLETED LIST, one per line. NEVER use inline comma-separated format.**

### Phase 3: Compilation

4. **Compile all sub-agent results** - Gather outputs from all parallel agents
5. **Synthesize into unified brief** - Merge findings, remove duplicates, organize coherently
6. **Add cross-cutting insights** - Identify connections between sub-topics

## Output Format

Produce a structured research brief with sub-topic sections:

```markdown
# Research Brief: [Topic]

## Executive Summary
Brief overview synthesizing all sub-topic research (2-3 sentences)

## Sub-Topics Researched
1. [Sub-topic 1]
2. [Sub-topic 2]
3. [Sub-topic 3]
...

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

⚠️ **Note:** Format sources as a bulleted list with URLs. The Reviewer skill validates source formatting.

## Example: Parallel Sub-Agent Invocation

When researching "AI in Healthcare":

```
Identified Sub-topics:
1. AI Diagnostics & Medical Imaging
2. Drug Discovery & Development
3. Administrative & Operational AI
4. Patient Care & Monitoring
5. Regulatory & Ethical Considerations

Then spawn 5 parallel Task agents in ONE message:
- Agent 1: Research "AI Diagnostics & Medical Imaging"
- Agent 2: Research "Drug Discovery & Development"
- Agent 3: Research "Administrative & Operational AI"
- Agent 4: Research "Patient Care & Monitoring"
- Agent 5: Research "Regulatory & Ethical Considerations"
```

## Advanced: Tool-Based Parallel Research

Use tool-based parallelization when a sub-topic requires **more than one tool** to gather information. Each sub-topic spawns **one agent per tool type needed**, determined dynamically.

### When to Use Tool-Based Mode

Use Tool-Based Mode for any sub-topic that needs multiple tools:

```
Sub-topic needs:
├── Only WebSearch → Standard Mode (1 agent)
├── WebFetch + WebSearch → Tool-Based Mode (2 agents)
├── WebSearch + Bash (gh) → Tool-Based Mode (2 agents)
└── WebFetch + WebSearch + Bash → Tool-Based Mode (3 agents)
```

**Rule: If a sub-topic requires 2+ tools → spawn separate agents per tool**

### Dynamic Tool Selection

**The number of agents per sub-topic depends on which tools are relevant:**

```
For each sub-topic, ask:
├── Are there known documentation URLs to fetch? → Add WebFetch agent
├── Do we need to search for articles/tutorials? → Add WebSearch agent
└── Do we need GitHub repo data (stars, issues)? → Add Bash (gh) agent

Agents per sub-topic = Count of relevant tools (1, 2, or 3)
Total agents = Sum of tools needed across all sub-topics
```

### Reference

For detailed implementation, templates, and examples, see [references/tool-based-research.md](references/tool-based-research.md)

## References

- [Quality Criteria](references/quality-criteria.md) - Standards for research output
- [Tool-Based Research](references/tool-based-research.md) - Implementation details and templates
- [Sample Output](references/sample-output.md) - Complete example of expected output