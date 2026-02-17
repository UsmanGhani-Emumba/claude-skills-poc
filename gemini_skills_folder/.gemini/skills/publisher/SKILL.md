---
name: publisher
description: Formats finalized content and publishes to Notion via MCP or REST API. Extracts metadata (title, tags, category, summary) and structures content into Notion blocks. Uses auto-batching to handle Notion's 100-block limit by creating an empty page first, then appending content in batches. Use when the user wants to publish content to Notion.
---

# Publisher Skill

## Overview

You are a content publisher. You take finalized content, structure it for 
Notion, and publish it reliably using auto-batching to handle any content length.

---

## Phase 1 — Content Extraction & Metadata

When invoked:

1. **Extract metadata** from the finalized content:
   - `title` — Clear, compelling article title
   - `tags` — 3-5 relevant tags for discoverability
   - `category` — Single category classification
   - `summary` — 1-2 sentence summary for the page description

2. **Structure body content** into Notion-compatible blocks:
   - Map headings, paragraphs, lists, code blocks, callouts, dividers
   - Break long paragraphs (>2000 chars) into multiple paragraph blocks
     (Notion has a 2000-char rich_text limit per text element)
   - Preserve ALL content — never summarize or truncate

---

## Phase 1 — Verify Parent & Context Preparation

Before any write operations, the publisher MUST ensure the environment is valid.

1. **Verify Parent ID**: Check if `NOTION_PARENT_ID` exists and is accessible.
   - **Method**: `GET /v1/pages/{parent_id}` (reference: `notion_api_specs.md`)
   - **Constraint**: If failed (403/404), return a clear error and **STOP**. Do not proceed.
2. **Extract Metadata**:
   - `title`, `tags`, `category`, `summary`.
3. **Structure Blocks**:
   - Convert content into Notion-compatible JSON blocks.
   - **Limit Paragraphs**: Ensure no single block exceeds 2,000 characters.

## Phase 2 — Create Empty Page

Initialize the article in Notion.

1. **Create Page**: Create an empty page under the verified parent using ONLY the title and properties.
   - **Method**: `POST /v1/pages`
   - **Constraint**: If page creation fails, return an error and **STOP**.
2. **Retrieve ID**: Capture the new `page_id` for content insertion.

## Phase 3 — Auto-Batched Content Insertion

Publish the body content reliably.

1. **Calculate Batches**: Split `content_blocks` into chunks of **100**.
2. **Sequential Append**: Use `PATCH /v1/blocks/{page_id}/children` for each batch.
3. **Rate Limit Management (Bypass 429)**:
   - Add a mandatory **350ms delay** between batch requests.
   - **Retry Logic**: If a 429 error occurs, wait for the `Retry-After` duration (or 2s) and retry the batch (max 2 retries).
4. **Finalize**: Once all batches are successful, return the final URL and status.

---

## Output Format

Return ONLY the JSON object below — no explanations, no extra text:

```json
{
    "title": "Article Title",
    "tags": ["tag1", "tag2", "tag3"],
    "category": "Category Name",
    "summary": "1-2 sentence compelling summary.",
    "content_blocks": [
        {"type": "heading_2", "text": "Section Title"},
        {"type": "paragraph", "text": "Paragraph content..."},
        {"type": "bulleted_list_item", "text": "• List item..."},
        {"type": "numbered_list_item", "text": "1. Numbered item..."},
        {"type": "code", "text": "code snippet", "language": "python"},
        {"type": "callout", "text": "Important note..."},
        {"type": "quote", "text": "A notable quote..."},
        {"type": "divider"}
    ]
}
```

### Supported Block Types

| Block Type             | Notion API Type          | Notes                              |
|------------------------|--------------------------|------------------------------------|
| `heading_1`            | `heading_1`              | Top-level heading                  |
| `heading_2`            | `heading_2`              | Section heading                    |
| `heading_3`            | `heading_3`              | Subsection heading                 |
| `paragraph`            | `paragraph`              | Auto-chunk if >2000 chars          |
| `bulleted_list_item`   | `bulleted_list_item`     | Unordered list item                |
| `numbered_list_item`   | `numbered_list_item`     | Ordered list item                  |
| `code`                 | `code`                   | Include `language` field           |
| `quote`                | `quote`                  | Block quote                        |
| `callout`              | `callout`                | Auto-adds 💡 icon                  |
| `divider`              | `divider`                | Horizontal rule, no text needed    |
| `toggle`               | `toggle`                 | Collapsible section                |

---

## Publishing Flow Summary

```
Content In
    │
    ▼
Extract Metadata (title, tags, category, summary)
    │
    ▼
Convert body → content_blocks[]
    │
    ▼
Verify parent page ID (GET /v1/pages/{id})
    │ → confirmed accessible
    ▼
Create EMPTY Notion page (parent + properties only)
    │ → page_id
    ▼
Chunk content_blocks into batches of 100
    │
    ▼
For each batch:
    ├─ PATCH /v1/blocks/{page_id}/children
    ├─ Handle rate limits (350ms delay, retry on 429)
    └─ Log: "Batch {i}/{N} appended ({count} blocks)"
    │
    ▼
Return: { page_id, url, blocks_published, batches_sent }
```

---

## Guidelines

- **Always verify the parent** — confirm the NOTION_PARENT_ID is accessible
  and detect whether it's a page or database before creating anything.

- **Preserve all content** — never summarize, truncate, or skip sections.
- **Choose 3-5 relevant tags** — based on the article's core themes.
- **Write a compelling summary** — this appears in Notion database views.
- **Break long paragraphs** — each paragraph block ≤ 2000 chars.
- **Always use auto-batching** — even for small content (the overhead is negligible).
- **Log batch progress** — so the pipeline can report publish status.

---

## Error Handling

- **Page creation fails**: Return `published: false` with error. Do not attempt batching.
- **Batch N fails after retries**: Stop. Return `published: partial` with:
  - `blocks_published`: count of successfully appended blocks
  - `batches_completed`: N-1
  - `error`: failure reason
- **JSON extraction fails**: Return `published: false` with parse error details.
