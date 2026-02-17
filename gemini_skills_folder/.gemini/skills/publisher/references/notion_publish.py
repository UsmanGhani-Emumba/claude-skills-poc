#!/usr/bin/env python3
"""
Notion publishing skill and standalone script.
Reads JSON from stdin/file or executes as a skill within the orchestrator.

Usage:
    echo '{"title": "..."}' | python notion_publish.py
    python notion_publish.py --file output.json
"""
import json
import os
import sys
import time
import re
import requests

try:
    from base import BaseSkill
except ImportError:
    # Fallback for standalone execution
    class BaseSkill:
        def __init__(self, client, model):
            self.client = client
            self.model = model
        def execute(self, user_message, context=None):
            return {"content": user_message}

BATCH_SIZE = 100
INTER_BATCH_DELAY = 0.35   # 350ms between batches
MAX_RETRIES = 2


def _extract_json_from_content(text: str) -> dict:
    """Extract JSON from LLM output that may contain markdown fences or extra text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from publisher output: {text[:200]}")


def _to_notion_block(block: dict) -> dict:
    """Convert a simple block dict to Notion API block format."""
    btype = block.get("type", "paragraph")
    text = block.get("text", "")

    # Divider has no rich_text
    if btype == "divider":
        return {"object": "block", "type": "divider", "divider": {}}

    # Notion rich_text has a 2000-char limit per text object — chunk if needed
    chunks = [text[i:i + 2000] for i in range(0, max(len(text), 1), 2000)]
    rich_text = [{"type": "text", "text": {"content": c}} for c in chunks]

    notion_block = {"object": "block", "type": btype, btype: {"rich_text": rich_text}}

    # Callout requires an icon
    if btype == "callout":
        notion_block["callout"]["icon"] = {"type": "emoji", "emoji": "💡"}

    return notion_block


def _verify_parent(parent_id: str, headers: dict) -> str:
    """Verify the parent page exists and is accessible.

    Returns:
        parent_title — e.g. "Claude Workspace"

    Raises:
        ValueError if the parent page is not accessible.
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
        return title

    raise ValueError(
        f"Parent page '{parent_id}' not found or not shared with integration. "
        f"Status: {resp.status_code}. Ensure the Notion integration has access to the page."
    )


def _chunk(lst: list, size: int) -> list:
    """Split a list into chunks of `size`."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _append_batch_with_retry(page_id: str, batch: list, headers: dict,
                              batch_num: int, total_batches: int) -> int:
    """Append a single batch, retrying on failure. Returns blocks appended."""
    resp = None
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            backoff = 1 if attempt == 1 else 3
            time.sleep(backoff)

        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": batch},
        )

        # Rate limited — honour Retry-After
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 1))
            time.sleep(retry_after)
            continue  # don't count as an attempt

        if resp.status_code < 400:
            return len(batch)

    raise RuntimeError(
        f"Batch {batch_num}/{total_batches} failed after {MAX_RETRIES} retries: "
        f"{resp.status_code} {resp.text[:200]}"
    )


def publish_to_notion(data: dict) -> dict:
    """Publish to Notion via REST API with parent verification + auto-batching."""
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = os.getenv("NOTION_PARENT_ID")

    if not api_key or not parent_id:
        raise ValueError("NOTION_API_KEY and NOTION_PARENT_ID must be set in environment variables.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # ── Step 0: Verify parent page exists ──────────────────────────────────
    parent_title = _verify_parent(parent_id, headers)

    children = [_to_notion_block(block) for block in data.get("content_blocks", [])]
    batches = _chunk(children, BATCH_SIZE)

    # ── Step 1: Create EMPTY child page (no children) ─────────────────────
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"text": {"content": data["title"]}}],
        },
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=page_payload,
    )
    resp.raise_for_status()
    result = resp.json()
    page_id = result["id"]

    # ── Step 2: Append content in batches of 100 ───────────────────────────
    blocks_published = 0
    for i, batch in enumerate(batches, 1):
        blocks_published += _append_batch_with_retry(
            page_id, batch, headers, i, len(batches)
        )
        if i < len(batches):
            time.sleep(INTER_BATCH_DELAY)

    result["blocks_published"] = blocks_published
    result["batches_sent"] = len(batches)
    return result


class PublisherSkill(BaseSkill):
    name = "publisher"
    _fallback_prompt = "You are a content publisher. Format content for Notion with title, tags, category, summary, and content_blocks as JSON."

    def __init__(self, client, model, metrics_collector, notion_mcp_client=None):
        super().__init__(client, model, metrics_collector)
        self.notion = notion_mcp_client

    def execute(self, user_message: str, context: dict = None) -> dict:
        # result is expected to be a dict with 'content'
        result = super().execute(user_message, context)

        try:
            notion_data = _extract_json_from_content(result["content"])
        except ValueError as e:
            result["published"] = False
            result["publish_error"] = str(e)
            return result

        # Try MCP client first, fall back to REST API
        if self.notion:
            try:
                publish_result = self.notion.create_page(notion_data)
                result["notion_url"] = publish_result.get("url", "")
                result["published"] = True
            except Exception as e:
                result["published"] = False
                result["publish_error"] = f"MCP publish failed: {e}"
        else:
            try:
                publish_result = publish_to_notion(notion_data)
                result["notion_url"] = publish_result.get("url", "")
                result["published"] = True
            except Exception as e:
                result["published"] = False
                result["publish_error"] = str(e)

        return result


if __name__ == "__main__":
    if "--file" in sys.argv:
        idx = sys.argv.index("--file") + 1
        with open(sys.argv[idx]) as f:
            data = json.load(f)
    else:
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                data = json.loads(raw_input)
            else:
                print("No input provided via stdin.")
                sys.exit(1)
        except json.JSONDecodeError:
            print("Invalid JSON input via stdin.")
            sys.exit(1)
            
    try:
        publish_to_notion(data)
        print("Publishing successful!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
