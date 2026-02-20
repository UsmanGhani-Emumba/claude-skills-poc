#!/usr/bin/env python3
"""
Notion publishing skill and standalone script.
Reads JSON from stdin/file or executes as a skill within the orchestrator.
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
    class BaseSkill:
        def __init__(self, client, model, metrics_collector=None):
            self.client = client
            self.model = model
            self.metrics = metrics_collector
        def execute(self, user_message, context=None):
            return {"content": user_message}

BATCH_SIZE = 100
INTER_BATCH_DELAY = 0.35
MAX_RETRIES = 2


def _extract_json_from_content(text: str) -> dict:
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


def _verify_parent(parent_id: str, headers: dict) -> dict:
    """Verify parent page exists. Returns {'type': 'page', 'title': str}."""
    resp = requests.get(f"https://api.notion.com/v1/pages/{parent_id}", headers=headers)
    if resp.status_code == 200:
        page = resp.json()
        title = "Untitled Page"
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title" and prop.get("title"):
                title = "".join(t.get("plain_text", "") for t in prop["title"])
                break
        return {"type": "page", "title": title}

    raise ValueError(
        f"Parent Page ID '{parent_id}' not found or inaccessible (Status: {resp.status_code}). "
        f"Details: {resp.text[:200]}"
    )


def _chunk(lst: list, size: int) -> list:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _append_batch_with_retry(page_id: str, batch: list, headers: dict, batch_num: int, total_batches: int) -> int:
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            time.sleep(1 if attempt == 1 else 3)

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
        
        # If it's a 4xx error (not 429), it might be a block validation error.
        if 400 <= resp.status_code < 500 and resp.status_code != 429:
            raise RuntimeError(f"Notion API error (Batch {batch_num}): {resp.status_code} - {resp.text}")

    raise RuntimeError(f"Batch {batch_num}/{total_batches} failed after {MAX_RETRIES} retries.")


def publish_to_notion(data: dict) -> dict:
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = "2ff01e7f802c8041bb7bf826722f02da"

    if not api_key or not parent_id:
        raise ValueError("NOTION_API_KEY and NOTION_PARENT_ID must be set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    print(f"Phase 1: Verifying parent {parent_id}...")
    parent_info = _verify_parent(parent_id, headers)
    print(f"Parent verified: {parent_info['type']} '{parent_info['title']}'")

    blocks = data.get("content_blocks", [])
    if not blocks:
        print("Warning: No content blocks found in input data.")
    
    children = [_to_notion_block(block) for block in blocks]
    batches = _chunk(children, BATCH_SIZE)

    print(f"Phase 2: Creating empty page under {parent_id}...")
    
    # Always use page_id and title property since parent is guaranteed to be a page
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"text": {"content": data["title"]}}]}
        },
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=page_payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to create page: {resp.status_code} - {resp.text}")
    
    result = resp.json()
    page_id = result["id"]
    notion_url = result.get("url", "N/A")
    print(f"Page created: {page_id}")
    print(f"URL: {notion_url}")

    if batches:
        print(f"Phase 3: Appending {len(children)} blocks in {len(batches)} batch(es)...")
        blocks_published = 0
        for i, batch in enumerate(batches, 1):
            blocks_published += _append_batch_with_retry(page_id, batch, headers, i, len(batches))
            print(f"  Batch {i}/{len(batches)} appended ({blocks_published} blocks total)")
            if i < len(batches):
                time.sleep(INTER_BATCH_DELAY)
    else:
        print("Phase 3: Skipping (no blocks to append)")

    result["blocks_published"] = len(children)
    result["batches_sent"] = len(batches)
    result["notion_url"] = notion_url
    return result


class PublisherSkill(BaseSkill):
    name = "publisher"
    _fallback_prompt = "You are a content publisher. Format content for Notion as JSON."

    def __init__(self, client, model, metrics_collector, notion_mcp_client=None):
        super().__init__(client, model, metrics_collector)
        self.notion = notion_mcp_client

    def execute(self, user_message: str, context: dict = None) -> dict:
        result = super().execute(user_message, context)
        try:
            notion_data = _extract_json_from_content(result["content"])
            if self.notion:
                publish_result = self.notion.create_page(notion_data)
                result["notion_url"] = publish_result.get("url", "")
                result["published"] = True
            else:
                publish_result = publish_to_notion(notion_data)
                result["notion_url"] = publish_result.get("notion_url", "")
                result["published"] = True
                result["blocks_published"] = publish_result.get("blocks_published", 0)
        except Exception as e:
            print(f"Publisher Error: {e}")
            result["published"] = False
            result["publish_error"] = str(e)
        return result


if __name__ == "__main__":
    load_dotenv()
    # Minimal CLI for manual testing
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            data = json.loads(raw_input)
            publish_to_notion(data)
            print("Success!")
    except Exception as e:
        print(f"Error: {e}")
