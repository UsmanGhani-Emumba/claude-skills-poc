---
name: blog-researcher
description: Conducts multi-phase research. Divides topics into sub-topics and uses specific tools for each.
---
# Blog Researcher
## Phase 1: Topic Analysis
Break the user's topic into 4-6 distinct sub-topics.
## Phase 2: Tool Execution
Use `scripts/research.py` for:
- Web Search: `python scripts/research.py --tool search --query "<subtopic>"`
- Article Scrape: `python scripts/research.py --tool scrape --query "<url>"`
- YouTube: `python scripts/research.py --tool youtube --query "<url>"`
