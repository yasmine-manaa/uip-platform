"""
Standard Output Contracts for All Specialized UIP Agents.
Section 6: Common contract with status, findings, evidence, sources,
missing fields, confidence score, alerts, timestamp, and version.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentAlert(BaseModel):
    code: str
    severity: str = Field(description="INFO, WARNING, or CRITICAL")
    message: str
    action_required: Optional[str] = None


class AgentEvidence(BaseModel):
    key: str
    value: Any
    source_ref: Optional[str] = None
    confidence: float = 1.0


class CitationRef(BaseModel):
    citation_id: str
    doc_id: str
    doc_title: str
    page: int
    article: str
    snippet: str
    relevance_score: float = 1.0


class AgentOutputContract(BaseModel):
    agent_id: str
    agent_name: str
    version: str = "1.0.0"
    status: str = Field(description="SUCCESS, WARNING, ESCALATED, or DATA_DEFICIENT")
    confidence_score: float = Field(ge=0.0, le=1.0)
    findings: List[str] = []
    evidence: List[AgentEvidence] = []
    sources: List[CitationRef] = []
    missing_fields: List[str] = []
    alerts: List[AgentAlert] = []
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = {}
