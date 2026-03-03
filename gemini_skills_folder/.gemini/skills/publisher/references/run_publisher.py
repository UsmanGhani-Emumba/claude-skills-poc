"""
Standalone Notion publisher. Reads a JSON payload from adhd_payload.json
and publishes it to Notion via the REST API (no external dependencies).
"""
import importlib.util
import json
import os
import sys
import time
import requests

# ── Load .env manually ──────────────────────────────────────────────────────
env_path = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', '..', '.env'
)
env_path = os.path.abspath(env_path)
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# ── Notion REST helpers ───────────────────────────────────────────────────────
BATCH_SIZE = 100
INTER_BATCH_DELAY = 0.35
MAX_RETRIES = 2


def _to_notion_block(block):
    btype = block.get("type", "paragraph").lower()
    text = block.get("text", "")
    if btype == "divider":
        return {"object": "block", "type": "divider", "divider": {}}
    chunks = [text[i:i + 2000] for i in range(0, max(len(text), 1), 2000)]
    rich_text = [{"type": "text", "text": {"content": c}} for c in chunks]
    notion_block = {"object": "block", "type": btype, btype: {"rich_text": rich_text}}
    if btype == "callout":
        notion_block["callout"]["icon"] = {"type": "emoji", "emoji": "💡"}
    elif btype == "code":
        notion_block["code"]["language"] = block.get("language", "plain text")
    return notion_block


def _verify_parent(parent_id, headers):
    resp = requests.get(f"https://api.notion.com/v1/pages/{parent_id}", headers=headers)
    if resp.status_code == 200:
        page = resp.json()
        props = page.get("properties", {})
        title = "Untitled"
        for prop in props.values():
            if prop.get("type") == "title" and prop.get("title"):
                title = "".join(t.get("plain_text", "") for t in prop["title"])
                break
        print(f"Verified parent: '{title}' (page_id: {parent_id})")
        return title
    raise ValueError(
        f"Parent page '{parent_id}' not found or not shared with integration. "
        f"Status: {resp.status_code}. Details: {resp.text[:200]}"
    )


def _chunk(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _append_batch_with_retry(page_id, batch, headers, batch_num, total_batches):
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            backoff = 1 if attempt == 1 else 3
            time.sleep(backoff)
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": batch},
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 2))
            time.sleep(retry_after)
            continue
        if resp.status_code < 400:
            return len(batch)
    raise RuntimeError(
        f"Batch {batch_num}/{total_batches} failed after {MAX_RETRIES} retries: "
        f"{resp.status_code} {resp.text[:200]}"
    )


def _publish_to_notion_rest(data):
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
    if not api_key:
        raise ValueError("NOTION_API_KEY must be set in .env")
    if not parent_id:
        raise ValueError("NOTION_PARENT_PAGE_ID must be set in .env")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    print(f"Phase 1: Verifying parent {parent_id}...")
    _verify_parent(parent_id, headers)

    blocks = data.get("content_blocks", [])
    children = [_to_notion_block(block) for block in blocks]
    batches = _chunk(children, BATCH_SIZE)

    print(f"Phase 2: Creating empty child page under {parent_id}...")
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"text": {"content": data["title"]}}]}
        },
    }
    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=page_payload)
    resp.raise_for_status()
    result = resp.json()
    page_id = result["id"]
    notion_url = result.get("url", "N/A")
    print(f"Page created: {page_id}")
    print(f"URL: {notion_url}")

    blocks_published = 0
    if batches:
        print(f"Phase 3: Appending {len(children)} blocks in {len(batches)} batch(es)...")
        for i, batch in enumerate(batches, 1):
            blocks_published += _append_batch_with_retry(page_id, batch, headers, i, len(batches))
            print(f"  Batch {i}/{len(batches)} appended ({blocks_published} blocks total)")
            if i < len(batches):
                time.sleep(INTER_BATCH_DELAY)
    else:
        print("Phase 3: Skipping (no blocks to append)")

    result["blocks_published"] = blocks_published
    result["batches_sent"] = len(batches)
    result["notion_url"] = notion_url
    return result


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    payload_path = os.path.join(os.path.dirname(__file__), "adhd_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        result = _publish_to_notion_rest(data)
        print("\n=== PUBLISH RESULT ===")
        print(f"Status  : passed")
        print(f"URL     : {result['notion_url']}")
        print(f"Blocks  : {result['blocks_published']}")
        print(f"Batches : {result['batches_sent']}")
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
