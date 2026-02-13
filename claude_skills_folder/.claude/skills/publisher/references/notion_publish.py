#!/usr/bin/env python3
"""
Standalone Notion publishing script bundled with the publisher skill.
Reads JSON from stdin or a file, publishes to Notion via API.

Usage:
    echo '{"title": "..."}' | python notion_publish.py
    python notion_publish.py --file output.json
"""
import json
import os
import sys
import requests


def publish_to_notion(data: dict) -> dict:
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = os.getenv("NOTION_DATABASE_ID")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    children = [_to_notion_block(block) for block in data.get("content_blocks", [])]
    first_batch = children[:100]
    remaining = children[100:]

    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"text": {"content": data["title"]}}],
        },
        "children": first_batch,
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=page_payload)

    # Fall back to database parent if page parent fails
    if resp.status_code in (400, 404):
        db_payload = {
            "parent": {"database_id": parent_id},
            "properties": {
                "Name": {"title": [{"text": {"content": data["title"]}}]},
            },
            "children": first_batch,
        }
        resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=db_payload)

    resp.raise_for_status()
    result = resp.json()
    print(f"Published: {result.get('url', 'No URL')}")

    # Append remaining blocks in batches of 100
    page_id = result["id"]
    while remaining:
        batch = remaining[:100]
        remaining = remaining[100:]
        requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": batch},
        ).raise_for_status()

    return result


def _to_notion_block(block: dict) -> dict:
    btype = block.get("type", "paragraph")
    text = block.get("text", "")

    if btype == "divider":
        return {"object": "block", "type": "divider", "divider": {}}

    chunks = [text[i:i + 2000] for i in range(0, max(len(text), 1), 2000)]
    rich_text = [{"type": "text", "text": {"content": c}} for c in chunks]

    notion_block = {"object": "block", "type": btype, btype: {"rich_text": rich_text}}

    if btype == "callout":
        notion_block["callout"]["icon"] = {"type": "emoji", "emoji": "💡"}

    return notion_block


if __name__ == "__main__":
    if "--file" in sys.argv:
        idx = sys.argv.index("--file") + 1
        with open(sys.argv[idx]) as f:
            data = json.load(f)
    else:
        data = json.loads(sys.stdin.read())
    publish_to_notion(data)
