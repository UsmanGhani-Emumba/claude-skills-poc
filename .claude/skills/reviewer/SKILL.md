---
name: reviewer
description: Editorial review skill for polishing and improving blog drafts. Activates after writing is complete or when asked to review/edit/improve content. Triggers on "review this", "improve the draft", "edit for quality", "polish this article", or as the final step in content creation pipelines.
---

# Reviewer Skill

## Purpose

Elevate draft content to publication-ready quality through systematic review and targeted improvements.

## Prerequisites

- Draft blog post should be available (from Writer skill)
- Original research brief (optional but helpful for fact-checking)

## Review Workflow

Execute these checks in order:

### 1. Structure Check
- Does the opening hook grab attention?
- Is there a clear narrative flow?
- Does each section transition smoothly to the next?
- Is the conclusion memorable (not generic)?

### 2. Content Quality Check
- Are all claims supported by sources?
- Are there any unsupported assertions to flag or remove?
- Is the content depth appropriate (not too shallow, not overwhelming)?
- Are examples concrete and relatable?

### 3. Engagement Check
- Would YOU want to keep reading?
- Are there any dull stretches that need energy?
- Is the tone consistent throughout?
- Are subheadings compelling (not generic)?

### 4. Technical Check
- Grammar and spelling
- Sentence variety (not all same length/structure)
- Paragraph length (break up walls of text)
- Jargon (explain or remove)

### 5. Final Polish
- Strengthen weak verbs (is/was → active verbs)
- Cut filler words (very, really, just, actually)
- Sharpen the opening line
- Ensure the last line resonates

## Output Format

Provide the improved blog post with a brief changelog:

```markdown
# [Revised Title if improved]

[Full revised blog post]

---

## Revision Notes

**Key improvements made:**
- [Change 1 and why]
- [Change 2 and why]
- [Change 3 and why]

**Suggestions for author consideration:**
- [Optional improvement 1]
- [Optional improvement 2]
```

## Quality Criteria

- All five review checks completed
- At least 3 substantive improvements made
- Maintains author's voice while elevating quality
- Final output is publication-ready

## Reference

For a complete example of expected output, see [references/sample-output.md](references/sample-output.md)