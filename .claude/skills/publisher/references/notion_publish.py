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
    db_id = os.getenv("NOTION_DATABASE_ID")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    page_payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": data["title"]}}]},
        },
        "children": [
            _to_notion_block(block) for block in data.get("content_blocks", [])
        ],
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=page_payload)
    resp.raise_for_status()
    result = resp.json()
    print(f"Published: {result.get('url', 'No URL')}")
    return result


def _to_notion_block(block: dict) -> dict:
    btype = block.get("type", "paragraph")
    text = block.get("text", "")
    return {
        "object": "block",
        "type": btype,
        btype: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


if __name__ == "__main__":
    if "--file" in sys.argv:
        idx = sys.argv.index("--file") + 1
        with open(sys.argv[idx]) as f:
            data = json.load(f)
    else:
        data = json.loads(sys.stdin.read())
    publish_to_notion(data)
