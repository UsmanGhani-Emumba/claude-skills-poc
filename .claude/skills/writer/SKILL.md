---
name: writer
description: Writing skill for crafting engaging blog posts from research briefs. Activates after research is complete or when directly asked to write/draft content. Triggers on "write a blog about", "draft an article", "create content on", or when a research brief is available and content creation is needed.
---

# Writer Skill

## Purpose

Transform research findings into an engaging, well-structured blog post that informs and captivates readers. Uses an **instrumented Python agent** for the writing step to capture Arize observability metrics (tokens, cost, latency).

## Prerequisites

**Required before writing:**

1. Research brief available (from Researcher skill)
2. **Target audience defined**

### Audience Check (CRITICAL)

**STOP** if target audience is not specified. Ask the user:

> "Who is the target audience for this blog? For example:
> - **General public** — No assumed knowledge, conversational tone
> - **Industry professionals** — Familiar with terminology, deeper insights
> - **Executives/Decision-makers** — Bottom-line focused, time-constrained
> - **Technical practitioners** — Detail-oriented, wants specifics
> - **Beginners/Students** — Educational tone, explain fundamentals
>
> Or describe your specific audience."

**Do not proceed with writing until audience is confirmed.**

### How Audience Affects Writing

| Audience | Tone | Complexity | Focus |
|----------|------|------------|-------|
| General public | Warm, accessible | Low jargon | Relatable examples |
| Professionals | Peer-to-peer | Industry terms OK | Trends, implications |
| Executives | Direct, efficient | High-level | ROI, decisions, risks |
| Technical | Precise, detailed | Deep specifics | How-to, implementation |
| Beginners | Patient, encouraging | Define everything | Fundamentals, analogies |

## Workflow

### Step 1: Gather Context (main conversation)

1. **Verify research brief** exists from Researcher skill
2. **Confirm audience** — ask if not specified (see Audience Check above)
3. **Read the style guide** — read the contents of [references/style-guide.md](references/style-guide.md)

### Step 2: Prepare Writing Task

Compose a comprehensive task prompt that includes ALL context the Python agent needs, then write it to a task file.

**Write the following to `.claude/logs/tasks/writer-1.txt`:**

```
You are an expert blog writer. Transform the research brief below into an engaging, well-structured blog post.

## Target Audience
[INSERT: audience name and description confirmed in Step 1]

## Blog Structure Template

# [Compelling Title with Hook]

[Opening paragraph - hook the reader with a surprising fact, question, or bold statement]

## [Section 1: Set the Context]
[2-3 paragraphs introducing the topic and why it matters]

## [Section 2: The Core Content]
[3-4 paragraphs diving into the main points, using research]

## [Section 3: Implications/What This Means]
[2-3 paragraphs on impact, future outlook, or practical applications]

## [Conclusion: Call to Action or Thought-Provoker]
[1-2 paragraphs wrapping up with a memorable ending]

---

**Sources:**

- [Source Title 1](URL)
- [Source Title 2](URL)

## Style Guide

[INSERT: full contents of references/style-guide.md]

## Source Formatting Rules

CRITICAL: Sources must ALWAYS be formatted as a bulleted markdown list, one source per line.

CORRECT:
**Sources:**
- [Source Title](URL)

WRONG (NEVER do this):
Sources: Source Title, Another Source

## Research Brief

[INSERT: full research brief from Researcher skill]

---

Write the complete blog post now. Follow the style guide, structure template, and source formatting rules precisely. Target 800-1200 words.
```

**Important:** Include the FULL style guide and FULL research brief in the task file. The Python agent has no access to local files — it only sees what's in the task prompt.

### Step 3: Execute Instrumented Writer

Run the Python agent via Bash:

```
Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/writer-1.txt --tools none --skill writer --agent-id writer-1
```

The agent returns JSON with `result` (the blog post) and `metrics` (tokens, cost, latency).

### Step 4: Present Result

1. **Parse the JSON** output from the agent
2. **Display the blog post** from the `result` field
3. **Show writing metrics:**

```markdown
## Writing Metrics

| Metric | Value |
|--------|-------|
| Input tokens | X |
| Output tokens | Y |
| Cost | $Z |
| Latency | Ns |
| Model | claude-sonnet-4-5-20250929 |
```

### Iteration

If the user requests changes (e.g., "make the intro stronger", "add more statistics"):

1. Compose an updated task prompt including the current draft + requested changes
2. Write to `.claude/logs/tasks/writer-2.txt` (increment the number)
3. Run the agent again — each iteration is tracked as a separate metrics entry in Arize

## References

- [references/style-guide.md](references/style-guide.md) — Formatting, typography, voice guidelines
- [references/sample-output.md](references/sample-output.md) — Complete blog example
