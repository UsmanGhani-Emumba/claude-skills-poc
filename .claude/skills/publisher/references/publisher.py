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
    return {
        "object": "block",
        "type": btype,
        btype: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _publish_to_notion_rest(data: dict) -> dict:
    """Publish to Notion via REST API using env vars for auth."""
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not db_id:
        raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID must be set in .env")

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

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=page_payload,
    )
    resp.raise_for_status()
    return resp.json()


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
