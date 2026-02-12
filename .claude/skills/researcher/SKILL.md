---
name: researcher
description: Research skill for gathering facts, data, and sources on a given topic. Activates when the task requires finding current information, statistics, expert opinions, or real-world examples before writing. Triggers on requests like "research [topic]", "find information about", "gather facts on", or as the first step in content creation pipelines.
---

# Researcher Skill

> **MANDATORY FIRST STEP — DO NOT SKIP**
> Before reading ANY other section, before analyzing the topic,
> before planning anything, execute this command IMMEDIATELY:
> ```
> Bash: SESSION_ID=$(/c/Python311/python.exe scripts/arize_agent.py --action start-session --skill researcher --model claude-sonnet-4-5-20250929)
> ```
> Only after this command succeeds should you continue reading below.

## Purpose

Gather comprehensive, accurate information on a topic to serve as the foundation for content creation. Uses **parallel instrumented sub-agents** to research multiple sub-topics simultaneously for faster, more thorough research — with full Arize observability.

---

## Core Principle: Quality Over Agent Count

**NEVER compromise research quality to reduce the number of agents.**

Parallel sub-agents exist to **maximize quality while saving time** - not to minimize agent usage. Always spawn all necessary agents for comprehensive coverage.

**Rules:**
1. Always evaluate which tools each sub-topic requires (web_search, web_fetch, github_cli)
2. **ONE AGENT PER TOOL TYPE** - If a sub-topic needs multiple tools, spawn separate agents for each tool
3. More agents = better coverage (parallel execution means no time penalty)

### Research Limits (Prevent Long Loops)

To ensure focused, quality research without getting stuck:

| Constraint | Limit |
|------------|-------|
| Distinct tools per sub-topic | Max 5 |
| Results/calls per tool | Max 5 |

**Example:** For a sub-topic using web_search, the agent performs up to 5 searches and uses the top results. Don't endlessly search for more - quality over quantity.

### Agent-per-Distinct-Tool Example

**Sub-topic:** "GitHub Repository Statistics"

**Distinct tools needed:** web_search + github_cli (2 distinct tool types)

**WRONG (1 agent using both tools):**
```
❌ Agent 1: web_search + github_cli
```

**CORRECT (2 agents in parallel, one per distinct tool):**
```
✅ Agent 1a: web_search only → "Find articles about repo community growth"
✅ Agent 1b: github_cli only → "Get live stars, forks, issues counts"
```

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

### Phase 2: Parallel Instrumented Sub-Agent Research

4. **Create agent assignment table** - For each sub-topic, list the DISTINCT tools needed (one row per distinct tool type):

   | Sub-topic | Tool | Agent ID | Research Goal |
   |-----------|------|----------|---------------|
   | Framework A overview | web_search | 1a | Find adoption articles |
   | Framework B overview | web_search | 2a | Find comparison posts |
   | Official docs | web_fetch | 3a | Extract API patterns from docs.example.com |
   | GitHub stats | web_search | 4a | Find articles about community growth |
   | GitHub stats | github_cli | 4b | Run gh CLI for live star/fork counts |

   **Key rules:**
   - One agent per **distinct tool type** per sub-topic
   - A sub-topic can use **up to 5 different tools** → up to 5 agents for that sub-topic
   - Multiple calls of the same tool = 1 agent (e.g., 3 web searches = 1 web_search agent)
   - Different tool types = separate agents (e.g., web_search + github_cli = 2 agents)

   > **Clarification: Tool vs Function Call**
   > - **Same tool, multiple calls** (e.g., `search("q1")`, `search("q2")`) → **1 Agent** (the agent loop handles iteration internally)
   > - **Different tools** (e.g., `web_search` + `github_cli`) → **2 Agents** (each tool gets its own agent)

5. **Count total agents** - Simply count the rows in your table:
   ```
   Total Agents = Number of rows in assignment table
   ```

6. **Write task prompts** - For each agent, write its task prompt to a file:

   ```
   Write each agent's task prompt to: .claude/logs/tasks/<agent-id>.txt
   ```

   **Sub-agent prompt template:**
   ```
   Research the following sub-topic for a blog post:

   Main Topic: [MAIN_TOPIC]
   Sub-topic: [SUB_TOPIC]
   Research Goal: [SPECIFIC_GOAL]

   Use your available tool to find comprehensive information.
   Make up to 5 tool calls for thorough coverage.

   Return your findings in this format:

   ## [SUB_TOPIC]

   ### Key Findings
   - Finding 1 (Source: ...)

   ### Sources
   - [Source Title](URL) or command/method used
   ```

7. **Spawn ALL agents in a SINGLE message** - Use the Bash tool to launch all instrumented Python agents simultaneously, passing `--session-id`:

   ```
   For each agent, use the Bash tool with:
     /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/<agent-id>.txt --tools <tool> --agent-id <id> --skill researcher --session-id $SESSION_ID
   Launch ALL Bash calls in ONE message for true parallelism.
   ```

   **Available tools:** `web_search`, `web_fetch`, `github_cli`

   **Example — launching 5 agents in parallel (all linked to session):**
   ```
   Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/1a.txt --tools web_search --agent-id 1a --skill researcher --session-id $SESSION_ID
   Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_fetch  --agent-id 1b --skill researcher --session-id $SESSION_ID
   Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/2a.txt --tools web_search --agent-id 2a --skill researcher --session-id $SESSION_ID
   Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/3a.txt --tools web_search --agent-id 3a --skill researcher --session-id $SESSION_ID
   Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/3b.txt --tools github_cli --agent-id 3b --skill researcher --session-id $SESSION_ID
   ```

   ⚠️ **CRITICAL:** Do NOT combine multiple tools into one agent. Each tool type = separate agent.

   Each agent outputs **JSON** with `result` (research findings) and `metrics` (tokens, cost, latency, tools).

See [Tool-Based Research Reference](references/tool-based-research.md) for tool-specific prompt templates.

### Phase 3: Compilation & Metrics

9. **Parse agent outputs** - Each Bash call returns JSON. Extract the `result` field from each.
10. **Compile research brief** - Merge all findings, remove duplicates, organize coherently
11. **Resolve data conflicts** - Different sources may contradict each other:

   | Source Type | Data Nature | Trust Level |
   |-------------|-------------|-------------|
   | github_cli (Bash/gh) | Current/live state | **High** (exact numbers) |
   | web_search | Historical/contextual | Medium (may be outdated) |
   | web_fetch (docs) | Official/authoritative | High (but check version) |

   > **Conflict Resolution:** If CLI data contradicts web search data, trust CLI tools for exact numbers (they reflect current state). Note discrepancies in the brief.

12. **Add cross-cutting insights** - Identify connections between sub-topics
13. **End the skill session** — After all agents complete and results are compiled, close the session to aggregate metrics:

   ```
   Bash: /c/Python311/python.exe scripts/arize_agent.py --action end-session --session-id $SESSION_ID
   ```

   This outputs a JSON summary with aggregated session metrics (total tokens, cost, wall latency, tools, etc.) and creates a summary span in Arize Phoenix for the entire researcher skill invocation.

14. **Aggregate metrics** - Collect the `metrics` field from each agent output and the session summary to produce a combined view:

   ```markdown
   ## Research Metrics

   | Agent | Tool | Input Tokens | Output Tokens | Cost | Latency |
   |-------|------|-------------|---------------|------|---------|
   | 1a | web_search | 2,100 | 450 | $0.0138 | 8.2s |
   | 1b | web_fetch | 3,200 | 600 | $0.0186 | 12.1s |
   | ... | ... | ... | ... | ... | ... |
   | **Total** | | **X** | **Y** | **$Z** | **Ns** |

   - **Sub-agents spawned:** N
   - **Distinct tools used:** N (web_search, web_fetch, github_cli)
   ```

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

---

## Research Metrics

| Agent | Tool | Input Tokens | Output Tokens | Cost | Latency |
|-------|------|-------------|---------------|------|---------|
| ... | ... | ... | ... | ... | ... |
| **Total** | | **X** | **Y** | **$Z** | **Ns** |

- **Sub-agents spawned:** N
- **Distinct tools used:** N (list)
```

**Note:** Format sources as a bulleted list with URLs. The Reviewer skill validates source formatting.

---

## References

- [Quality Criteria](references/quality-criteria.md) - Standards for research output
- [Tool-Based Research](references/tool-based-research.md) - Implementation details and prompt templates
- [Parallel Invocation](references/parallel-invocation.md) - Examples of spawning parallel agents
- [Sample Output](references/sample-output.md) - Complete example of expected output
