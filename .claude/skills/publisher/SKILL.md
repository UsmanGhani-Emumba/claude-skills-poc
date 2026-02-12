---
name: publisher
description: Publishing skill for deploying finalized content to Notion. Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
---

# Publisher Skill

> **MANDATORY FIRST STEP — DO NOT SKIP**
> Before reading ANY other section, before extracting tokens,
> before checking prerequisites, execute this command IMMEDIATELY:
> ```
> Bash: SESSION_ID=$(/c/Python311/python.exe scripts/arize_agent.py --action start-session --skill publisher --model claude-sonnet-4-5-20250929 --project-name "<TOPIC_SLUG>_claude_skills")
> ```
> **Derive `<TOPIC_SLUG>`** from the blog topic: lowercase, spaces to underscores, max 30 chars, alphanumeric + underscores only.
> Example: "How to use Cypress with Cucumber" → `cypress_with_cucumber_claude_skills`
>
> Only after this command succeeds should you continue reading below.

## Purpose

Deploy finalized content to Notion by creating a new page under a parent page using the Notion API via curl. Uses an **instrumented Python agent** for the markdown-to-Notion-blocks conversion step to capture Arize observability metrics (tokens, cost, latency).

## Prerequisites

1. Finalized blog content (from Reviewer skill)
2. `.mcp.json` file with `NOTION_TOKEN` configured
3. Parent page shared with Notion integration

## Workflow

### Step 0: Extract NOTION_TOKEN

Read the token from `.mcp.json` file in the project root:

```bash
# The token is stored at: .mcp.json -> mcpServers.notion.env.NOTION_TOKEN
# Use jq or manual parsing to extract it
```

Token location in `.mcp.json`:
```json
{
  "mcpServers": {
    "notion": {
      "env": {
        "NOTION_TOKEN": "ntn_xxxxxxxxxxxxx"
      }
    }
  }
}
```

### Step 1: Discover Available Pages

Use curl to search for connected pages:

```bash
curl -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "object", "value": "page"},
    "page_size": 20
  }'
```

### Step 2: Let User Select Parent

Present discovered pages and use `AskUserQuestion` to let user pick the parent page.

### Step 3: Create Empty Page

Use curl to create a new page under the selected parent:

```bash
curl -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "PARENT_PAGE_ID"},
    "properties": {
      "title": [{"text": {"content": "Blog Title Here"}}]
    }
  }'
```

**Response:** Save the returned `id` field for Step 5.

### Step 4: Convert Markdown to Notion Blocks (Instrumented)

Use the instrumented Python agent to convert the blog markdown into Notion API block JSON.

**Write the following to `.claude/logs/tasks/publisher-1.txt`:**

```
You are a Notion API block converter. Convert the blog post markdown below into valid Notion API block JSON.

## Supported Block Types

| Content Type | Block Type |
|--------------|------------|
| Paragraph | paragraph |
| Heading 2 | heading_2 |
| Heading 3 | heading_3 |
| Bullet list | bulleted_list_item |
| Numbered list | numbered_list_item |
| Code block | code |
| Divider | divider |

## Block JSON Structures

[INSERT: full contents of references/block-structures.md]

## Rules

1. Convert ALL content into Notion block JSON objects
2. Group blocks into batches of EXACTLY 5 blocks maximum
3. Handle rich text formatting: **bold** → annotations.bold, *italic* → annotations.italic, [links](url) → text.link
4. Use heading_2 for ## sections, heading_3 for ### subsections
5. Each list item (- or 1.) is a separate block
6. Use divider blocks for --- horizontal rules
7. Do NOT include the H1 title (it becomes the page title)

## Blog Content to Convert

[INSERT: full finalized blog post markdown]

---

Return your output as a JSON object with this structure:
{
  "batches": [
    [block1, block2, block3, block4, block5],
    [block6, block7, block8, block9, block10],
    ...
  ],
  "total_blocks": N,
  "total_batches": N
}

Each block must be a valid Notion API block object. Return ONLY the JSON, no explanation.
```

**Important:** Include the FULL block-structures.md reference and FULL blog content in the task file.

**Run the instrumented agent** with the session ID (from Start Skill Session):

```
Bash: /c/Python311/python.exe scripts/arize_agent.py --task-file .claude/logs/tasks/publisher-1.txt --tools none --skill publisher --agent-id publisher-1 --max-tokens 8192 --session-id $SESSION_ID
```

The agent returns JSON with `result` (the Notion block batches) and `metrics`.

### Step 5: Upload Blocks in Batches (Auto-Progress)

Parse the `batches` array from the agent's `result` field, then upload each batch via curl:

```bash
curl -X PATCH "https://api.notion.com/v1/blocks/NEW_PAGE_ID/children" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [BATCH_BLOCKS_HERE]
  }'
```

**Batch size:** 5 blocks maximum per API call.

**Auto-Batching Required:**

Process ALL batches automatically without pausing for user confirmation:

1. Calculate total batches from the agent output
2. Execute each batch curl command sequentially
3. Only pause if an error occurs that requires user intervention
4. Display progress inline after each successful batch

**DO NOT** ask "Should I continue?" between batches. Complete the entire upload in one continuous flow.

5. **End the skill session** after all batches are uploaded:

   ```
   Bash: /c/Python311/python.exe scripts/arize_agent.py --action end-session --session-id $SESSION_ID
   ```

   This creates a summary span in Arize Phoenix for the entire publisher skill invocation.

## Supported Block Types

| Content Type | Block Type | Example |
|--------------|------------|---------|
| Paragraph | `paragraph` | Body text |
| Heading 2 | `heading_2` | Section headers |
| Heading 3 | `heading_3` | Subsection headers |
| Bullet list | `bulleted_list_item` | `- item` |
| Numbered list | `numbered_list_item` | `1. item` |
| Code block | `code` | Code snippets |
| Divider | `divider` | Horizontal line |

For detailed JSON structures, see [references/block-structures.md](references/block-structures.md).

## Error Handling

| Error | Action |
|-------|--------|
| 400 Bad Request | Check JSON syntax, retry with smaller batch |
| 401 Unauthorized | Verify NOTION_TOKEN is correct |
| 429 Rate Limited | Wait 30 seconds, retry |
| 403 Forbidden | Ask user to share page with integration |

## Progress Tracking

Display progress inline as each batch completes (no user prompts between batches):

```
Publishing to Notion

Page created: "Blog Title"

Uploading content (4 batches):
Batch 1/4 complete
Batch 2/4 complete
Batch 3/4 complete
Batch 4/4 complete

All content uploaded successfully.
```

## Success Output

```markdown
## Published Successfully

**New Page:** [Blog Title](https://notion.so/...)
**Parent:** "Parent Page Name"

- Word count: XXX
- Sections: X

[Open in Notion](https://notion.so/...)

## Publishing Metrics

| Metric | Value |
|--------|-------|
| Session ID | $SESSION_ID |
| Block conversion input tokens | X |
| Block conversion output tokens | Y |
| Conversion cost | $Z |
| Conversion latency | Ns |
| Batches uploaded | N |
```

## Reference

- [references/sample-output.md](references/sample-output.md) — Publishing workflow and output examples
- [references/block-structures.md](references/block-structures.md) — JSON structure for Notion blocks
