---
description: Run the full content pipeline (research → write → review → revise → publish)
---

Run the full content pipeline for:

$ARGUMENTS

Execute in order:
1. Researcher skill → produce research brief
2. Writer skill → draft content using research
3. Reviewer skill → review the draft
4. If NEEDS_REVISION: Writer skill again with feedback
5. Publisher skill → publish to Notion

Pass context between each step. Trace every skill invocation with Arize Phoenix. Display per-skill and total metrics (input tokens, output tokens, context window, latency, cost) after completion.
