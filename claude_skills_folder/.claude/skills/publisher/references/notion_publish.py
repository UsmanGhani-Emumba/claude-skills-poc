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
import time
import requests

BATCH_SIZE = 100
INTER_BATCH_DELAY = 0.35   # 350ms between batches
MAX_RETRIES = 2


def _verify_parent(parent_id: str, headers: dict) -> str:
    """Verify the parent page exists and is accessible.

    Returns:
        parent_title — e.g. "Claude Workspace"
    """
    resp = requests.get(
        f"https://api.notion.com/v1/pages/{parent_id}",
        headers=headers,
    )
    if resp.status_code == 200:
        page = resp.json()
        props = page.get("properties", {})
        title = "Untitled"
        for prop in props.values():
            if prop.get("type") == "title" and prop.get("title"):
                title = "".join(t.get("plain_text", "") for t in prop["title"])
                break
        print(f"Verified parent: '{title}' (page_id)")
        return title

    print(
        f"Error: Parent page '{parent_id}' not found or not shared with integration. "
        f"Status: {resp.status_code}",
        file=sys.stderr,
    )
    sys.exit(1)


def _chunk(lst: list, size: int) -> list:
    """Split a list into chunks of `size`."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def publish_to_notion(data: dict) -> dict:
    """Publish to Notion with parent verification + empty-page-first auto-batching."""
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = os.getenv("NOTION_PARENT_ID")

    if not api_key or not parent_id:
        print("Error: NOTION_API_KEY and NOTION_PARENT_ID must be set.", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # ── Step 0: Verify parent page exists ──────────────────────────────────
    parent_title = _verify_parent(parent_id, headers)

    children = [_to_notion_block(block) for block in data.get("content_blocks", [])]
    batches = _chunk(children, BATCH_SIZE)
    total_blocks = len(children)

    print(f"Total blocks: {total_blocks} → {len(batches)} batch(es)")

    # ── Step 1: Create EMPTY child page (no children) ─────────────────────
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"text": {"content": data["title"]}}],
        },
        # NO children — empty page first
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=page_payload)
    resp.raise_for_status()
    result = resp.json()
    page_id = result["id"]
    print(f"Page created: {page_id}")
    print(f"URL: {result.get('url', 'N/A')}")

    # ── Step 2: Append content in batches of 100 ───────────────────────────
    blocks_published = 0

    for i, batch in enumerate(batches, 1):
        success = False
        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                backoff = 1 if attempt == 1 else 3
                print(f"  Retry {attempt}/{MAX_RETRIES} after {backoff}s...")
                time.sleep(backoff)

            append_resp = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                json={"children": batch},
            )

            # Rate limited — honour Retry-After
            if append_resp.status_code == 429:
                retry_after = int(append_resp.headers.get("Retry-After", 1))
                print(f"  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            if append_resp.status_code < 400:
                blocks_published += len(batch)
                print(f"Batch {i}/{len(batches)} appended ({len(batch)} blocks, total: {blocks_published}/{total_blocks})")
                success = True
                break

            print(f"  Batch {i} attempt {attempt + 1} failed ({append_resp.status_code})")

        if not success:
            print(f"FAILED after {MAX_RETRIES} retries on batch {i}. Published {blocks_published}/{total_blocks} blocks.", file=sys.stderr)
            return result

        if i < len(batches):
            time.sleep(INTER_BATCH_DELAY)

    print(f"\nDone! {blocks_published} blocks published across {len(batches)} batch(es).")
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
