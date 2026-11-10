"""
API Endpoints: Human Review & Decision Validation (F10).
Enforces Human-in-the-Loop principle: An authorized underwriter reviews
the provisional recommendation and validates, modifies, or escalates.
"""

from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case, HumanReview, AuditEvent
from app.schemas.case import HumanReviewRequest

router = APIRouter(prefix="/cases/{case_id}/review", tags=["Human Review"])


@router.post("")
def record_human_review(
    case_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Records official underwriter human decision:
    - Sets final decision (ACCEPTED, MODIFIED, INFO_REQUESTED, ESCALATED_SENIOR, REFUSED)
    - Records final commercial premium, loading %, and deductible
    - Sets immutable audit entry
    - Updates Case status accordingly
    Accepts both standard format and frontend format.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    review_id = f"REV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    # Extract fields from either format
    underwriter_name = payload.get("underwriter_name") or payload.get("reviewer_name", "Unknown")
    underwriter_role = payload.get("underwriter_role") or payload.get("reviewer_role", "Souscripteur")
    decision = payload.get("decision") or payload.get("override_decision", "ACCEPTED")
    justification = payload.get("justification") or payload.get("comments", "")

    # Validate critical/high risk cases require proper justification
    if case.risk_tier in ["HIGH", "CRITICAL"]:
        if not justification or len(justification) < 20:
            raise HTTPException(
                status_code=400,
                detail="Justification détaillée requise pour les cas à risque élevé/critique (min 20 caractères)."
            )
        if decision in ["ACCEPTED", "PROCEED_STANDARD"] and not payload.get("final_premium_eur"):
            raise HTTPException(
                status_code=400,
                detail="Prime finale obligatoire pour les cas à risque élevé/critique."
            )
        if decision in ["ACCEPTED", "PROCEED_STANDARD"] and payload.get("technical_loading_pct", 0) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Chargement technique obligatoire pour les cas à risque élevé/critique."
            )

    review_record = HumanReview(
        id=review_id,
        case_id=case_id,
        underwriter_name=underwriter_name,
        underwriter_role=underwriter_role,
        decision=decision,
        final_premium_eur=payload.get("final_premium_eur"),
        technical_loading_pct=payload.get("technical_loading_pct", 0.0),
        deductible_eur=payload.get("deductible_eur"),
        justification=justification,
        special_conditions=payload.get("special_conditions")
    )
    db.add(review_record)

    # Update Case status
    status_map = {
        "ACCEPTED": "APPROVED",
        "MODIFIED": "MODIFIED",
        "INFO_REQUESTED": "DRAFT",
        "ESCALATED_SENIOR": "ESCALATED",
        "REFUSED": "CLOSED",
        "PROCEED_STANDARD": "APPROVED",
        "PROCEED_WITH_CONDITIONS": "MODIFIED",
        "REFER_TO_SENIOR": "ESCALATED",
        "REQUEST_ADDITIONAL_INFO": "DRAFT",
        "DECLINE": "CLOSED",
    }
    case.status = status_map.get(decision, "UNDER_REVIEW")
    case.updated_at = datetime.utcnow()

    # Immutable Hash Chained Audit Event
    last_audit = db.query(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else ""
    audit = AuditEvent.create_event(
        case_id=case_id,
        event_type="HUMAN_REVIEW_SUBMITTED",
        actor=f"{underwriter_name} ({underwriter_role})",
        details={
            "review_id": review_id,
            "decision": decision,
            "final_premium_eur": payload.get("final_premium_eur"),
            "justification": justification
        },
        prev_hash=prev_hash
    )
    db.add(audit)
    db.commit()
    db.refresh(review_record)

    return review_record.to_dict()


@router.get("")
def get_human_reviews(case_id: str, db: Session = Depends(get_db)):
    """
    Returns historical review records for a case.
    """
    reviews = db.query(HumanReview).filter(HumanReview.case_id == case_id).order_by(HumanReview.reviewed_at.desc()).all()
    return [r.to_dict() for r in reviews]
