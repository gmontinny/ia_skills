import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from src.domain.skill import Skill
from src.domain.knowledge import KnowledgeBundle
from src.services.gitlab_client import GitLabClient
from src.services.skill_loader import parse_skill
from src.services.knowledge_loader import parse_knowledge
from src.services.okf_validator import validate_skill
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_SKILL_FILE = "SKILL.md"
_REFERENCE_FILE = "reference.md"
_KNOWLEDGE_FILE = "knowledge.yaml"


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._knowledge: Optional[KnowledgeBundle] = None
        self._cached_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._ttl = timedelta(seconds=get_settings().skill_cache_ttl)

    def _is_cache_valid(self) -> bool:
        if self._cached_at is None:
            return False
        return datetime.now(timezone.utc) - self._cached_at < self._ttl

    async def _load_from_gitlab(self) -> None:
        client = GitLabClient()
        logger.info("Carregando skills do GitLab...")

        # Carrega knowledge.yaml se existir
        knowledge_raw = await client.get_file(_KNOWLEDGE_FILE)
        if knowledge_raw:
            self._knowledge = parse_knowledge(knowledge_raw)
            logger.info("knowledge.yaml carregado: %s", self._knowledge.name if self._knowledge else "inválido")

        # Lista todos os arquivos do repositório
        tree = await client.list_tree(recursive=True)
        skill_paths = [
            item["path"] for item in tree
            if item["type"] == "blob" and item["name"] == _SKILL_FILE
        ]

        loaded, skipped = 0, 0
        skills: dict[str, Skill] = {}

        for skill_path in skill_paths:
            raw = await client.get_file(skill_path)
            if not raw:
                skipped += 1
                continue

            # Tenta carregar reference.md do mesmo diretório
            ref_path = skill_path.replace(_SKILL_FILE, _REFERENCE_FILE)
            reference_raw = await client.get_file(ref_path)

            skill = parse_skill(skill_path, raw, reference_raw)
            if not skill:
                skipped += 1
                continue

            result = validate_skill(skill)
            if not result.valid:
                logger.warning("Skill '%s' rejeitada: %s", skill.id, result.errors)
                skipped += 1
                continue

            # Não expõe skills deprecated
            if skill.metadata.status == "deprecated":
                logger.info("Skill '%s' ignorada (deprecated)", skill.id)
                skipped += 1
                continue

            skills[skill.id] = skill
            loaded += 1

        self._skills = skills
        self._cached_at = datetime.now(timezone.utc)
        logger.info("Skills carregadas: %d válidas, %d ignoradas", loaded, skipped)

    async def get_all(self) -> dict[str, Skill]:
        async with self._lock:
            if not self._is_cache_valid():
                await self._load_from_gitlab()
        return self._skills

    async def get(self, skill_id: str) -> Optional[Skill]:
        skills = await self.get_all()
        return skills.get(skill_id)

    async def get_knowledge(self) -> Optional[KnowledgeBundle]:
        await self.get_all()
        return self._knowledge

    def invalidate_cache(self) -> None:
        self._cached_at = None
        logger.info("Cache de skills invalidado")
