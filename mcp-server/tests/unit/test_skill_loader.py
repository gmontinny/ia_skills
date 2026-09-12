import pytest
from src.services.skill_loader import parse_skill
from src.services.okf_validator import validate_skill

VALID_SKILL_MD = """---
name: test-skill
description: Skill de teste para validação OKF
status: stable
---

# Test Skill

Conteúdo da skill de teste com mais de cinquenta caracteres para passar na validação.
"""

MISSING_NAME_MD = """---
description: Skill sem nome
status: stable
---

Conteúdo da skill sem nome definido no frontmatter.
"""

DEPRECATED_MD = """---
name: old-skill
description: Skill antiga
status: deprecated
---

Conteúdo da skill deprecated.
"""


def test_parse_skill_valid():
    skill = parse_skill("skills/test-skill/SKILL.md", VALID_SKILL_MD)
    assert skill is not None
    assert skill.id == "test-skill"
    assert skill.metadata.name == "test-skill"
    assert skill.metadata.status == "stable"


def test_parse_skill_with_reference():
    skill = parse_skill("skills/test-skill/SKILL.md", VALID_SKILL_MD, "# Referências\n- fonte 1")
    assert skill.reference == "# Referências\n- fonte 1"


def test_validate_skill_valid():
    skill = parse_skill("skills/test-skill/SKILL.md", VALID_SKILL_MD)
    result = validate_skill(skill)
    assert result.valid is True
    assert result.errors == []


def test_validate_skill_missing_name():
    skill = parse_skill("skills/no-name/SKILL.md", MISSING_NAME_MD)
    result = validate_skill(skill)
    assert result.valid is False
    assert any("name" in e for e in result.errors)


def test_validate_skill_deprecated_warning():
    skill = parse_skill("skills/old-skill/SKILL.md", DEPRECATED_MD)
    result = validate_skill(skill)
    assert result.valid is True
    assert any("deprecated" in w for w in result.warnings)


def test_skill_id_from_nested_path():
    skill = parse_skill("skills/lgpd-brasil/SKILL.md", VALID_SKILL_MD)
    assert skill.id == "lgpd-brasil"
