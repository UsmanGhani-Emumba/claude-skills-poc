# Gemini CLI Skills POC

A proof-of-concept for building reusable AI workflows in Gemini CLI using **Skills** and **Commands**.

---

## What Are Skills?

A **Skill** is a reusable, role-specific prompt module stored under `.gemini/skills/<skill-name>/SKILL.md`. Each skill defines a persona, a behavior, and a structured output format.

Skills are the *logic layer* — they contain the detailed instructions for how Gemini should think, decompose a problem, and format its response. Skills do not run on their own; they are invoked by commands or referenced directly in conversation.

**Structure of a skill:**
```
.gemini/skills/
  researcher/
    SKILL.md          ← core skill instructions
  writer/
    SKILL.md
    references/       ← supporting docs the skill reads
  reviewer/
    SKILL.md
    references/
  publisher/
    SKILL.md
    references/
      run_publisher.py ← standalone script that calls the Notion API
```

---

## What Are Commands?

A **Command** is a short prompt file stored under `.gemini/commands/<command-name>.md`. It acts as a *thin entry point* that invokes a skill and passes user-supplied arguments via `$ARGUMENTS`.

Commands are registered as slash commands inside Gemini CLI, making them directly executable from the CLI:

```
/research <topic>
/write <topic or brief>
/review <content>
/publish <content>
/pipeline <topic>
```

**Structure of a command:**
```
.gemini/commands/
  research.md     → invokes researcher skill
  write.md        → invokes writer skill
  review.md       → invokes reviewer skill
  publish.md      → invokes publisher skill
  pipeline.md     → chains all skills end-to-end
```

---

## Skills Created

### 1. Researcher
**File:** `.gemini/skills/researcher/SKILL.md`

Deep-researches any topic using parallel sub-agent decomposition.

- Breaks the topic into 4–6 subtopics
- Assigns research approaches to each subtopic (web search, academic papers, code search, video talks, official docs, data APIs)
- Spawns all `(subtopic, approach)` pairs as sub-agents simultaneously in a single parallel batch
- Synthesizes findings into a structured research brief with source registry, data points, multiple perspectives, and confidence levels

### 2. Writer
**File:** `.gemini/skills/writer/SKILL.md`

Writes polished, publish-ready articles and blog posts from research briefs or raw topics.

- Produces content with a compelling headline, strong hook, structured body, and clear conclusion
- Follows a defined reference format (H1 title, metadata, H2/H3 sections, bold lead-ins)
- Handles revisions by incorporating feedback from the reviewer

### 3. Reviewer
**File:** `.gemini/skills/reviewer/SKILL.md`

Reviews written content for quality, accuracy, clarity, and AI fingerprint detection.

- Scores content out of 10 and returns an `APPROVED` or `NEEDS_REVISION` verdict
- Checks paragraph structure, logical flow, factual accuracy, and Notion formatting guidelines
- Detects AI writing patterns (dash overuse, robotic transitions, missing contractions, structural uniformity)
- The verdict directly drives the pipeline — if `NEEDS_REVISION`, the writer revises before publishing

### 4. Publisher
**File:** `.gemini/skills/publisher/SKILL.md`

Transforms finalized content into structured JSON and publishes it to Notion.

- Extracts metadata: title, tags, category, summary
- Converts content into Notion-compatible block types (headings, paragraphs, lists, code, callouts, dividers)
- Returns a JSON payload consumed by `run_publisher.py`, which handles the 3-phase Notion API pipeline: verify parent page → create child page → append content in batches

---

## Commands vs Skills — Why Prefer Commands to Execute Prompts

**Always invoke skills through commands** rather than writing out skill instructions manually. Here is why:

| | Command (`/research ...`) | Raw prompt (typing instructions) |
|---|---|---|
| **Invocation** | One-line slash command | Re-typing or copy-pasting skill instructions |
| **Consistency** | Same skill, same behavior every time | Varies with how you phrase the prompt |
| **Arguments** | Clean `$ARGUMENTS` injection | Embedded in freeform text |
| **Discoverability** | Listed in Gemini CLI as registered commands | Hidden; must be remembered |
| **Chaining** | `/pipeline` chains all skills in order automatically | Requires manual step-by-step coordination |
| **Maintainability** | Update the skill file once; all invocations benefit | Each manual invocation is independent |

Commands are the *interface*; skills are the *implementation*. Keeping them separate means you can improve a skill's logic without changing how it is called, and you can add new entry points without duplicating instructions.

### The `/pipeline` Command

The most powerful command chains all four skills in a single invocation:

```
/pipeline Write about AI trends in software engineering
```

Execution order:
1. **Researcher** → produces a research brief
2. **Writer** → drafts content from the brief
3. **Reviewer** → scores the draft; issues `APPROVED` or `NEEDS_REVISION`
4. **Writer** (if needed) → revises based on reviewer feedback
5. **Publisher** → formats and publishes the approved article to Notion

Each step receives the full context from the previous step automatically.

---

## Hooks & Tracing

### Automatic Hook Logging (Always-On)

Hooks are configured in `.gemini/settings.json` using `BeforeTool` and `AfterTool` events. They fire on **every** tool call automatically — no extra flags needed.

- **BeforeTool** logs tool name + input before execution
- **AfterTool** logs tool name + input + output preview after execution
- Each session creates its own file: `traces/hooks-<session-id>.jsonl`

### Stream-JSON Tracing (On-Demand)

For a full event stream including tokens, tool calls, and results:

```bash
bash trace-run.sh "/pipeline Write about AI trends"
```

### Trace Analysis

```bash
python analyze-trace.py hooks latest    # Analyze most recent hook trace
python analyze-trace.py stream latest   # Analyze most recent stream trace
python analyze-trace.py both latest     # Both together
```

---

## Quick Start

```bash
# Interactive mode
cd gemini_skills_folder
gemini

# Then run any command:
/research How does retrieval-augmented generation work?
/write Draft a blog post about developer productivity
/pipeline Write about the future of AI coding assistants
```

```bash
# Headless mode (single command)
gemini "/pipeline Write about AI trends and publish to Notion"
```

See `how_to_run.md` for tracing, logging, and analysis instructions.
