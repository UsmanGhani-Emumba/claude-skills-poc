---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples.
---

# Researcher Skill

## Purpose
Gather comprehensive, accurate information on a topic using available tools to provide a high-quality research brief.

## Workflow
1. **Analyze Topic**: Break down the main topic into **5-6 independent sub-topics**.
2. **Assign Agents (Parallel Strategy)**:
   - **One Agent per Tool Type**: If a sub-topic needs `web_search` and `github_cli`, spawn separate parallel agents for each.
   - **Maximize Quality**: Spawn as many agents as necessary to cover all sub-topics and tools simultaneously.
3. **Execute Research**: Use the `browser_subagent` tool to spawn all necessary sub-agents in a single parallel batch (`waitForPreviousTools: false`).
4. **Compile Brief**: Synthesize all findings into a unified, structured research brief.

## Available Tools
- `web_search`: Core discovery tool (built-in).
- `web_fetch`: Programmatic content extraction ([web_fetch.py](references/web_fetch.py)).
- `bash`: Generic terminal command execution (built-in).
- `github_cli`: Repository and community data wrapper ([github_cli.py](references/github_cli.py)).

## Research Strategy
Refer to the **[Search Strategy](references/search_strategy.md)** for best practices on combining these tools for high-quality findings.

## Quality Standards
- **Depth**: Find specific facts and statistics, not just general summaries.
- **Multitool Usage**: If a sub-topic needs GitHub data AND documentation, use both `github_cli` and `web_fetch`.
- **Sources**: Every key fact must be attributed to a source URL.

## Output Format: Research Brief
Return a structured markdown document containing:
1. **Executive Summary**: 2-3 sentence overview.
2. **Sub-Topic Sections**: Structured facts and data for each of the 5-6 sub-topics.
3. **Cross-Cutting Insights**: Connections found between different areas.
4. **Sources**: A bulleted list of all URLs referenced.

---

## References
- [Quality Criteria](references/quality-criteria.md) - Standards for research output
- [Tool-Based Research](references/tool-based-research.md) - Implementation details and prompt templates
- [Parallel Invocation](references/parallel-invocation.md) - Examples of spawning parallel agents
- [Sample Output](references/sample-output.md) - Complete example of expected output
