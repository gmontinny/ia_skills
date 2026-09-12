from fastapi import APIRouter
from src.services.skill_registry import SkillRegistry
from src.core.config import get_settings

router = APIRouter()
registry = SkillRegistry()
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "server": settings.mcp_server_name,
        "version": settings.mcp_server_version,
    }


@router.get("/skills")
async def list_skills() -> dict:
    skills = await registry.get_all()
    return {
        "skills": [
            {
                "id": s.id,
                "name": s.metadata.name,
                "description": s.tool_description,
                "status": s.metadata.status,
                "stale": s.is_stale,
            }
            for s in skills.values()
        ],
        "total": len(skills),
    }
