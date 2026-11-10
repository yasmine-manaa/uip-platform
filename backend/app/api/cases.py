"""
API Endpoints: Case Management (F01).
CRUD operations, status filtering, and case context assembly.
"""

from typing import List, Optional
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case, AuditEvent
from app.schemas.case import CaseCreateRequest, CaseResponse

router = APIRouter(prefix="/cases", tags=["Case Management"])


@router.post("", response_model=CaseResponse)
def create_case(payload: dict, db: Session = Depends(get_db)):
    """
    Creates a new underwriting dossier (Case) with unique ID and logs initial audit event.
    Accepts both standard format and frontend format for flexibility.
    """
    case_id = f"CAS-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    # Extract applicant name from either format
    if "applicant" in payload:
        applicant_name = payload["applicant"].get("full_name", "Unknown")
    elif "applicant_name" in payload:
        applicant_name = payload["applicant_name"]
    else:
        applicant_name = "Unknown"

    # Normalize to standard format
    raw_data = {
        "case_id": case_id,
        "applicant": payload.get("applicant", {
            "full_name": applicant_name,
            "driver_age": payload.get("applicant_data", {}).get("age", 35),
            "licence_years": payload.get("applicant_data", {}).get("licence_years", 14),
            "usage": payload.get("applicant_data", {}).get("usage", "Commuting"),
            "postal_code": payload.get("applicant_data", {}).get("postal_code", "75001"),
            "annual_mileage": payload.get("applicant_data", {}).get("annual_mileage", 15000),
        }),
        "vehicle": payload.get("vehicle", {
            "vehicle_model": payload.get("vehicle_data", {}).get("model", "Unknown"),
            "vehicle_power": payload.get("vehicle_data", {}).get("power_cv", 5),
            "vehicle_age": 2025 - payload.get("vehicle_data", {}).get("year", 2020),
            "vehicle_genre": "VP",
            "license_plate": "AA-123-AA",
        }),
        "claims_summary": payload.get("claims_summary", {
            "bonus_malus": payload.get("claims_history", {}).get("bonus_malus", 0.85),
            "prior_claims_count": payload.get("claims_history", {}).get("total_claims_5y", 0),
            "cancelled_by_previous_insurer": payload.get("claims_history", {}).get("prior_cancellation", False),
        }),
        "coverage_requested": payload.get("coverage_requested", "Tous Risques"),
        "area_density": payload.get("area_density", 3),
    }

    new_case = Case(
        id=case_id,
        applicant_name=applicant_name,
        status="DRAFT",
        coverage_requested=payload.get("coverage_requested", "Tous Risques"),
        raw_input_json=json.dumps(raw_data)
    )
    db.add(new_case)

    # Initial immutable audit log
    audit = AuditEvent.create_event(
        case_id=case_id,
        event_type="CASE_CREATED",
        actor="System Ingestion",
        details={"applicant": applicant_name, "coverage": payload.get("coverage_requested", "Tous Risques")}
    )
    db.add(audit)
    db.commit()
    db.refresh(new_case)

    return new_case.to_dict()


@router.get("", response_model=List[CaseResponse])
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: DRAFT, ANALYZED, UNDER_REVIEW, APPROVED, ESCALATED"),
    db: Session = Depends(get_db)
):
    """
    Lists all underwriting dossiers with optional status filter.
    """
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    cases = query.order_by(Case.created_at.desc()).all()
    return [c.to_dict() for c in cases]


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single case by ID with full metadata.
    """
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return c.to_dict()
