"""
Underwriting Intelligence Platform (UIP) - Main FastAPI Application.
Plateforme intelligente d'aide à la souscription et à l'évaluation des risques en assurance.
Conforme au Cahier des Charges Fonctionnel et Technique (PFE).
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.database import engine, Base, SessionLocal
from app.api import api_router
from app.actuarial.trainer import actuarial_engine
from app.seed_data.demo_cases import seed_demo_cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create DB Tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Calibrate Actuarial Engine
    print("[UIP Backend] Initializing Actuarial Engine...", flush=True)
    if not actuarial_engine.is_initialized:
        actuarial_engine.train_and_calibrate(n_samples=1500)
    print(f"[UIP Backend] Actuarial Engine calibrated (v{actuarial_engine.VERSION}).", flush=True)

    # 3. Seed Demo Data
    db = SessionLocal()
    try:
        seed_demo_cases(db)
        print("[UIP Backend] Demo cases and reference policies seeded successfully.", flush=True)
    finally:
        db.close()

    yield
    print("[UIP Backend] Shutting down clean.", flush=True)


app = FastAPI(
    title="Underwriting Intelligence Platform (UIP) API",
    description=(
        "Plateforme intelligente d'aide à la souscription et à l'évaluation des risques en assurance. "
        "Combine traitement documentaire, RAG vérifiable, modèles actuariels (GLM Poisson/Gamma, XGBoost, SHAP), "
        "agents IA spécialisés, et gouvernance Human-in-the-Loop avec traçabilité cryptographique."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API v1 endpoints
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Underwriting Intelligence Platform",
        "actuarial_version": actuarial_engine.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
