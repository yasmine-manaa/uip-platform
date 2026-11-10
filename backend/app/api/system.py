"""
API Endpoints: System Info, Model Governance & Health (F12, Section 10.4).
"""

from fastapi import APIRouter
from app.actuarial.trainer import actuarial_engine

router = APIRouter(prefix="/system", tags=["System & Model Governance"])


@router.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": "Underwriting Intelligence Platform (UIP)",
        "version": "1.0.0",
        "actuarial_model_version": actuarial_engine.VERSION
    }


@router.get("/model-governance")
def get_model_governance():
    """
    Returns registered actuarial model versions, AIC, diagnostics, and compliance boundaries (F12).
    """
    if not actuarial_engine.is_initialized:
        actuarial_engine.train_and_calibrate(n_samples=1000)

    return {
        "framework": "MLflow / Scikit-Learn Actuarial Hub",
        "model_version": actuarial_engine.VERSION,
        "frequency_model": actuarial_engine.freq_model.get_summary(),
        "severity_model": actuarial_engine.sev_model.get_summary(),
        "benchmark_model": actuarial_engine.benchmark_model.get_summary(),
        "validity_bounds": {
            "driver_age": [18, 85],
            "licence_years": [0, 67],
            "bonus_malus": [0.50, 2.50],
            "vehicle_power": [3, 22]
        },
        "compliance": {
            "human_in_the_loop": True,
            "gdpr_sensitive_data_check": True,
            "immutable_audit_logging": True
        }
    }
