---
name: blog-researcher
description: Conducts hierarchical, multi-tool research by spawning sub-agents for sub-topics and distinct tools.
---

# Blog Researcher

## Unified Research Execution
When a research topic is provided, you must execute the entire hierarchical decomposition and sub-agent identification in a **single step/prompt**. This ensures consistency and prevents missing sub-agents.

1.  **Topic Decomposition:** Divide the main topic into **4-6 distinct sub-topics**.
2.  **Sub-Agent Identification:** For each sub-topic, immediately identify the required **Tool-Specific Sub-Agents**.
    - **Spawn a distinct sub-agent for each tool.** (e.g., if Sub-Topic 1 needs YouTube and Articles, identify "Sub-Topic 1 YouTube Agent" and "Sub-Topic 1 Article Agent").
    - **Limit:** At most **5 distinct tools** per sub-topic.

## Research Tools & Capabilities
Each identified tool-specific sub-agent has the capability to make **up to 5 calls** to their respective tool to ensure depth and recency.

### Available Tools:
1.  **Web Pages / Articles:** Use `scripts/research.py --tool scrape`.
2.  **Wiki:** Use `scripts/research.py --tool scrape` on Wikipedia URLs found via search.
3.  **YouTube:** Use `scripts/research.py --tool youtube`.
4.  **GitHub:** Use `scripts/research.py --tool github` to find repos or code snippets.
5.  **Bash:** Execute local shell commands using `run_shell_command` for environment-specific research.
6.  **Web Search:** Use `scripts/research.py --tool search` to find URLs for other tools.

## Execution Pattern
1.  **Topic** -> [Sub-Topic 1, Sub-Topic 2, ...]
2.  **Sub-Topic X** -> [Tool Agent A (Max 5 calls), Tool Agent B (Max 5 calls), ...]
3.  **Consolidate:** Gather all findings from all sub-agents into a final JSON research report.

## Metrics & Observability
Every sub-agent call must log:
- **Latency**, **Status (Pass/Fail)**, **Input/Output Tokens**, and **Cost**.
- Report metrics in the format: `[METRICS] Agent: <sub_topic>_<tool>, Status: <status>, Latency: <sec>s`