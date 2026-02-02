---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples before writing. Triggers on requests like "research [topic]", "find information about", "gather facts on", or as the first step in content creation pipelines.
---

# Researcher Skill

## Purpose

Gather comprehensive, accurate information on a topic to serve as the foundation for content creation.

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

## Output Format

Produce a structured research brief:

```markdown
# Research Brief: [Topic]

## Key Facts
- Fact 1 (Source: ...)
- Fact 2 (Source: ...)
- Fact 3 (Source: ...)

## Recent Developments
- Development 1 (Date, Source)
- Development 2 (Date, Source)

## Statistics & Data
- Stat 1 (Source, Year)
- Stat 2 (Source, Year)

## Interesting Angles
- Angle worth exploring 1
- Angle worth exploring 2

## Sources
1. [Title](URL) - Brief description
2. [Title](URL) - Brief description
```

## Quality Criteria

- Minimum 5 distinct, credible sources
- Include at least 2 statistics or data points
- Prioritize recent information (last 1-2 years when relevant)
- Flag any conflicting information found
- Note gaps where information was not found

## Reference

For a complete example of expected output, see [references/sample-output.md](references/sample-output.md)