from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TrustSignals(BaseModel):
    """Bloco trust_signals do knowledge.yaml OKF v0.2."""
    status: str = "draft"
    stale_after: Optional[datetime] = None
    autonomous_use: Optional[str] = None
    maturity: Optional[str] = None


class KnowledgeBundle(BaseModel):
    """Descritor machine-readable do bundle OKF (knowledge.yaml)."""
    id: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    trust_signals: Optional[TrustSignals] = None

    @property
    def is_autonomous_use_prohibited(self) -> bool:
        if self.trust_signals is None:
            return False
        return "prohibited" in (self.trust_signals.autonomous_use or "")
