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

### Step 2: Append Content (with Auto-Retry)

Use `API-patch-block-children` to add content:

```
block_id: "<page_id from search results>"
children: [array of block objects as JSON string]
```

## Automated Upload Strategy (CRITICAL)

⚠️ **The Notion API is prone to 400 errors.** Use this automated approach:

### Batch Configuration
- **Batch size: 5 blocks maximum** (smaller = more reliable)
- **Never exceed 5 blocks per API call**
- Convert all content to blocks first, then split into batches

### Auto-Retry Loop (MANDATORY)

**Before starting, create a batch tracking list:**
```
Total blocks: [count]
Batches needed: [total / 5, rounded up]
Current batch: 1
```

**For each batch, follow this loop:**

```
REPEAT until current_batch > total_batches:
  1. Attempt API call for batch [current_batch]
  2. IF success:
     - Log: "✅ Batch [current_batch] uploaded successfully"
     - Increment current_batch
     - Continue to next batch
  3. IF 400 error:
     - Log: "⚠️ Batch [current_batch] failed - retrying..."
     - Wait 2 seconds
     - Retry SAME batch (up to 3 attempts)
     - If still failing after 3 attempts:
       a. Try with even smaller batch (2-3 blocks)
       b. If still failing, try blocks one at a time
  4. IF rate limited (429):
     - Wait 30 seconds
     - Retry same batch
  5. NEVER skip a batch - keep retrying until success
  6. Report progress: "[current_batch]/[total_batches] batches complete"
```

### Progress Tracking Template

Use this format to track and display progress:
```
📤 Publishing Progress
━━━━━━━━━━━━━━━━━━━━
Total blocks: XX
Batch size: 5
Total batches: XX

[■■■■■□□□□□] 50% - Batch 5/10
✅ Batch 1: Success
✅ Batch 2: Success
✅ Batch 3: Success
✅ Batch 4: Success
🔄 Batch 5: In progress...
```

### 400 Error Recovery Strategies

If a batch keeps failing with 400:

1. **Reduce batch size** — Try 3 blocks, then 2, then 1
2. **Check block content** — Remove special characters, emojis, or unusual formatting
3. **Simplify rich text** — Use plain text without formatting
4. **Split long paragraphs** — Break paragraphs over 2000 characters

### Example: Single Block Upload (Fallback)

When batches fail, upload one block at a time:
```json
[{"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Your text"}}]}}]
```

### Completion Confirmation

Only report success when ALL batches are uploaded:
```
✅ Publishing Complete!
━━━━━━━━━━━━━━━━━━━━
All [XX] batches uploaded successfully.
Total blocks published: [XX]
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
| Rate limited (429) | Wait 30 seconds, then auto-retry same batch |
| **400 Bad Request** | **Auto-retry with smaller batch (see below)** |
| Timeout | Wait 5 seconds, auto-retry same batch |

### 400 Error Auto-Recovery Protocol

When receiving a 400 error, follow this escalation:

1. **First attempt failed** → Retry same batch immediately
2. **Second attempt failed** → Wait 2 seconds, retry same batch
3. **Third attempt failed** → Reduce batch size by half, retry
4. **Fourth attempt failed** → Try uploading blocks one at a time
5. **Single block still failing** → Simplify that block's content (remove special chars/formatting)
6. **Still failing** → Skip problematic block, log it, continue with remaining blocks

**NEVER stop the upload process due to errors.** Always continue until all possible content is uploaded.

## Success Criteria

- Target page found by name
- All content properly formatted as Notion blocks
- Content successfully appended to page
- User receives working Notion URL

## Reference

For expected output format, see [references/sample-output.md](references/sample-output.md)