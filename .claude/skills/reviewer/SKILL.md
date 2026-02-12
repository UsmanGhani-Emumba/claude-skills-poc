---
name: reviewer
description: Editorial review skill for polishing and improving blog drafts. Activates after writing is complete or when asked to review/edit/improve content. Triggers on "review this", "improve the draft", "edit for quality", "polish this article", or as the final step in content creation pipelines.
---

# Reviewer Skill

> **MANDATORY FIRST STEP — DO NOT SKIP**
> Before reading ANY other section, before checking prerequisites,
> before gathering context, execute this command IMMEDIATELY:
> ```
> Bash: SESSION_ID=$(/c/Python311/python.exe scripts/arize_agent.py --action start-session --skill reviewer --model claude-sonnet-4-5-20250929)
> ```
> Only after this command succeeds should you continue reading below.

## Purpose

Elevate draft content to publication-ready quality through systematic review and targeted improvements. Uses an **instrumented Python agent** for the review step to capture Arize observability metrics (tokens, cost, latency).

## Prerequisites

- Draft blog post available (from Writer skill)
- Research brief (for fact-checking)
- Target audience (for tone validation)

## Workflow

### Step 1: Gather Context (main conversation)

1. **Verify draft** exists from Writer skill
2. **Verify research brief** is available for fact-checking
3. **Confirm target audience** for tone validation

### Step 2: Prepare Review Task

Compose a comprehensive task prompt with ALL context, then write it to a task file.

**Write the following to `.claude/logs/tasks/reviewer-1.txt`:**

```
You are an expert editorial reviewer. Elevate this draft blog post to publication-ready quality through systematic review.

## Target Audience
[INSERT: audience name and description]

## Review Checklist

### 1. Content Quality
- Every claim backed by research — no unsupported assertions
- No fluff paragraphs — each adds value
- Clear narrative thread from intro to conclusion
- Appropriate depth — not too shallow, not overwhelming
- Examples are concrete and relatable

### 2. Audience Alignment
- Tone matches target audience
- Complexity level appropriate
- Jargon explained (or removed for general audience)
- Focus areas relevant to audience needs

### 3. Structure Check
- Title is compelling and clear (under 60 characters)
- Opening hook grabs attention in first sentence
- Clear section flow with smooth transitions
- Conclusion is memorable, not generic
- 800-1200 words (unless specified otherwise)

### 4. Style Compliance
- Conversational but authoritative tone
- 2-4 sentences per paragraph (5 max)
- Sentence variety (not all same length)
- No filler words (very, really, just, actually)
- Active voice preferred over passive
- Reading level accessible (8th-10th grade)

### 5. Technical Polish
- Grammar and spelling correct
- Headings are scannable and informative
- Emphasis used sparingly (bold, italics)
- Sources formatted as bulleted list (NOT inline comma-separated)

## Source Formatting (CRITICAL)

Sources MUST be formatted as a bulleted list. If they are inline comma-separated, FIX THEM.

CORRECT:
**Sources:**
- [Source Title](URL)

WRONG (fix immediately):
Sources: Source Title, Another Source

## Review Process

1. Run through the checklist systematically
2. Flag issues that fail each check
3. Apply fixes while preserving author voice
4. Final polish:
   - Strengthen weak verbs (is/was → active verbs)
   - Cut filler words (very, really, just, actually)
   - Sharpen the opening line
   - Ensure the last line resonates

## Draft to Review

[INSERT: full blog post draft from Writer skill]

## Research Brief (for fact-checking)

[INSERT: full research brief from Researcher skill]

---

Provide the improved blog post followed by revision notes in this format:

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

**Important:** Include the FULL draft and FULL research brief in the task file. The Python agent has no access to local files.

### Step 3: Execute Instrumented Reviewer

**Run the Python agent** with the session ID (from Step 0):

```
Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/reviewer-1.txt --tools none --skill reviewer --agent-id reviewer-1 --session-id $SESSION_ID
```

**End the session** to aggregate metrics and create a summary span in Arize:

```
Bash: /c/Python311/python.exe scripts/arize_agent.py --action end-session --session-id $SESSION_ID
```

The agent returns JSON with `result` (revised blog + revision notes) and `metrics`. The session end returns aggregated skill-level metrics.

### Step 4: Present Result

1. **Parse the JSON** output from the agent
2. **Display the revised blog post** from the `result` field
3. **Show review metrics** (from agent output and session summary):

```markdown
## Review Metrics

| Metric | Value |
|--------|-------|
| Session ID | $SESSION_ID |
| Input tokens | X |
| Output tokens | Y |
| Cost | $Z |
| Latency | Ns |
| Model | claude-sonnet-4-5-20250929 |
```

## Success Criteria

- All checklist items pass (or flagged with reason)
- At least 3 substantive improvements made
- Author's voice preserved while elevating quality
- Final output is publication-ready

### Iteration

If the user requests further changes:

1. Compose an updated task prompt including the current revised draft + requested changes
2. Write to `.claude/logs/tasks/reviewer-2.txt` (increment the number)
3. Run the agent again — each iteration is tracked separately in Arize

## Reference

For a complete example of expected output, see [references/sample-output.md](references/sample-output.md)
