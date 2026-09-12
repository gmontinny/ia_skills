from dataclasses import dataclass, field
from src.domain.skill import Skill
from src.core.logging import get_logger

logger = get_logger(__name__)

REQUIRED_FRONTMATTER = {"name", "description"}
VALID_STATUSES = {"draft", "stable", "deprecated"}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_skill(skill: Skill) -> ValidationResult:
    """Valida conformidade OKF de uma skill."""
    errors: list[str] = []
    warnings: list[str] = []

    # Campos obrigatórios
    if not skill.metadata.name:
        errors.append("frontmatter: campo 'name' ausente ou vazio")
    if not skill.metadata.description:
        errors.append("frontmatter: campo 'description' ausente ou vazio")

    # Status válido
    if skill.metadata.status not in VALID_STATUSES:
        errors.append(
            f"frontmatter: status '{skill.metadata.status}' inválido. "
            f"Use: {', '.join(VALID_STATUSES)}"
        )

    # Skill deprecated não deve ser exposta
    if skill.metadata.status == "deprecated":
        warnings.append("skill está deprecated e não será exposta via MCP")

    # Aviso de expiração
    if skill.is_stale:
        warnings.append(
            f"skill expirou em {skill.metadata.stale_after.date()} "
            f"(stale_after). Atualize ou renove o prazo."
        )

    # Conteúdo mínimo
    if len(skill.content.strip()) < 50:
        errors.append("SKILL.md: conteúdo muito curto (mínimo 50 caracteres)")

    valid = len(errors) == 0
    if not valid:
        logger.warning("Skill '%s' inválida: %s", skill.id, errors)
    if warnings:
        logger.warning("Skill '%s' avisos: %s", skill.id, warnings)

    return ValidationResult(valid=valid, errors=errors, warnings=warnings)
