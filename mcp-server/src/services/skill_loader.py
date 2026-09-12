import re
from typing import Optional
import frontmatter
from src.domain.skill import Skill, SkillMetadata
from src.core.logging import get_logger

logger = get_logger(__name__)

_SKILL_FILE = "SKILL.md"
_REFERENCE_FILE = "reference.md"


def _skill_id_from_path(gitlab_path: str) -> str:
    """Deriva o ID da skill a partir do path no GitLab.
    Ex: skills/lgpd-brasil/SKILL.md → lgpd-brasil
    """
    parts = gitlab_path.replace("\\", "/").split("/")
    skill_dir = parts[-2] if len(parts) >= 2 else parts[0]
    return skill_dir


def parse_skill(
    gitlab_path: str,
    raw_content: str,
    reference_content: Optional[str] = None,
) -> Optional[Skill]:
    """Parseia o conteúdo de um SKILL.md e retorna um objeto Skill."""
    try:
        post = frontmatter.loads(raw_content)
        metadata = SkillMetadata(
            name=post.get("name", ""),
            description=post.get("description", ""),
            status=post.get("status", "draft"),
            stale_after=post.get("stale_after"),
        )
        return Skill(
            id=_skill_id_from_path(gitlab_path),
            metadata=metadata,
            content=raw_content,
            reference=reference_content,
            gitlab_path=gitlab_path,
        )
    except Exception as e:
        logger.warning("Falha ao parsear skill %s: %s", gitlab_path, e)
        return None
