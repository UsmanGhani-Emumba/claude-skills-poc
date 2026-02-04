# Sample Publisher Output

**Input:** Reviewed blog post about remote work trends

**Action:** Auto-discover pages → User selects parent → Create new page

---

## Auto-Discovery Flow

### Step 1: Discover Connected Pages

```
Tool: mcp__notion__API-post-search
Parameters: (none)

Response:
{
  "results": [
    {
      "id": "abc123-def456-...",
      "object": "page",
      "properties": {
        "title": {"title": [{"plain_text": "Blog Posts"}]}
      },
      "url": "https://notion.so/..."
    },
    {
      "id": "xyz789-uvw012-...",
      "object": "page",
      "properties": {
        "title": {"title": [{"plain_text": "My Articles"}]}
      },
      "url": "https://notion.so/..."
    }
  ]
}
```

### Step 2: Present Options (AskUserQuestion)

```
📋 Found 2 Notion pages connected to the integration:

Select parent page:
  ○ Blog Posts
  ○ My Articles
```

### Step 3: User Selects → Create Page

User selects "Blog Posts" → Use page_id `abc123-def456-...` as parent

---

## Success Output (New Page Creation)

```markdown
## ✅ Published Successfully

**New Page Created:** [The Great Office Tug-of-War: Remote Work in 2025](https://notion.so/workspace/the-great-office-tug-of-war-abc123)
**Parent Page:** "Blog Posts"

### Publishing Progress
📤 Publishing Progress
━━━━━━━━━━━━━━━━━━━━
Blog Title: "The Great Office Tug-of-War: Remote Work in 2025"
Parent Page: "Blog Posts"

Phase 1: Creating page...
✅ Page created with initial content (ID: abc123-def456)

Phase 2: Uploading remaining content
Total blocks: 25
Blocks in page creation: 20
Remaining blocks: 5
Batches needed: 1

[■■■■■■■■■■] 100% - Complete
✅ All batches uploaded successfully

### Content Summary
- Word count: 892 words
- Sections: 4
- Sources cited: 4

[Open in Notion](https://notion.so/workspace/the-great-office-tug-of-war-abc123)
```

---

## API Call Sequence Example

### Step 1: Search for Parent Page
```
Tool: API-post-search
Input: query: "Blog Posts"
Output: { "id": "parent-page-id-123", "title": "Blog Posts", ... }
```

### Step 2: Create New Page
```
Tool: API-post-page
Input:
  parent: { "page_id": "parent-page-id-123" }
  properties: { "title": [{ "text": { "content": "The Great Office Tug-of-War: Remote Work in 2025" }}] }
  children: [
    { "type": "paragraph", "paragraph": { "rich_text": [{ "type": "text", "text": { "content": "Introduction..." }}]}},
    { "type": "heading_2", "heading_2": { "rich_text": [{ "type": "text", "text": { "content": "The Flexibility Divide" }}]}},
    ... (first 20 blocks)
  ]
Output: { "id": "new-page-id-456", "url": "https://notion.so/...", ... }
```

### Step 3: Append Remaining Content (if needed)
```
Tool: API-patch-block-children
Input:
  block_id: "new-page-id-456"
  children: [ ... remaining blocks in batches of 5 ... ]
Output: { "results": [...] }
```

---

## Parent Page Not Found Output

```markdown
## ⚠️ Parent Page Not Found

I couldn't find a page named "Blog Posts" in your Notion workspace.

### Please check:
1. The parent page exists in Notion
2. The page name matches exactly (case-sensitive)
3. The page is shared with your Notion integration

**To share with integration:**
1. Open the parent page in Notion
2. Click ⋯ menu → Add connections
3. Select your integration
4. Tell me the parent page name again
```

---

## Permission Error Output

```markdown
## ❌ Publishing Failed

**Error:** Permission denied for parent page "Blog Posts"

### How to Fix
1. Open your parent page in Notion
2. Click ⋯ menu → Add connections
3. Select your integration
4. Try publishing again
```

---

## Partial Upload Output (with retries)

```markdown
## ✅ Published with Retries

**New Page Created:** [The Great Office Tug-of-War: Remote Work in 2025](https://notion.so/...)
**Parent Page:** "Blog Posts"

### Publishing Progress
📤 Publishing Progress
━━━━━━━━━━━━━━━━━━━━
Blog Title: "The Great Office Tug-of-War: Remote Work in 2025"
Parent Page: "Blog Posts"

Phase 1: Creating page...
✅ Page created with initial content

Phase 2: Uploading remaining content
Total blocks: 35
Remaining after page creation: 15
Batches needed: 3

✅ Batch 1/3: Success
⚠️ Batch 2/3: Failed (400) - Retrying...
⚠️ Batch 2/3: Failed (400) - Reducing batch size...
✅ Batch 2/3: Success (batch size: 2)
✅ Batch 3/3: Success

[■■■■■■■■■■] 100% - Complete

### Content Summary
- Word count: 892 words
- Sections: 4
- Sources cited: 4
- Retries needed: 2

[Open in Notion](https://notion.so/...)
```

---

## What Makes This Good

- **Automatic page creation** — No need to pre-create empty pages
- **Two-phase upload** — Creates page with initial content, then appends rest
- **Robust retry logic** — Handles API errors gracefully
- **Clear progress tracking** — User sees what's happening
- **Immediate link** — User can access published content right away
- **Content summary** — Confirms what was published
- **Clear error guidance** — If it fails, user knows how to fix it
