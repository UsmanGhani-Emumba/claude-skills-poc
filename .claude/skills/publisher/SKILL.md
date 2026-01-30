---
name: publisher
description: Publishing skill for deploying finalized content to Notion. Activates after review is complete or when asked to publish/deploy/post content. Triggers on "publish to Notion", "post this to Notion", "deploy the blog", or as the final step in content creation pipelines.
---

# Publisher Skill

## Purpose

Deploy finalized, reviewed content to Notion with proper formatting, metadata, and organization.

## Prerequisites

**Required before publishing:**

1. ✅ Finalized blog content (from Reviewer skill)
2. ✅ Notion MCP connection active
3. ✅ Target workspace/page specified

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
2. **Confirm destination** — Ask user where to publish if not specified
3. **Format content** — Convert markdown to Notion blocks
4. **Create page** — Create new page with blog title
5. **Add metadata** — Apply properties and icon
6. **Publish content** — Write formatted blocks to the page
7. **Return link** — Provide the Notion page URL

## Destination Check

If destination is not specified, ask:

> "Where should I publish this blog?
> - **Default workspace** — Your main Notion workspace
> - **Specific page** — Provide the parent page name
> - **Database** — Add as entry to a blog database"

## Notion Formatting

| Markdown | Notion Block |
|----------|--------------|
| `# Title` | Page title |
| `## Heading` | Heading 2 |
| `### Subheading` | Heading 3 |
| Paragraphs | Paragraph blocks |
| `- item` | Bulleted list |
| `1. item` | Numbered list |
| `> quote` | Quote block |
| `**bold**` | Bold text |
| `*italic*` | Italic text |
| `---` | Divider |
| 💡 Callout | Callout block with icon |

## Page Metadata

When creating the page, include:

- **Title** — Blog title (from H1)
- **Icon** — Relevant emoji based on topic
- **Created** — Current date
- **Status** — "Published"
- **Author** — "AI Generated" or user name if specified
- **Audience** — Target audience (from research brief)

## Error Handling

| Error | Response |
|-------|----------|
| MCP not connected | Guide user to set up connection |
| Permission denied | Check page is shared with integration |
| Page not found | Verify parent page exists |
| Rate limited | Wait and retry, inform user |

## Success Criteria

- Page created with correct title and metadata
- All content properly formatted
- User receives working Notion URL

## Reference

For expected output format, see [references/sample-output.md](references/sample-output.md)