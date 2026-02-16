---
name: blog-writer
description: Generates high-quality blog posts from research data. Use this skill after the research phase to transform raw findings into a structured, engaging Markdown article with a 'Conversational Authority' voice.
---

# Blog Writer

## When to Use This Skill
Activate this skill once the research phase is complete and you have a set of sub-topics or raw data. It is used to synthesize information into a cohesive narrative that follows professional style standards.

## Drafting Process
1.  **Analyze Research Data:** Review the findings from the `blog-researcher` skill.
2.  **Consult Style Guide:** Read [references/style_guide.md](references/style_guide.md) to adopt the "Conversational Authority" voice and ensure correct typography, list formatting, and callout usage.
3.  **Draft the Structure:**
    - **H1 Title:** Create a bold, intriguing hook.
    - **Opening:** 1-2 paragraphs setting the thesis.
    - **Body (H2/H3):** 3-5 sections covering the core sub-topics.
    - **Closing:** A thoughtful, memorable ending (avoiding "In conclusion").
4.  **Formatting Integration:**
    - Use **Bold** for emphasis and `Code` for technical terms.
    - Insert Notion-style Callout Boxes (Insight, Warning, Stats) to break up text.
    - Ensure sentence and paragraph lengths align with the Readability Standards in the style guide.

## Requirements
- Output must be in clean Markdown.
- Maintain a balance between being clear and being engaging.
- Strictly follow the hierarchy and typography rules in the reference guide.

## Metrics
Report execution latency, estimated cost, and token counts. Provide a summary of the blog's structure (e.g., "5 sections, 3 callouts, 1200 words").