# Notion API Request Reference (Python)

This guide provides the exact Python `notion-client` request structures for the three core phases of the publishing workflow.

## 1. Verify Parent Page
Check if the parent page ID is valid and accessible.

```python
# Returns a page object if successful
notion.pages.retrieve(page_id="PARENT_PAGE_UUID")
```

---

## 2. Create Empty Page
Create the initial page container under the parent.

```python
# Returns the new page object including its ID
new_page = notion.pages.create(
    parent={"page_id": "PARENT_PAGE_UUID"},
    properties={
        "title": [
            {
                "text": { "content": "Blog Title" }
            }
        ]
    }
)
page_id = new_page["id"]
```

---

## 3. Append Block Batches
Add content blocks to the newly created page. Ensure batches do not exceed 100 blocks.

```python
# Appends blocks to the specified page
notion.blocks.children.append(
    block_id="NEW_PAGE_UUID",
    children=[
        # List of block objects (see notion_format.md)
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{ "type": "text", "text": { "content": "Sample text content" } }]
            }
        }
    ]
)
```

---

## 4. Handling 429 Errors (Rate Limiting)
When the API returns a 429 status code:
- **Strategy:** Catch the exception and implement exponential backoff.
- **Backoff Sequence:** 2s, 4s, 8s, 16s, 32s.
- **Max Retries:** 5 attempts per batch.