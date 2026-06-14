import logging

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request

from mcp.server.sse import SseServerTransport

from app.mcp.web_fetch_server import app as mcp_app

logger = logging.getLogger(__name__)

sse = SseServerTransport("/api/v1/mcp/messages/")


async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_app.run(
            streams[0],
            streams[1],
            mcp_app.create_initialization_options(),
        )


mcp_starlette = Starlette(
    routes=[
        Route("/api/v1/mcp/sse", endpoint=handle_sse),
        Route(
            "/api/v1/mcp/messages/",
            endpoint=sse.handle_post_message,
            methods=["POST"],
        ),
    ],
)
