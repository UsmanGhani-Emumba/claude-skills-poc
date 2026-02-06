---
name: publisher
description:- [x] **Publisher**: Discovered Notion pages and deployed content in batches. Optimized for `SafeToAutoRun: true` on deployment scripts.
 Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
---

# Publisher Skill

## Purpose

Deploy finalized content to Notion by creating a new page under a parent page using the Notion API via curl.

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

Use the shared discovery template to find connected Notion pages.

1.  **Read Template**: [notion-discover.js](references/notion-discover.js)
2.  **Execute**:
    ```powershell
    # Copy template to temporary file, inject token, and run
    node discover.js
    ```
    *(Set `SafeToAutoRun: true` for the execution command)*

### Step 2: Let User Select Parent

Present discovered pages and use `notify_user` to let user pick the parent page (BlockedOnUser: true).

### Step 3: Create and Upload Content (Robust Method)

⚠️ **CRITICAL: No code in SKILL.md. Use the following reference files.**

1.  **Prepare Content**: Write `blog_content.json` following the structure in [block-structures.md](references/block-structures.md).
2.  **Use Script**: [notion-publish.js](references/notion-publish.js)
3.  **Deploy**:
    ```powershell
    $env:NOTION_TOKEN="..."; $env:NOTION_PARENT_ID="..."; node notion-publish.js
    ```
    *(Set `SafeToAutoRun: true` for the execution command)*

**Batch size:** 5 blocks maximum per API call.

Process ALL batches automatically without pausing for user confirmation.

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
📤 Publishing to Notion
━━━━━━━━━━━━━━━━━━━━
✅ Page created: "Blog Title"

Uploading content (4 batches):
✅ Batch 1/4 complete
✅ Batch 2/4 complete
✅ Batch 3/4 complete
✅ Batch 4/4 complete

All content uploaded successfully.
```

**Note:** Progress updates appear after each batch completes. The entire upload runs automatically without requiring user confirmation.

## Success Output

```markdown
## ✅ Published Successfully

**New Page:** [Blog Title](https://notion.so/...)
**Parent:** "Parent Page Name"

- Word count: XXX
- Sections: X

[Open in Notion](https://notion.so/...)
```

## Reference

- [references/sample-output.md](references/sample-output.md) — Publishing workflow and output examples
- [references/block-structures.md](references/block-structures.md) — JSON structure for Notion blocks
