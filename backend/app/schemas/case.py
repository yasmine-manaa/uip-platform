"""
Pydantic v2 Request & Response Schemas for API v1.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ApplicantCreate(BaseModel):
    full_name: str
    driver_age: int = Field(ge=16, le=100)
    licence_years: int = Field(ge=0, le=80)
    usage: str = Field(default="Commuting", description="Private, Commuting, Professional, Taxi_VTC")
    postal_code: str = Field(default="75001")
    annual_mileage: Optional[int] = 15000


class VehicleCreate(BaseModel):
    vehicle_model: str
    vehicle_power: int = Field(ge=1, le=50, description="Fiscal horsepower (CV)")
    vehicle_age: int = Field(ge=0, le=40)
    vehicle_genre: str = Field(default="VP", description="VP, TAXI, VTC, VU")
    license_plate: Optional[str] = "AA-123-AA"


class ClaimsSummaryCreate(BaseModel):
    bonus_malus: Optional[float] = Field(default=0.85, ge=0.50, le=3.50)
    prior_claims_count: int = Field(default=0, ge=0)
    cancelled_by_previous_insurer: bool = False
    cancellation_reason: Optional[str] = None


class CaseCreateRequest(BaseModel):
    applicant: ApplicantCreate
    vehicle: VehicleCreate
    claims_summary: ClaimsSummaryCreate
    coverage_requested: str = Field(default="Tous Risques")
    area_density: Optional[int] = 3


class CaseResponse(BaseModel):
    id: str
    applicant_name: str
    status: str
    coverage_requested: str
    risk_tier: Optional[str] = None
    pure_premium_eur: Optional[float] = None
    decision_code: Optional[str] = None
    provisional_recommendation: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    raw_input: Dict[str, Any] = {}


class HumanReviewRequest(BaseModel):
    underwriter_name: str
    underwriter_role: str = "Souscripteur Habilité"
    decision: str = Field(description="ACCEPTED, MODIFIED, INFO_REQUESTED, ESCALATED_SENIOR, REFUSED")
    justification: str
    final_premium_eur: Optional[float] = None
    technical_loading_pct: Optional[float] = 0.0
    deductible_eur: Optional[float] = None
    special_conditions: Optional[str] = None
