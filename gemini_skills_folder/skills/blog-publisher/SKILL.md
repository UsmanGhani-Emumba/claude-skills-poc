---
name: blog-publisher
description: Publishes content to Notion following a strict 3-step sequence: Parent Verification, Page Creation, and Resilient Block Batching.
---

# Blog Publisher

## When to Use This Skill
Activate this skill after the blog review phase is complete. It transforms the final Markdown draft into a live Notion page.

## Sequential Publishing Workflow
You must follow these steps exactly, referencing the API patterns in the guides:

### Step 1: Parent Verification
Identify and verify the parent page via the provided `NOTION_PARENT_PAGE_ID`.
- Consult [references/notion_api_calls.md](references/notion_api_calls.md) for the retrieval pattern.
- **If found:** Proceed to Step 2.
- **If not found:** Halt and report a "Parent Page Not Found" error.

### Step 2: Empty Page Creation
Create a new, empty page under the verified parent.
- Consult [references/notion_api_calls.md](references/notion_api_calls.md) for the creation payload.
- **If created:** Proceed to Step 3.
- **If creation fails:** Halt and report a "Page Creation Failed" error.

### Step 3: Resilient Block Appending
Convert content into blocks and append them.
- Consult [references/notion_format.md](references/notion_format.md) for individual block JSON structures.
- Consult [references/notion_api_calls.md](references/notion_api_calls.md) for the batch patching pattern.
- **Auto-Batching:** Push groups of 50 blocks.
- **429 Handling:** Use exponential backoff as documented in the API guide.

## Execution
Run the script: `python references/publish.py --token <TOKEN> --parent <ID> --title "<TITLE>" --content_file "tmp_blog.md"`

## Metrics & Error Reporting
Report status (Pass/Fail) and specific step failures. Include the final Notion URL upon success.