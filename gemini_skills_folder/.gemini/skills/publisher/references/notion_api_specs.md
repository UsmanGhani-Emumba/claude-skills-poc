# Notion API Specification for Publisher

This specification details the endpoints, payloads, and logic for publishing content to Notion via the REST API.

---

## 1. Verify Parent Page
**Endpoint**: `GET /v1/pages/{page_id}`
- **Purpose**: Confirms the integration has access to the parent page.
- **Error Handling**: 
    - 404/403: Stop immediately. The `NOTION_PARENT_ID` is invalid or the page is not shared with the integration.

---

## 2. Create Empty Child Page
**Endpoint**: `POST /v1/pages`
- **Payload**:
```json
{
  "parent": { "page_id": "{NOTION_PARENT_ID}" },
  "properties": {
    "title": {
      "title": [
        { "text": { "content": "{ARTICLE_TITLE}" } }
      ]
    }
  }
}
```
- **Error Handling**: 
    - 400/401/403: Stop. Report "Failed to create initial page".
- **Result**: Extract `id` (the new `page_id`) for appending content.

---

## 3. Append Content (Batched)
**Endpoint**: `PATCH /v1/blocks/{page_id}/children`
- **Payload**:
```json
{
  "children": [
    { "type": "heading_2", "heading_2": { "rich_text": [{ "text": { "content": "Section Title" } }] } },
    { "type": "paragraph", "paragraph": { "rich_text": [{ "text": { "content": "Content..." } }] } }
  ]
}
```
- **Constraints**:
    - **Max 100 blocks per request**.
    - **Max 2,000 characters per rich_text item**.
- **Auto-Batching Logic**:
    1. Count total `content_blocks`.
    2. Divide into chunks of 100 blocks.
    3. Send sequential PATCH requests.
    4. Implement **350ms delay** between requests to respect the ~3 req/s rate limit.
- **Error Handling (429 Too Many Requests)**:
    - On 429: Parse `Retry-After` header or wait 2s, then retry the current batch (up to 2 times).

---

## 4. Metadata Mapping
- **Tags**: Map to a `multi_select` property.
- **Summary**: Map to a `rich_text` property named "Summary".
- **Category**: Map to a `select` property.
- Note: Database property names must match the Notion database schema exactly if the parent is a database.
