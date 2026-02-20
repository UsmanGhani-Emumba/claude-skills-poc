import json
import os
import re
import time
import asyncio
import requests

from base import BaseSkill

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
    btype = block.get("type", "paragraph").lower()
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
    elif btype == "code":
        notion_block["code"]["language"] = block.get("language", "plain text")

    return notion_block


def _verify_parent(parent_id: str, headers: dict) -> str:
    """Verify the parent page exists and is accessible."""
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
        print(f"Verified parent: '{title}' (page_id: {parent_id})")
        return title

    raise ValueError(
        f"Parent page '{parent_id}' not found or not shared with integration. "
        f"Status: {resp.status_code}. Details: {resp.text[:200]}"
    )


def _chunk(lst: list, size: int) -> list:
    """Split a list into chunks of `size`."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _append_batch_with_retry(page_id: str, batch: list, headers: dict,
                              batch_num: int, total_batches: int) -> int:
    """Append a single batch, retrying on failure. Returns blocks appended."""
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
            retry_after = int(resp.headers.get("Retry-After", 2))
            time.sleep(retry_after)
            continue

        if resp.status_code < 400:
            return len(batch)

    raise RuntimeError(
        f"Batch {batch_num}/{total_batches} failed after {MAX_RETRIES} retries: "
        f"{resp.status_code} {resp.text[:200]}"
    )


def _publish_to_notion_rest(data: dict) -> dict:
    """Publish to Notion via REST API with parent verification + auto-batching."""
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = "2ff01e7f802c8041bb7bf826722f02da"

    if not api_key or not parent_id:
        raise ValueError("NOTION_API_KEY must be set in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # ── Phase 1: Verify parent page exists ──────────────────────────────────
    print(f"Phase 1: Verifying parent {parent_id}...")
    _verify_parent(parent_id, headers)

    blocks = data.get("content_blocks", [])
    children = [_to_notion_block(block) for block in blocks]
    batches = _chunk(children, BATCH_SIZE)

    # ── Phase 2: Create EMPTY child page (no children) ─────────────────────
    print(f"Phase 2: Creating empty child page under {parent_id}...")
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"text": {"content": data["title"]}}]}
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
    notion_url = result.get("url", "N/A")
    print(f"Page created: {page_id}")
    print(f"URL: {notion_url}")

    # ── Phase 3: Append content in batches of 100 ───────────────────────────
    blocks_published = 0
    if batches:
        print(f"Phase 3: Appending {len(children)} blocks in {len(batches)} batch(es)...")
        for i, batch in enumerate(batches, 1):
            blocks_published += _append_batch_with_retry(
                page_id, batch, headers, i, len(batches)
            )
            print(f"  Batch {i}/{len(batches)} appended ({blocks_published} blocks total)")
            if i < len(batches):
                time.sleep(INTER_BATCH_DELAY)
    else:
        print("Phase 3: Skipping (no blocks to append)")

    result["blocks_published"] = blocks_published
    result["batches_sent"] = len(batches)
    result["notion_url"] = notion_url
    return result


class PublisherSkill(BaseSkill):
    name = "publisher"
    _fallback_prompt = "You are a content publisher. Format content for Notion with title, tags, category, summary, and content_blocks as JSON."

    def __init__(self, client, model, metrics_collector, notion_mcp_client=None):
        super().__init__(client, model, metrics_collector)
        self.notion = notion_mcp_client

    def execute(self, user_message: str, context: dict = None) -> dict:
        result = super().execute(user_message, context)

        try:
            notion_data = _extract_json_from_content(result["content"])
        except ValueError as e:
            result["published"] = False
            result["publish_error"] = str(e)
            result["status"] = "failed"
            result["error_message"] = f"JSON extraction failed: {e}"
            return result

        # Try MCP client first, fall back to REST API
        if self.notion:
            try:
                # create_page is async in MCP client, need to await it
                # Using asyncio.run if there is no running loop, or run_until_complete if there is
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # This might happen if called from within an async function
                    # In that case, we need a different approach, but skill.execute is typically sync
                    future = asyncio.run_coroutine_threadsafe(self.notion.create_page(notion_data), loop)
                    publish_result = future.result()
                else:
                    publish_result = loop.run_until_complete(self.notion.create_page(notion_data))
                
                result["notion_url"] = publish_result.get("url", "")
                result["published"] = True
                result["status"] = "passed"
            except Exception as e:
                print(f"MCP publish failed: {e}. Falling back to REST API...")
                try:
                    publish_result = _publish_to_notion_rest(notion_data)
                    result["notion_url"] = publish_result.get("notion_url", "")
                    result["published"] = True
                    result["status"] = "passed"
                except Exception as rest_e:
                    result["published"] = False
                    result["publish_error"] = f"Both MCP and REST failed. REST error: {rest_e}"
                    result["status"] = "failed"
                    result["error_message"] = result["publish_error"]
        else:
            try:
                publish_result = _publish_to_notion_rest(notion_data)
                result["notion_url"] = publish_result.get("notion_url", "")
                result["published"] = True
                result["status"] = "passed"
            except Exception as e:
                result["published"] = False
                result["publish_error"] = str(e)
                result["status"] = "failed"
                result["error_message"] = str(e)

        return result
