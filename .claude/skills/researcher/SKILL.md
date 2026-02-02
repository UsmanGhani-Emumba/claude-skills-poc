---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples before writing. Triggers on requests like "research [topic]", "find information about", "gather facts on", or as the first step in content creation pipelines.
---

# Researcher Skill

## Purpose

Gather comprehensive, accurate information on a topic to serve as the foundation for content creation. Uses **parallel sub-agents** to research multiple sub-topics simultaneously for faster, more thorough research.

## Metrics Tracking

**At skill START**, run:
```bash
python metrics/tracker.py start researcher "<user_query>"
```

**At skill END**, run:
```bash
python metrics/tracker.py end researcher "<final_output>"
```

This tracks latency, token usage, and cost. View reports with: `python metrics/tracker.py report`

## Workflow

1. **Start metrics tracking** - Run the start command above with the user's query
2. **Clarify scope** - Identify the core topic and any specific angles requested
2. **Search strategically** - Use 3-5 targeted searches covering:
   - Core concept/definition
   - Recent developments (include current year)
   - Statistics or data points
   - Expert perspectives or quotes
3. **Extract and organize** - Pull out key facts, citing sources
4. **Compile research brief** - Structure findings for the Writer skill
5. **End metrics tracking** - Run the end command with the complete research brief output

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

**IMPORTANT: Always format sources as a bulleted list, one source per line. NEVER use inline comma-separated format.**

- [Source Title 1](https://example.com/1) - Brief description
- [Source Title 2](https://example.com/2) - Brief description
- [Source Title 3](https://example.com/3) - Brief description
- [Source Title 4](https://example.com/4) - Brief description
```

## Source Formatting Rules

⚠️ **CRITICAL: Sources must ALWAYS be formatted as a bulleted markdown list.**

### ✅ CORRECT Format (Bulleted List):
```
Sources:
- [Gartner AI Predictions](https://gartner.com/...)
- [Anthropic Agent Skills](https://anthropic.com/...)
- [LangChain Multi-Agent Architecture](https://langchain.com/...)
```

### ❌ WRONG Format (Inline Comma-Separated):
```
Sources: Gartner AI Predictions, Anthropic Agent Skills, LangChain Multi-Agent Architecture
```

The bulleted list format is required because:
1. Each source is clearly distinguishable
2. URLs are properly clickable
3. Easier to scan and reference
4. Consistent with markdown best practices

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

## Quality Criteria

- Minimum 3 sub-topics researched in parallel
- Each sub-topic has at least 2 distinct sources
- Total of 8+ distinct, credible sources across all sub-topics
- Include statistics/data in at least 3 sub-topics
- Prioritize recent information (last 1-2 years when relevant)
- Flag any conflicting information found across sub-topics
- Note gaps where information was not found
- Identify at least 2 cross-cutting insights

## Reference

For a complete example of expected output, see [references/sample-output.md](references/sample-output.md)