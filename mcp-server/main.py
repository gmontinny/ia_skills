import uvicorn
from fastapi import FastAPI
from src.api.routes import router
from src.mcp_server import mcp
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.mcp_server_name,
    version=settings.mcp_server_version,
    description="Servidor MCP para skills OKF versionadas no GitLab",
)

# Rotas REST
app.include_router(router)

# Monta o servidor MCP no path /mcp com transporte streamable-http
app.mount("/mcp", mcp.streamable_http_app())

logger.info(
    "Servidor iniciando — MCP em http://%s:%d/mcp | Health em http://%s:%d/health",
    settings.mcp_host, settings.mcp_port,
    settings.mcp_host, settings.mcp_port,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.mcp_host,
        port=settings.mcp_port,
        reload=True,
    )
