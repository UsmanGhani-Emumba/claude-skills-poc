---
name: publisher
description: Publishing skill for deploying finalized content to Notion. Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
---

# Publisher Skill

## Purpose

Deploy finalized, reviewed content to Notion by **creating a new page under a parent page** with proper formatting.

## Prerequisites

**Required before publishing:**

1. ✅ Finalized blog content (from Reviewer skill)
2. ✅ Notion MCP connection active
3. ✅ **User has a parent page in Notion** where blogs will be created

### User Setup (REQUIRED)

⚠️ **Before publishing, the user must:**

1. Have a parent page in Notion (e.g., "Blog Posts", "My Articles")
2. Share that parent page with the Notion integration (Add connections → select integration)
3. Provide the **parent page name** to Claude

### Connection Check (CRITICAL)

⚠️ **STOP** if Notion MCP is not connected. Inform the user:

> "Notion MCP is not connected. Please ensure:
> 1. Notion MCP server is configured and running
> 2. Your integration token is valid
> 3. Parent page is shared with the integration

> Run `/mcp` command in Claude Code CLI to check connection status."

**Do not attempt publishing without confirmed connection.**

## Workflow

### Create New Page Under Parent (with Auto-Discovery)

1. **Verify connection** — Check Notion MCP is active
2. **Auto-discover pages** — Call `API-post-search` with NO parameters to list all connected pages
3. **Present options** — Show user a list of available pages to choose as parent
4. **User selects parent** — Use `AskUserQuestion` tool to let user pick from the list
5. **Extract blog title** — Get the title from the blog content (first H1 heading)
6. **Create new page** — Use `API-post-page` to create a child page with title and content
7. **Return link** — Provide the new Notion page URL

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  1. API-post-search (no params) → Get all pages         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Parse results → Extract page names and IDs          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. AskUserQuestion → "Select parent page:"             │
│     □ Blog Posts                                        │
│     □ My Articles                                       │
│     □ Published Content                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. API-post-page → Create new page under selected      │
│     parent: {page_id: "selected_id"}                    │
│     properties: {title: [...]}                          │
│     children: [...]                                     │
└─────────────────────────────────────────────────────────┘
```

## Auto-Discovery of Available Pages (PREFERRED)

Instead of asking the user for a page name, **automatically discover** all pages connected to the Notion integration:

### Step 1: List All Connected Pages

Use `API-post-search` WITHOUT a query to get all accessible pages:

```
Tool: mcp__notion__API-post-search
Parameters: (none required - call with empty/no parameters)
```

This returns all pages that have been shared with the Notion integration.

### Step 2: Present Options to User

Parse the search results and present a list of available pages:

```
📋 Available Notion Pages:

1. Blog Posts (page)
2. My Articles (page)
3. Published Content (page)
4. Drafts (page)

Which page should I use as the parent for this blog post?
```

Use the `AskUserQuestion` tool to let the user select from the discovered pages.

### Step 3: Use Selected Page ID

Once the user selects a page, use its `id` as the `parent.page_id` for creating the new blog page.

## Fallback: Manual Page Name

If auto-discovery fails or returns no pages, ask the user:

> "I couldn't find any pages connected to Notion. Please provide the **name of the parent page** where you want to create this blog post.
>
> **Note:** The parent page must be shared with the Notion integration (Page → ⋯ → Add connections)."

## API Usage

### Step 1: Discover Connected Pages

Use `API-post-search` to list all accessible pages:

```
Tool: mcp__notion__API-post-search
Parameters: (call with no parameters to get all pages)
```

The response contains an array of pages with:
- `id` - The page UUID (use this for parent.page_id)
- `properties.title` - The page title
- `object` - "page" or "database"

### Parsing Search Results

Extract page info from results:
```
For each result where object === "page":
  - id: result.id
  - title: result.properties.title.title[0].plain_text (or similar path)
  - url: result.url
```

### Step 2: Create New Page with Content

Use `API-post-page` to create a new child page.

## ⚠️ CRITICAL: MCP Parameter Format

The MCP tool has **strict parameter typing**. You MUST pass parameters as the correct types:

### Parameter Types Table

| Parameter    | Expected Type | How to Pass                                    |
|--------------|---------------|------------------------------------------------|
| `parent`     | **object**    | Pass as object: `{"page_id": "uuid-here"}`     |
| `properties` | **object**    | Pass as object: `{"title": [...]}`             |
| `children`   | **array**     | Pass as array of JSON strings: `["...", "..."]`|

### JSON Validation (MANDATORY)

Before making the API call, **validate every JSON block** in the children array:

1. Each block must be valid JSON
2. Each block must have proper opening AND closing braces
3. Count braces: every `{` needs a matching `}`
4. Count brackets: every `[` needs a matching `]`

Common error pattern to avoid:
```
BAD:  "content": "text"}}}]"     ← Missing closing braces
GOOD: "content": "text"}}]}}     ← All braces balanced
```

### Complete Block Structure

Every paragraph block must follow this EXACT structure:
```json
{
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "Your text here"
        }
      }
    ]
  }
}
```

Count the braces: 5 opening `{`, 5 closing `}` - they must match!

### Correct API Call Example

```
mcp__notion__API-post-page

parent: {"page_id": "2f801e7f-802c-80cd-a17c-d058fe3d60b3"}
        ↑ This is an OBJECT (no outer quotes)

properties: {"title": [{"text": {"content": "Blog Title"}}]}
            ↑ This is an OBJECT (no outer quotes)

children: [
  "{\"type\":\"paragraph\",\"paragraph\":{\"rich_text\":[{\"type\":\"text\",\"text\":{\"content\":\"First paragraph\"}}]}}",
  "{\"type\":\"heading_2\",\"heading_2\":{\"rich_text\":[{\"type\":\"text\",\"text\":{\"content\":\"Section Title\"}}]}}"
]
↑ This is an ARRAY of STRINGS (each string is escaped JSON)
```

### ❌ WRONG - Common Mistakes

```
# Mistake 1: parent as string (has outer quotes)
parent: "{\"page_id\": \"uuid\"}"   ← WRONG!

# Mistake 2: Unbalanced braces in children
children: ["...\"content\":\"text\"}}}]"]   ← WRONG! Missing braces
```

### ✅ CORRECT Format

```
# Correct: parent as object (no outer quotes)
parent: {"page_id": "2f801e7f-802c-80cd-a17c-d058fe3d60b3"}

# Correct: Each child is valid JSON with balanced braces
children: ["{\"type\":\"paragraph\",\"paragraph\":{\"rich_text\":[{\"type\":\"text\",\"text\":{\"content\":\"Text here\"}}]}}"]
```

## Fallback Strategy: Two-Step Publish

If `API-post-page` keeps failing with 400 errors, use this fallback:

### Step 1: Create Empty Page
Create a page with just the title (no children):
```
parent: {"page_id": "parent-uuid"}
properties: {"title": [{"text": {"content": "Blog Title"}}]}
children: []   ← Empty array
```

### Step 2: Append Content
Use `API-patch-block-children` to add content to the new page:
```
block_id: "new-page-id-from-step-1"
children: ["block1", "block2", ...]
```

This separates page creation from content addition, making debugging easier.

## Content Batching Strategy

⚠️ **The Notion API limits blocks in page creation.** Use this strategy:

### For Page Creation (API-post-page)
- **Include first 20-30 blocks** in the initial page creation
- This gives the page a title and initial content

### For Remaining Content (API-patch-block-children)
- **Batch size: 5 blocks maximum** per API call
- Use the new page's ID to append remaining blocks
- Follow the auto-retry loop (see below)

### Two-Phase Upload

```
Phase 1: Create page with title + first batch of content
         └── API-post-page (parent_id, title, first 20 blocks)

Phase 2: Append remaining content in batches
         └── API-patch-block-children (new_page_id, batch of 5 blocks)
         └── API-patch-block-children (new_page_id, batch of 5 blocks)
         └── ...
```

## Auto-Retry Loop (MANDATORY)

**Before starting, create a batch tracking list:**
```
Total blocks: [count]
Blocks in page creation: [first 20]
Remaining blocks: [count - 20]
Batches needed: [remaining / 5, rounded up]
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
Blog Title: "Your Blog Title"
Parent Page: "Blog Posts"

Phase 1: Creating page...
✅ Page created with initial content

Phase 2: Uploading remaining content
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

## Notion Block Format

When converting markdown to Notion blocks:

| Markdown | Notion Block Type |
|----------|-------------------|
| `# Title` | Page title (in properties) |
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
| Permission denied | Ask user to share parent page with integration |
| Parent page not found | Ask user to verify page name and that it's shared |
| Multiple pages found | Show options and ask user to confirm |
| Rate limited (429) | Wait 30 seconds, then auto-retry same batch |
| **400 Bad Request** | **Check parameter types + validate JSON** |
| Timeout | Wait 5 seconds, auto-retry same batch |

### 400 Error Troubleshooting

When receiving a 400 error:

1. **Check `parent` parameter** - Must be object, not string
2. **Check `properties` parameter** - Must be object, not string
3. **Validate all JSON in children** - Every block must have balanced braces
4. **Try empty children first** - Create page without content to isolate issue
5. **Add blocks one at a time** - Find which block causes the error

## Success Criteria

- Parent page found by name
- New child page created with blog title
- All content properly formatted as Notion blocks
- Content successfully added to new page
- User receives working Notion URL for the new page

## Output Format

On successful publish:

```markdown
## ✅ Published Successfully

**New Page Created:** [Blog Title](https://notion.so/...)
**Parent Page:** "Blog Posts"

### Content Summary
- Word count: XXX words
- Sections: X
- Sources cited: X

[Open in Notion](https://notion.so/...)
```

## Reference

For expected output format, see [references/sample-output.md](references/sample-output.md)
