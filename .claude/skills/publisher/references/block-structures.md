# Notion Block Structure Reference

JSON structures for constructing Notion API block payloads.

---

## Paragraph

**Basic paragraph:**
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [{"type": "text", "text": {"content": "Your paragraph text here"}}]
  }
}
```

**Paragraph with bold text:**
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "Bold text"}, "annotations": {"bold": true}},
      {"type": "text", "text": {"content": " and normal text"}}
    ]
  }
}
```

**Paragraph with italic text:**
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "Italic text"}, "annotations": {"italic": true}}
    ]
  }
}
```

---

## Headings

**Heading 2:**
```json
{
  "object": "block",
  "type": "heading_2",
  "heading_2": {
    "rich_text": [{"type": "text", "text": {"content": "Section Title"}}]
  }
}
```

**Heading 3:**
```json
{
  "object": "block",
  "type": "heading_3",
  "heading_3": {
    "rich_text": [{"type": "text", "text": {"content": "Subsection Title"}}]
  }
}
```

---

## Lists

**Bulleted list item:**
```json
{
  "object": "block",
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [{"type": "text", "text": {"content": "List item text"}}]
  }
}
```

**Numbered list item:**
```json
{
  "object": "block",
  "type": "numbered_list_item",
  "numbered_list_item": {
    "rich_text": [{"type": "text", "text": {"content": "Numbered item text"}}]
  }
}
```

**List item with bold label:**
```json
{
  "object": "block",
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [
      {"type": "text", "text": {"content": "Label: "}, "annotations": {"bold": true}},
      {"type": "text", "text": {"content": "Description text"}}
    ]
  }
}
```

---

## Links

**Link in text:**
```json
{
  "object": "block",
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [
      {"type": "text", "text": {"content": "Source Title", "link": {"url": "https://example.com"}}}
    ]
  }
}
```

**Paragraph with inline link:**
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "Read more at "}},
      {"type": "text", "text": {"content": "this article", "link": {"url": "https://example.com"}}},
      {"type": "text", "text": {"content": " for details."}}
    ]
  }
}
```

---

## Code Block

```json
{
  "object": "block",
  "type": "code",
  "code": {
    "rich_text": [{"type": "text", "text": {"content": "const x = 1;\nconsole.log(x);"}}],
    "language": "javascript"
  }
}
```

**Supported languages:** `javascript`, `typescript`, `python`, `java`, `bash`, `json`, `html`, `css`, `sql`, `markdown`, and more.

---

## Divider

```json
{
  "object": "block",
  "type": "divider",
  "divider": {}
}
```

---

## Annotations Reference

Available annotations for `rich_text` items:

```json
"annotations": {
  "bold": true,
  "italic": true,
  "strikethrough": true,
  "underline": true,
  "code": true,
  "color": "default"
}
```

**Colors:** `default`, `gray`, `brown`, `orange`, `yellow`, `green`, `blue`, `purple`, `pink`, `red`, plus `*_background` variants (e.g., `blue_background`).

---

## Combining Multiple Annotations

```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "Bold and italic"}, "annotations": {"bold": true, "italic": true}},
      {"type": "text", "text": {"content": " with "}},
      {"type": "text", "text": {"content": "code"}, "annotations": {"code": true}}
    ]
  }
}
```
