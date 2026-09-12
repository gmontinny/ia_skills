from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    """Frontmatter do SKILL.md — contrato mínimo OKF."""
    name: str
    description: str
    status: str = "draft"
    stale_after: Optional[datetime] = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Skill(BaseModel):
    """Skill completa: metadados OKF + conteúdo Markdown."""
    id: str = Field(description="Identificador único derivado do path no GitLab")
    metadata: SkillMetadata
    content: str = Field(description="Conteúdo completo do SKILL.md (system prompt)")
    reference: Optional[str] = Field(default=None, description="Conteúdo do reference.md")
    gitlab_path: str = Field(description="Path do arquivo no repositório GitLab")
    loaded_at: datetime = Field(default_factory=_now_utc)

    @property
    def is_stale(self) -> bool:
        if self.metadata.stale_after is None:
            return False
        stale = self.metadata.stale_after
        if stale.tzinfo is None:
            stale = stale.replace(tzinfo=timezone.utc)
        return _now_utc() > stale

    @property
    def tool_description(self) -> str:
        desc = self.metadata.description
        if self.is_stale:
            desc += f" ⚠️ SKILL DESATUALIZADA (expirou em {self.metadata.stale_after.date()})"
        return desc
