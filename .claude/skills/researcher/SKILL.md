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
1. Always evaluate which tools each sub-topic requires (WebSearch, WebFetch, Bash, etc.)
2. **ONE AGENT PER TOOL TYPE** - If a sub-topic needs multiple tools, spawn separate agents for each tool
3. More agents = better coverage (parallel execution means no time penalty)

### Research Limits (Prevent Long Loops)

To ensure focused, quality research without getting stuck:

| Constraint | Limit |
|------------|-------|
| Distinct tools per sub-topic | Max 5 |
| Results/calls per tool | Max 5 |

**Example:** For a sub-topic using WebSearch, perform up to 5 searches and use the top results. Don't endlessly search for more - quality over quantity.

### Agent-per-Distinct-Tool Example

**Sub-topic:** "GitHub Repository Statistics"

**Distinct tools needed:** WebSearch + Bash (2 distinct tool types)

**WRONG (1 agent using both tools sequentially):**
```
❌ Agent 1: WebSearch + Bash (gh CLI)
```

**CORRECT (2 agents in parallel, one per distinct tool):**
```
✅ Agent 1a: WebSearch only → "Find articles about repo community growth" (can make multiple searches)
✅ Agent 1b: Bash only → "Get live stars, forks, issues counts" (can run multiple commands)
```

**Note:** If Agent 1a needs 3 different WebSearch queries, that's still 1 agent making 3 calls - NOT 3 agents.

Both agents run simultaneously, results are merged in Phase 3.

See [Parallel Invocation Reference](references/parallel-invocation.md) for more examples.

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
3. **Check for dependencies** - Are any tools dependent on outputs of others?
   - **If YES** → Run dependent tasks **sequentially** (not in parallel)
   - **If NO** → Safe to parallelize all agents

   **Example of dependent tasks (CANNOT parallelize):**
   ```
   ❌ "Find GitHub URL for Project X" (Agent A) + "Clone it" (Agent B)
      → Agent B needs Agent A's output first → Run sequentially
   ```

   **Example of independent tasks (CAN parallelize):**
   ```
   ✅ "Search articles about Project X" (Agent A) + "Get GitHub stats" (Agent B)
      → Neither needs the other's output → Run in parallel
   ```

### Phase 2: Parallel Sub-Agent Research

4. **Create agent assignment table** - For each sub-topic, list the DISTINCT tools needed (one row per distinct tool type):

   | Sub-topic | Distinct Tool | Agent ID | Research Goal |
   |-----------|---------------|----------|---------------|
   | Framework A overview | WebSearch | 1 | Find adoption articles |
   | Framework B overview | WebSearch | 2 | Find comparison posts |
   | Official docs | WebFetch | 3 | Extract API patterns from docs.example.com |
   | GitHub stats | WebSearch | 4 | Find articles about community growth |
   | GitHub stats | Bash | 5 | Run gh CLI for live star/fork counts |

   **Key rules:**
   - One agent per **distinct tool type** per sub-topic
   - A sub-topic can use **up to 5 different tools** → up to 5 agents for that sub-topic
   - Multiple calls of the same tool = 1 agent (e.g., 3 WebSearches = 1 WebSearch agent)
   - Different tool types = separate agents (e.g., WebSearch + Bash = 2 agents)

   > **Clarification: Tool vs Function Call**
   > - **Same tool, multiple calls** (e.g., `search("q1")`, `search("q2")`) → **1 Agent** (the agent loop handles iteration internally)
   > - **Different tools** (e.g., `search()` + `shell()`) → **2 Agents** (each tool gets its own agent)

5. **Count total agents** - Simply count the rows in your table:
   ```
   Total Agents = Number of rows in assignment table
   ```

6. **Spawn ALL agents in a SINGLE message** - Use the Task tool to launch all sub-agents simultaneously:

```
For each agent, use the Task tool with:
- subagent_type: "general-purpose"
- run_in_background: false (to get results back)
- Launch ALL agents in ONE message for true parallelism
```

⚠️ **CRITICAL:** Do NOT combine multiple tools into one agent. Each tool type = separate agent.

**Sub-agent prompt template:**
```
Research the following sub-topic for a blog post:

Main Topic: [MAIN_TOPIC]
Sub-topic: [SUB_TOPIC]
Research Goal: [SPECIFIC_GOAL]

**TOOL RESTRICTION: Use ONLY [TOOL_NAME] for this research.**
- Make up to 5 calls with [TOOL_NAME]
- Do NOT use other tools - separate agents handle those

Return your findings in this format:

## [SUB_TOPIC] (via [TOOL_NAME])

### Key Findings
- Finding 1 (Source: ...)

### Sources
- [Source Title](URL) or command/method used
```

**Example goals by research type:**
- Web research: "Find recent articles about framework adoption trends and developer sentiment"
- Documentation: "Extract key features and API patterns from the official docs"
- GitHub data: "Get live repository statistics (stars, forks, issues, contributors) using gh CLI"

See [Tool-Based Research Reference](references/tool-based-research.md) for tool-specific prompt templates.

### Phase 3: Compilation

7. **Compile all sub-agent results** - Gather outputs from all parallel agents
8. **Synthesize into unified brief** - Merge findings, remove duplicates, organize coherently
9. **Resolve data conflicts** - Different sources may contradict each other:

   | Source Type | Data Nature | Trust Level |
   |-------------|-------------|-------------|
   | CLI tools (Bash/gh) | Current/live state | **High** (exact numbers) |
   | WebSearch | Historical/contextual | Medium (may be outdated) |
   | WebFetch (docs) | Official/authoritative | High (but check version) |

   > **Conflict Resolution:** If CLI data contradicts Web Search data, trust CLI tools for exact numbers (they reflect current state). Note discrepancies in the brief.

10. **Add cross-cutting insights** - Identify connections between sub-topics

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
