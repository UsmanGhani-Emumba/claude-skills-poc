"""
MCP client for Notion. Connects to the official Notion MCP server.
Install: npx @notionhq/notion-mcp-server
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class NotionMCPClient:
    def __init__(self, notion_api_key: str, database_id: str):
        self.notion_api_key = notion_api_key
        self.database_id = database_id
        self._session = None

    async def connect(self):
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={"NOTION_API_KEY": self.notion_api_key},
        )
        self._transport_ctx = stdio_client(server_params)
        read, write = await self._transport_ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self._session = await self._session_ctx.__aenter__()
        await self._session.initialize()
        return self

    async def create_page(self, notion_data: dict) -> dict:
        result = await self._session.call_tool(
            "notion_create_page",
            arguments={
                "parent_database_id": self.database_id,
                "title": notion_data["title"],
                "properties": {
                    "Tags": {"multi_select": [{"name": t} for t in notion_data.get("tags", [])]},
                    "Category": {"select": {"name": notion_data.get("category", "Uncategorized")}},
                    "Summary": {"rich_text": [{"text": {"content": notion_data.get("summary", "")}}]},
                },
            },
        )
        page_id = result.get("id")
        if page_id and notion_data.get("content_blocks"):
            await self._session.call_tool(
                "notion_append_block_children",
                arguments={"block_id": page_id, "children": notion_data["content_blocks"]},
            )
        return result

    async def disconnect(self):
        if self._session:
            await self._session_ctx.__aexit__(None, None, None)
            await self._transport_ctx.__aexit__(None, None, None)
