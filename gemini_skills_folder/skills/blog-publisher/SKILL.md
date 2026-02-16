---
name: blog-publisher
description: Publishes content to Notion. Use this skill after the review phase to finalize and save the humanized blog post into a designated Notion workspace.
---

# Blog Publisher

## When to Use This Skill
Activate this skill as the final step of the content creation pipeline. It should be triggered once the `blog-reviewer` has provided a "Ready to Publish" Markdown draft.

## Unified Publishing Workflow
1.  **Preparation:**
    - Save the finalized blog content to a temporary file (e.g., `tmp_blog.md`).
    - Identify the `NOTION_TOKEN` and `NOTION_PARENT_PAGE_ID` from the environment.
2.  **Format Compliance:**
    - Consult [references/notion_format.md](references/notion_format.md) to ensure all Markdown elements (headings, callouts, lists) are converted into the exact JSON block structure required by the Notion API.
3.  **Execution (Script-Driven):**
    - Run the publishing script: `python references/publish.py --token <TOKEN> --parent <PARENT_ID> --title "<TITLE>" --content_file "tmp_blog.md"`.
    - **Note:** The script handles parent page verification, empty page creation, and auto-batching (50 blocks/batch) with exponential backoff for 429 errors.

## Requirements
- Content must be cleanly formatted as per the Style Guide before publishing.
- If the script returns an error, identify the cause (e.g., "401 Unauthorized" or "404 Parent Not Found") and report it.

## Metrics
Report final execution status (Pass/Fail), the total number of blocks published, and the URL of the new Notion page.