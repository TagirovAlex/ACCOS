import logging
from urllib.parse import urlparse

from mcp.server import Server
from mcp.types import Tool, TextContent
from app.adapters.web_fetch_adapter import WebFetchAdapter, BLOCKED_EXTENSIONS

logger = logging.getLogger(__name__)

app = Server(
    name="accos-web-fetch",
    version="1.0.0",
    instructions="Web fetch tool for ACCOS. Fetches web pages and returns markdown content.",
)

adapter = WebFetchAdapter()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch_web_page",
            description="Fetch a web page URL and return its content as markdown text. "
                        "Useful when you need to read articles, documentation, or any web content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch (e.g. https://example.com/page)",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 10000)",
                        "default": 10000,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="search_in_page",
            description="Search for a query within a fetched web page. "
                        "Useful when you need to find specific information on a page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the page to search in",
                    },
                    "query": {
                        "type": "string",
                        "description": "The search query to find in the page content",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters of context to return around matches (default 5000)",
                        "default": 5000,
                    },
                },
                "required": ["url", "query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_web_page":
        url = arguments.get("url", "")
        max_chars = arguments.get("max_chars", 10000)
        return [await _fetch_page(url, max_chars)]
    elif name == "search_in_page":
        url = arguments.get("url", "")
        query = arguments.get("query", "")
        max_chars = arguments.get("max_chars", 5000)
        return [await _search_page(url, query, max_chars)]
    raise ValueError(f"Unknown tool: {name}")


async def _fetch_page(url: str, max_chars: int) -> TextContent:
    ext = _get_extension(url)
    if ext in BLOCKED_EXTENSIONS:
        return TextContent(type="text", text=f"Error: Blocked file extension `{ext}`")

    result = await adapter.fetch(url, max_chars=max_chars)
    if result["success"]:
        text = result["content"]
        return TextContent(type="text", text=text)
    return TextContent(type="text", text=f"Error: {result.get('error', 'Unknown error')}")


async def _search_page(url: str, query: str, max_chars: int) -> TextContent:
    result = await adapter.fetch(url, max_chars=max_chars * 2)
    if not result["success"]:
        return TextContent(type="text", text=f"Error fetching page: {result.get('error', 'Unknown error')}")

    text = result["content"].lower()
    query_lower = query.lower()
    lines = text.split("\n")
    matches = []
    for i, line in enumerate(lines):
        if query_lower in line.lower():
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context = "\n".join(lines[start:end])
            matches.append(f"...[line {start + 1}]...\n{context}\n...[line {end}]...")

    if not matches:
        return TextContent(type="text", text=f"No matches found for `{query}` in {url}")

    result_text = f"Found {len(matches)} matches for `{query}` in {url}:\n\n---\n\n"
    result_text += "\n\n---\n\n".join(matches[:10])
    if len(matches) > 10:
        result_text += f"\n\n... and {len(matches) - 10} more matches"

    if len(result_text) > max_chars:
        result_text = result_text[:max_chars] + f"\n\n[Truncated at {max_chars} characters]"

    return TextContent(type="text", text=result_text)


def _get_extension(url: str) -> str:
    from urllib.parse import unquote
    path = unquote(urlparse(url).path)
    pos = path.rfind(".")
    if pos == -1:
        return ""
    return path[pos:].lower().split("?")[0].split("#")[0]
