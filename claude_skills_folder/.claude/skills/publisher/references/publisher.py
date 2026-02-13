import json
import os
import re

import requests

from base import BaseSkill


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


def _publish_to_notion_rest(data: dict) -> dict:
    """Publish to Notion via REST API using env vars for auth."""
    api_key = os.getenv("NOTION_API_KEY")
    parent_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not parent_id:
        raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID must be set in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    children = [_to_notion_block(block) for block in data.get("content_blocks", [])]

    # Notion limits children to 100 blocks per request — batch if needed
    first_batch = children[:100]
    remaining = children[100:]

    # Try as page parent first (most common), fall back to database parent
    page_payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"text": {"content": data["title"]}}],
        },
        "children": first_batch,
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=page_payload,
    )

    # If page_id fails, retry as database_id
    if resp.status_code == 400 or resp.status_code == 404:
        db_payload = {
            "parent": {"database_id": parent_id},
            "properties": {
                "Name": {"title": [{"text": {"content": data["title"]}}]},
            },
            "children": first_batch,
        }
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=db_payload,
        )

    resp.raise_for_status()
    result = resp.json()

    # Append remaining blocks in batches of 100
    page_id = result["id"]
    while remaining:
        batch = remaining[:100]
        remaining = remaining[100:]
        append_resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": batch},
        )
        append_resp.raise_for_status()

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
                publish_result = _publish_to_notion_rest(notion_data)
                result["notion_url"] = publish_result.get("url", "")
                result["published"] = True
            except Exception as e:
                result["published"] = False
                result["publish_error"] = str(e)

        return result
