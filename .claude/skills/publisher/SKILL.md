---
name: publisher
description: Publishing skill for deploying finalized content to Notion. Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
---

# Publisher Skill

## Purpose

Deploy finalized, reviewed content to an existing Notion page with proper formatting.

## Prerequisites

**Required before publishing:**

1. ✅ Finalized blog content (from Reviewer skill)
2. ✅ Notion MCP connection active
3. ✅ **User has created an empty page in Notion** (see below)

### User Setup (REQUIRED)

⚠️ **Before publishing, the user must:**

1. Create an empty page in Notion where the blog will be published
2. Share that page with the Notion integration (Add connections → select integration)
3. Provide the **exact page name** to Claude

### Connection Check (CRITICAL)

⚠️ **STOP** if Notion MCP is not connected. Inform the user:

> "Notion MCP is not connected. Please ensure:
> 1. Notion MCP server is configured and running
> 2. Your integration token is valid
> 3. Target page is shared with the integration
>
> Run `/mcp` to check connection status."

**Do not attempt publishing without confirmed connection.**

## Workflow

1. **Verify connection** — Check Notion MCP is active
2. **Ask for page name** — Request the exact name of the target Notion page
3. **Search for page** — Use `API-post-search` to find the page by name
4. **Confirm page** — Verify the correct page was found
5. **Format content** — Convert markdown to Notion blocks
6. **Append content** — Use `API-patch-block-children` to add blocks to the page
7. **Return link** — Provide the Notion page URL

## Page Name Request

If page name is not specified, ask:

> "Please provide the **exact name** of the Notion page where you want to publish this blog.
>
> **Note:** The page must already exist in Notion and be shared with the integration."

## API Usage

### Step 1: Search for Page

Use `API-post-search` to find the target page:

```
query: "<page name>"
```

⚠️ **Note:** Only use the `query` parameter. Other parameters like `filter` and `page_size` cause serialization errors in the current MCP version.

### Step 2: Append Content

Use `API-patch-block-children` to add content:

```
block_id: "<page_id from search results>"
children: [array of block objects as JSON string]
```

⚠️ **IMPORTANT: Batch your requests!** Notion API limits ~100 blocks per request. For long blog posts:
1. Split content into batches of 10-20 blocks each
2. Make multiple sequential API calls
3. Each call appends to the end of the page

Example children parameter (small batch):
```json
[{"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Your text"}}]}}]
```

## Notion Block Format

When converting markdown to Notion blocks for `children` parameter:

| Markdown | Notion Block Type |
|----------|-------------------|
| `## Heading` | `{"type": "heading_2", "heading_2": {"rich_text": [...]}}` |
| `### Subheading` | `{"type": "heading_3", "heading_3": {"rich_text": [...]}}` |
| Paragraphs | `{"type": "paragraph", "paragraph": {"rich_text": [...]}}` |
| `- item` | `{"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [...]}}` |

Rich text format:
```json
{"type": "text", "text": {"content": "Your text here"}}
```

## Error Handling

| Error | Response |
|-------|----------|
| MCP not connected | Guide user to set up connection |
| Permission denied | Ask user to share page with integration |
| Page not found | Ask user to verify page name and that it's shared |
| Multiple pages found | Show options and ask user to confirm |
| Rate limited | Wait and retry, inform user |

## Success Criteria

- Target page found by name
- All content properly formatted as Notion blocks
- Content successfully appended to page
- User receives working Notion URL

## Reference

For expected output format, see [references/sample-output.md](references/sample-output.md)