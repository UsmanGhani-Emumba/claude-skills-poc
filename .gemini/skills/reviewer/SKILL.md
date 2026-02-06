---
name: reviewer
description: Editorial review skill for polishing and improving blog drafts. Activates after writing is complete or when asked to review/edit/improve content. Triggers on "review this", "improve the draft", "edit for quality", "polish this article", or as the final step in content creation pipelines.
---

# Reviewer Skill

## Purpose

Elevate draft content to publication-ready quality through systematic review and targeted improvements.

## Prerequisites

- Draft blog post available (from Writer skill)
- Research brief (for fact-checking)
- Target audience (for tone validation)

## Review Checklist

### 1. Content Quality
- [ ] Every claim backed by research — no unsupported assertions
- [ ] No fluff paragraphs — each adds value
- [ ] Clear narrative thread from intro to conclusion
- [ ] Appropriate depth — not too shallow, not overwhelming
- [ ] Examples are concrete and relatable

### 2. Audience Alignment
- [ ] Tone matches target audience
- [ ] Complexity level appropriate
- [ ] Jargon explained (or removed for general audience)
- [ ] Focus areas relevant to audience needs

### 3. Structure Check
- [ ] Title is compelling and clear (under 60 characters)
- [ ] Opening hook grabs attention in first sentence
- [ ] Clear section flow with smooth transitions
- [ ] Conclusion is memorable, not generic
- [ ] 800-1200 words (unless specified otherwise)

### 4. Style Compliance
- [ ] Conversational but authoritative tone
- [ ] 2-4 sentences per paragraph (5 max)
- [ ] Sentence variety (not all same length)
- [ ] No filler words (very, really, just, actually)
- [ ] Active voice preferred over passive
- [ ] Reading level accessible (8th-10th grade)

### 5. Technical Polish
- [ ] Grammar and spelling correct
- [ ] Headings are scannable and informative
- [ ] Emphasis used sparingly (bold, italics)
- [ ] **Sources formatted as bulleted list** (NOT inline comma-separated)

## Source Formatting (CRITICAL)

⚠️ **Sources must be formatted as a bulleted list. If they are inline comma-separated, FIX THEM.**

### ✅ CORRECT:
```markdown
**Sources:**

- [McKinsey Future of Work Report](https://mckinsey.com/...)
- [Buffer State of Remote Work](https://buffer.com/...)
- [Gallup Workplace Trends](https://gallup.com/...)
```

### ❌ WRONG (fix this immediately):
```markdown
Sources: McKinsey Future of Work Report, Buffer State of Remote Work, Gallup Workplace Trends
```

## Review Workflow

1. **Run through checklist** — Systematically check all items above
2. **Flag issues** — Note what fails each check
3. **Apply fixes** — Make improvements while preserving author voice
4. **Final polish:**
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

## Success Criteria

- All checklist items pass (or flagged with reason)
- At least 3 substantive improvements made
- Author's voice preserved while elevating quality
- Final output is publication-ready

## Reference

For a complete example of expected output, see [references/sample-output.md](references/sample-output.md)