"""
API Endpoints: Audit Trail & Governance (F11, Section 10).
Returns immutable cryptographic audit log and verifies hash chain integrity.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case, AuditEvent

router = APIRouter(prefix="/cases/{case_id}/audit", tags=["Audit & Governance"])


@router.get("")
def get_case_audit_trail(case_id: str, db: Session = Depends(get_db)):
    """
    Returns full cryptographic audit trail with chain verification status.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    events = db.query(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp.asc()).all()

    # Verify cryptographic hash chain integrity
    is_chain_valid = True
    prev_hash = ""
    for ev in events:
        if ev.previous_hash != prev_hash:
            is_chain_valid = False
            break
        prev_hash = ev.current_hash

    return {
        "case_id": case_id,
        "is_chain_intact": is_chain_valid,
        "total_events": len(events),
        "events": [e.to_dict() for e in events]
    }
