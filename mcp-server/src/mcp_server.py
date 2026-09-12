from mcp.server.fastmcp import FastMCP
from src.services.skill_registry import SkillRegistry
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()
registry = SkillRegistry()

mcp = FastMCP(name=settings.mcp_server_name)


@mcp.tool(
    name="list_skills",
    description="Lista todas as skills disponíveis com seus metadados OKF (nome, descrição, status, validade).",
)
async def list_skills() -> dict:
    skills = await registry.get_all()
    knowledge = await registry.get_knowledge()

    result = {
        "skills": [
            {
                "id": s.id,
                "name": s.metadata.name,
                "description": s.tool_description,
                "status": s.metadata.status,
                "stale": s.is_stale,
                "stale_after": s.metadata.stale_after.isoformat() if s.metadata.stale_after else None,
            }
            for s in skills.values()
        ],
        "total": len(skills),
    }

    if knowledge and knowledge.trust_signals:
        result["bundle"] = {
            "name": knowledge.name,
            "version": knowledge.version,
            "status": knowledge.trust_signals.status,
            "autonomous_use_prohibited": knowledge.is_autonomous_use_prohibited,
        }

    return result


@mcp.tool(
    name="get_skill",
    description=(
        "Retorna o conteúdo completo de uma skill pelo ID para uso como system prompt. "
        "Use list_skills primeiro para descobrir os IDs disponíveis."
    ),
)
async def get_skill(skill_id: str) -> dict:
    skill = await registry.get(skill_id)

    if not skill:
        return {"error": f"Skill '{skill_id}' não encontrada. Use list_skills para ver as disponíveis."}

    result = {
        "id": skill.id,
        "name": skill.metadata.name,
        "description": skill.tool_description,
        "status": skill.metadata.status,
        "stale": skill.is_stale,
        "content": skill.content,
    }

    if skill.reference:
        result["reference"] = skill.reference

    if skill.is_stale:
        result["warning"] = (
            f"Esta skill expirou em {skill.metadata.stale_after.date()}. "
            "Verifique se há uma versão atualizada no repositório."
        )

    return result


@mcp.tool(
    name="reload_skills",
    description="Força o recarregamento das skills do GitLab, ignorando o cache.",
)
async def reload_skills() -> dict:
    registry.invalidate_cache()
    skills = await registry.get_all()
    return {"reloaded": True, "total": len(skills)}
