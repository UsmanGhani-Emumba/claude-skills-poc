# Notion API Block Formatting Guide

Use the following exact JSON structures for the `children` array when appending blocks.

## 1. Paragraph
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Sample text here. Max 2000 chars." }
      }
    ]
  }
}
```

## 2. Headings (H1, H2, H3)
```json
{
  "object": "block",
  "type": "heading_2",
  "heading_2": {
    "rich_text": [{ "type": "text", "text": { "content": "Section Title" } }]
  }
}
```

## 3. Lists (Bulleted & Numbered)
```json
{
  "object": "block",
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [{ "type": "text", "text": { "content": "List item text" } }]
  }
}
```

## 4. Callout (Notion-Style)
```json
{
  "object": "block",
  "type": "callout",
  "callout": {
    "rich_text": [{ "type": "text", "text": { "content": "Key Insight text" } }],
    "icon": { "emoji": "💡" },
    "color": "gray_background"
  }
}
```

## 5. Divider
```json
{
  "object": "block",
  "type": "divider",
  "divider": {}
}
```

## 6. Quote
```json
{
  "object": "block",
  "type": "quote",
  "quote": {
    "rich_text": [{ "type": "text", "text": { "content": "Famous quote text" } }]
  }
}
```

## Crucial API Constraints:
- **Rich Text Limit:** Each `content` string must be **under 2,000 characters**. If a paragraph is longer, it must be split into multiple paragraph blocks.
- **Batch Size:** A single `children.append` call can accept a maximum of **100 blocks**.
- **Parent ID:** Must be a valid UUID.