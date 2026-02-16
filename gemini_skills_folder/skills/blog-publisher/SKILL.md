---
name: blog-publisher
description: Publishes content to Notion following a strict 3-step sequence: Parent Verification, Page Creation, and Resilient Block Batching.
---

# Blog Publisher

## When to Use This Skill
Activate this skill after the blog review phase is complete. It transforms the final Markdown draft into a live Notion page.

## Sequential Publishing Workflow
You must follow these steps exactly:

### Step 1: Parent Verification
Identify and verify the parent page via the provided `NOTION_PARENT_PAGE_ID`. 
- **If found:** Proceed to Step 2.
- **If not found:** Halt and report a "Parent Page Not Found" error.

### Step 2: Empty Page Creation
Create a new, empty page using the blog title as the primary property under the verified parent.
- **If created:** Proceed to Step 3.
- **If creation fails:** Halt and report a "Page Creation Failed" error.

### Step 3: Resilient Block Appending
Convert the Markdown content into Notion-compatible JSON blocks (referencing [references/notion_format.md](references/notion_format.md)) and append them to the new page.
- **Auto-Batching:** Push blocks in groups of 50 to comply with Notion's size and performance standards.
- **429 Handling:** Use exponential backoff to automatically retry if rate limits are encountered.
- Ensure all content is added sequentially without skipping blocks.

## Execution
Run the script: `python references/publish.py --token <TOKEN> --parent <ID> --title "<TITLE>" --content_file "tmp_blog.md"`

## Metrics & Error Reporting
Report the status (Pass/Fail). If it fails, specify which Step (1, 2, or 3) failed and the exact error returned by the script. Output the final Notion URL upon success.
