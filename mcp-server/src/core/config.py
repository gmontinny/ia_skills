from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # MCP Server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000
    mcp_server_name: str = "ia-skills-mcp"
    mcp_server_version: str = "1.0.0"

    # GitLab
    gitlab_url: str = "http://192.168.15.4"
    gitlab_token: str
    gitlab_project_id: str
    gitlab_branch: str = "main"

    # Cache
    skill_cache_ttl: int = 300  # segundos

    # Log
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
