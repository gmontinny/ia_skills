from typing import Optional
import yaml
from src.domain.knowledge import KnowledgeBundle, TrustSignals
from src.core.logging import get_logger

logger = get_logger(__name__)


def parse_knowledge(raw_content: str) -> Optional[KnowledgeBundle]:
    """Parseia o knowledge.yaml e retorna um KnowledgeBundle."""
    try:
        data = yaml.safe_load(raw_content)
        ko = data.get("knowledge_object", data)
        ts_data = data.get("trust_signals", {})

        trust_signals = TrustSignals(
            status=ts_data.get("status", "draft"),
            stale_after=ts_data.get("stale_after"),
            autonomous_use=ts_data.get("autonomous_use"),
            maturity=ts_data.get("maturity"),
        ) if ts_data else None

        return KnowledgeBundle(
            id=ko.get("id"),
            name=ko.get("name"),
            version=str(ko.get("version", "")),
            description=ko.get("description"),
            trust_signals=trust_signals,
        )
    except Exception as e:
        logger.warning("Falha ao parsear knowledge.yaml: %s", e)
        return None
