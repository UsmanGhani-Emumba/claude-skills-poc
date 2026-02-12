---
name: publisher
description: Publishing skill for deploying content to Notion. Activates when the reviewer has finalized the blog post.
---

# Publisher Skill

## Purpose
Deploy the finalized blog post to Notion with proper formatting and organization.

## Workflow
1. **Discover Target**: Use the discovery tool ([notion_discover.js](references/notion_discover.js)) to verify availability.
   - **Primary Parent**: `Gemini Workspace` (ID: `2ff01e7f-802c-8041-bb7b-f826722f02da`).
   - All Gemini blogs **MUST** be published here.
2. **Transform to JSON**: Convert markdown into a JSON payload locally.
3. **Execute Publication**: **CRITICAL**: Use the `notion_publish` tool to deploy the content.
4. **Autonomous Action**: Do NOT stop to ask for the JSON or for confirmation. If the blog content is provided in your prompt, proceed directly through discovery to publication in a single sequence.

## Error Handling & Retry Policy
- **Rate Limits (429)**: The toolbox handles exponential backoff automatically.
- **Max Retries**: The engine is configured for **5 retries**. 
- **Strategy**: If publication fails after retries, log the final error and notify the user. Do not attempt to publish to a different parent without approval.

## Supported Block Types
Use these types for the `blocks` list:
- `paragraph`: Standard text content.
- `heading_2`: Main section headers.
- `heading_3`: Sub-headers.
- `bulleted_list_item`: For lists and sources.
- `numbered_list_item`: For ordered steps.
- `code`: For technical snippets.
- `divider`: For visual separation.

## JSON Payload Example
```json
{
  "title": "Blog Title",
  "blocks": [
    { "type": "paragraph", "content": "Intro text" },
    { "type": "heading_2", "content": "Main Section" },
    { "type": "divider" }
  ]
}
```

---

## References
- [Block Structures](references/block-structures.md) - JSON structures for Notion blocks
- [Sample Output](references/sample-output.md) - Example of a successfully published post payload
- [Notion Publish Config](references/notion-publish.js) - Underlying deployment engine
- [Notion Discovery Config](references/notion-discover.js) - Page search implementation
