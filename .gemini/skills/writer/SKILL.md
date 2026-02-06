---
name: writer
description: Writing skill for crafting engaging blog posts from research briefs. Activates after research is complete or when directly asked to write/draft content. Triggers on "write a blog about", "draft an article", "create content on", or when a research brief is available and content creation is needed.
---

# Writer Skill

## Purpose

Transform research findings into an engaging, well-structured blog post that informs and captivates readers.

## Prerequisites

**Required before writing:**

1. ✅ Research brief available (from Researcher skill)
2. ✅ **Target audience defined**

### Audience Check (CRITICAL)

⚠️ **STOP** if target audience is not specified. Ask the user:

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

1. **Analyze research** - Identify the most compelling angle from the brief
2. **Outline structure** - Plan the narrative arc before writing
3. **Draft content** - Write with the target audience in mind
4. **Weave in sources** - Naturally incorporate facts and citations

## Blog Structure Template

```markdown
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
- [Source Title 3](URL)
```

## Source Formatting Rules

⚠️ **CRITICAL: Sources must ALWAYS be formatted as a bulleted markdown list, one source per line.**

### ✅ CORRECT Format:
```markdown
---

**Sources:**

- [GitHub Copilot Statistics](https://github.com/...)
- [Indeed Hiring Lab](https://indeed.com/...)
- [MIT Technology Review](https://technologyreview.com/...)
- [Stack Overflow 2025 Survey](https://stackoverflow.com/...)
```

### ❌ WRONG Format (NEVER do this):
```markdown
Sources: GitHub Copilot Statistics, Indeed Hiring Lab, MIT Technology Review, Stack Overflow 2025 Survey
```

The inline comma-separated format is **forbidden** because:
1. Links are not clickable
2. Hard to distinguish individual sources
3. Looks unprofessional

## References

- [references/style-guide.md](references/style-guide.md) — Formatting, typography, voice guidelines
- [references/sample-output.md](references/sample-output.md) — Complete blog example