---
name: blog-publisher
description: Publishes content to Notion with auto-batching.
---
# Blog Publisher
## Workflow
1. Prepare `tmp_blog.md`.
2. Consult [references/notion_format.md](references/notion_format.md).
3. Run `python references/publish.py --token <T> --parent <P> --title <TI> --content_file tmp_blog.md`.
