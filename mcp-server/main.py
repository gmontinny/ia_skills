import re
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.sse import SseServerTransport
from src.api.routes import router
from src.mcp_server import mcp
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

_last_session_id: str | None = None
_SESSION_RE = re.compile(r"session_id=([a-f0-9]+)")

sse_transport = SseServerTransport("/sse")


async def _sse_get(scope, receive, send):
    global _last_session_id

    async def patched_send(message):
        if message["type"] == "http.response.body":
            body = message.get("body", b"")
            text = body.decode() if isinstance(body, bytes) else body
            if m := _SESSION_RE.search(text):
                _last_session_id = m.group(1)
                logger.debug("session_id capturado: %s", _last_session_id)
        await send(message)

    async with sse_transport.connect_sse(scope, receive, patched_send) as streams:
        await mcp._mcp_server.run(streams[0], streams[1], mcp._mcp_server.create_initialization_options())


async def _sse_post(scope, receive, send):
    global _last_session_id
    if not scope["query_string"] and _last_session_id:
        scope["query_string"] = f"session_id={_last_session_id}".encode()
    await sse_transport.handle_post_message(scope, receive, send)


# FastAPI para rotas REST
api = FastAPI(
    title=settings.mcp_server_name,
    version=settings.mcp_server_version,
    description="Servidor MCP para skills OKF versionadas no GitLab",
)
api.include_router(router)

# Streamable HTTP app — gerencia /mcp internamente
_mcp_streamable = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        logger.info(
            "Servidor iniciando — SSE: http://%s:%d/sse | HTTP: http://%s:%d/mcp | Health: http://%s:%d/health",
            settings.mcp_host, settings.mcp_port,
            settings.mcp_host, settings.mcp_port,
            settings.mcp_host, settings.mcp_port,
        )
        yield


async def _root_asgi(scope, receive, send):
    """Router ASGI raiz — roteia sem depender de Mount."""
    if scope["type"] != "http":
        await api(scope, receive, send)
        return

    path = scope.get("path", "")
    method = scope.get("method", "")

    if path == "/sse":
        if method == "GET":
            await _sse_get(scope, receive, send)
        elif method == "POST":
            await _sse_post(scope, receive, send)
        else:
            await Response(status_code=405)(scope, receive, send)
    elif path == "/mcp" or path.startswith("/mcp/"):
        await _mcp_streamable(scope, receive, send)
    else:
        await api(scope, receive, send)


app = Starlette(lifespan=lifespan, routes=[Mount("/", app=_root_asgi)])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.mcp_host,
        port=settings.mcp_port,
        reload=True,
    )
