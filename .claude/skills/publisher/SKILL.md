---
name: publisher
description: Publishing skill for deploying finalized content to Notion. Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
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

**Response:** Save the returned `id` field for Step 4.

### Step 4: Add Content in Batches (Auto-Progress)

Use curl to append content blocks to the new page:

```bash
curl -X PATCH "https://api.notion.com/v1/blocks/NEW_PAGE_ID/children" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "First paragraph"}}]}},
      {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Section Title"}}]}},
      {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "List item"}}]}}
    ]
  }'
```

**Batch size:** 5 blocks maximum per API call.

**⚠️ IMPORTANT: Auto-Batching Required**

Process ALL batches automatically without pausing for user confirmation:

1. Calculate total batches needed upfront
2. Execute each batch curl command sequentially in a single response
3. Only pause if an error occurs that requires user intervention
4. Display progress inline (e.g., "✅ Batch 1/4 complete") after each successful batch

**DO NOT** ask "Should I continue?" between batches. Complete the entire upload in one continuous flow.

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
