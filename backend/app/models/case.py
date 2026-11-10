"""
SQLAlchemy ORM Models for Underwriting Intelligence Platform (UIP).
Section 12.1: Case, Document, ExtractedField, AgentRun, RiskAssessment,
Recommendation, HumanReview, and AuditEvent with cryptographic hash chaining.
"""

from datetime import datetime
import json
import hashlib
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(64), primary_key=True, index=True)
    applicant_name = Column(String(128), nullable=False)
    status = Column(String(32), default="DRAFT")  # DRAFT, ANALYZED, UNDER_REVIEW, APPROVED, MODIFIED, ESCALATED, CLOSED
    coverage_requested = Column(String(64), default="Tous Risques")
    risk_tier = Column(String(32), nullable=True)  # LOW, MODERATE, HIGH, CRITICAL
    pure_premium_eur = Column(Float, nullable=True)
    decision_code = Column(String(64), nullable=True)
    provisional_recommendation = Column(Text, nullable=True)
    raw_input_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client_id = Column(String(64), ForeignKey("clients.id"), nullable=True, index=True)

    # Relationships
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="case", cascade="all, delete-orphan")
    reviews = relationship("HumanReview", back_populates="case", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="case", cascade="all, delete-orphan")
    client = relationship("Client", back_populates="cases")

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.id,  # Ajout du champ reference attendu par le frontend
            "applicant_name": self.applicant_name,
            "status": self.status,
            "coverage_requested": self.coverage_requested,
            "risk_tier": self.risk_tier,
            "pure_premium_eur": self.pure_premium_eur,
            "decision_code": self.decision_code,
            "final_decision": self.decision_code,  # Ajout pour compatibilité frontend
            "provisional_recommendation": self.provisional_recommendation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "raw_input": json.loads(self.raw_input_json) if self.raw_input_json else {}
        }


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    filename = Column(String(256), nullable=False)
    doc_type = Column(String(64), default="DOCUMENT_NON_RECONNU")
    doc_label = Column(String(128), default="Document Inconnu")
    page_count = Column(Integer, default=1)
    ocr_status = Column(String(32), default="SUCCESS")  # SUCCESS, OCR_APPLIED, FAILED
    confidence = Column(Float, default=1.0)
    file_path = Column(String(512), nullable=True)
    raw_text = Column(Text, nullable=True)
    extracted_fields_json = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "filename": self.filename,
            "doc_type": self.doc_type,
            "doc_label": self.doc_label,
            "page_count": self.page_count,
            "ocr_status": self.ocr_status,
            "confidence": self.confidence,
            "extracted_fields": json.loads(self.extracted_fields_json) if self.extracted_fields_json else [],
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(128), nullable=False)
    version = Column(String(32), default="1.0.0")
    status = Column(String(32), default="SUCCESS")  # SUCCESS, WARNING, ESCALATED, DATA_DEFICIENT
    confidence_score = Column(Float, default=1.0)
    findings_json = Column(Text, nullable=True)
    alerts_json = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    sources_json = Column(Text, nullable=True)
    missing_fields_json = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="agent_runs")

    def to_dict(self):
        # Convert evidence array to format expected by frontend
        evidence_list = json.loads(self.evidence_json) if self.evidence_json else []
        sources_list = json.loads(self.sources_json) if self.sources_json else []

        # Map evidence to proper format for frontend
        formatted_evidence = []
        for e in evidence_list:
            if isinstance(e, dict) and "key" in e:
                # Evidence is in key-value format, convert to citation format
                formatted_evidence.append({
                    "citation_id": f"EVI-{self.id[:8]}",
                    "doc_title": e.get("source_ref", "Données saisies"),
                    "page": 1,
                    "article": "Champ extrait",
                    "excerpt": f"{e.get('key', '')}: {e.get('value', '')}"
                })
            else:
                formatted_evidence.append(e)

        # Map sources to proper format
        formatted_sources = []
        for s in sources_list:
            if isinstance(s, dict) and "citation_id" in s:
                formatted_sources.append({
                    "citation_id": s.get("citation_id"),
                    "doc_title": s.get("doc_title", ""),
                    "page": s.get("page", 1),
                    "article": s.get("article", ""),
                    "excerpt": s.get("snippet", s.get("excerpt", ""))
                })
            else:
                formatted_sources.append(s)

        return {
            "id": self.id,
            "case_id": self.case_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "version": self.version,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "findings": json.loads(self.findings_json) if self.findings_json else [],
            "alerts": json.loads(self.alerts_json) if self.alerts_json else [],
            "evidence": formatted_evidence + formatted_sources,  # Combine evidence and sources
            "sources": formatted_sources,
            "missing_fields": json.loads(self.missing_fields_json) if self.missing_fields_json else [],
            "processing_time_ms": 150,  # Placeholder since not stored
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    underwriter_name = Column(String(128), nullable=False)
    underwriter_role = Column(String(64), default="Souscripteur Habilité")
    decision = Column(String(32), nullable=False)  # ACCEPTED, MODIFIED, INFO_REQUESTED, ESCALATED_SENIOR, REFUSED
    final_premium_eur = Column(Float, nullable=True)
    technical_loading_pct = Column(Float, default=0.0)
    deductible_eur = Column(Float, nullable=True)
    justification = Column(Text, nullable=False)
    special_conditions = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "underwriter_name": self.underwriter_name,
            "underwriter_role": self.underwriter_role,
            "decision": self.decision,
            "final_premium_eur": self.final_premium_eur,
            "technical_loading_pct": self.technical_loading_pct,
            "deductible_eur": self.deductible_eur,
            "justification": self.justification,
            "special_conditions": self.special_conditions,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }


class AuditEvent(Base):
    """
    Immutable cryptographic audit event with SHA-256 chaining.
    Section 10.1 & F11: Guarantees tamper-evident traceability of all underwriting decisions.
    """
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    actor = Column(String(128), nullable=False)
    details_json = Column(Text, nullable=False)
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="audit_events")

    @classmethod
    def create_event(cls, case_id: str, event_type: str, actor: str, details: dict, prev_hash: str = ""):
        event_id = f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        ts = datetime.utcnow()
        details_str = json.dumps(details, sort_keys=True)
        # Hash chaining
        payload = f"{event_id}|{case_id}|{event_type}|{actor}|{details_str}|{prev_hash}|{ts.isoformat()}"
        cur_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return cls(
            id=event_id,
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            details_json=details_str,
            previous_hash=prev_hash,
            current_hash=cur_hash,
            timestamp=ts
        )

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "details": json.loads(self.details_json) if self.details_json else {},
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
