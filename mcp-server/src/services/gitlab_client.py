import base64
from typing import Optional
import httpx
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class GitLabClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.gitlab_url.rstrip("/")
        self._token = settings.gitlab_token
        self._project = settings.gitlab_project_id
        self._branch = settings.gitlab_branch
        self._headers = {"PRIVATE-TOKEN": self._token}

    def _project_url(self, path: str) -> str:
        from urllib.parse import quote
        project_encoded = quote(self._project, safe="")
        return f"{self._base_url}/api/v4/projects/{project_encoded}/{path}"

    async def list_tree(self, path: str = "", recursive: bool = True) -> list[dict]:
        """Lista arquivos e diretórios no repositório."""
        params = {"ref": self._branch, "recursive": recursive, "per_page": 100}
        if path:
            params["path"] = path

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._project_url("repository/tree"),
                headers=self._headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_file(self, file_path: str) -> Optional[str]:
        """Retorna o conteúdo decodificado de um arquivo."""
        from urllib.parse import quote
        path_encoded = quote(file_path, safe="")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._project_url(f"repository/files/{path_encoded}"),
                headers=self._headers,
                params={"ref": self._branch},
                timeout=10.0,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return base64.b64decode(data["content"]).decode("utf-8")
