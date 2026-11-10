import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import sys, time

backend_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

print("Checkpoint 1: Starting script", flush=True)

from app.agents.profile_agent import CustomerProfileAgent
print("Checkpoint 2: Profile Agent loaded", flush=True)

from app.agents.policy_agent import PolicyDocumentAgent
print("Checkpoint 3: Policy Agent loaded", flush=True)

from app.agents.risk_agent import RiskAssessmentAgent
print("Checkpoint 4: Risk Agent loaded", flush=True)

from app.agents.claims_agent import HistoricalClaimsAgent
print("Checkpoint 5: Claims Agent loaded", flush=True)

from app.agents.external_agent import ExternalIntelligenceAgent
print("Checkpoint 6: External Agent loaded", flush=True)

from app.agents.governance_agent import GovernanceTrustAgent
print("Checkpoint 7: Governance Agent loaded", flush=True)

from app.orchestrator.decision_engine import DeterministicDecisionEngine
print("Checkpoint 8: Decision Engine loaded", flush=True)

from app.orchestrator.graph import execute_underwriting_workflow
print("Checkpoint 9: execute_underwriting_workflow loaded", flush=True)

import asyncio

async def run():
    print("Checkpoint 10: Running workflow...", flush=True)
    res = await execute_underwriting_workflow({
        "case_id": "CASE-DEMO-001",
        "applicant": {"full_name": "Jean Dupont", "driver_age": 32, "licence_years": 12, "usage": "Commuting", "postal_code": "75011"},
        "vehicle": {"vehicle_model": "PEUGEOT 208", "vehicle_power": 5, "vehicle_age": 3, "vehicle_genre": "VP"},
        "claims_summary": {"bonus_malus": 0.68, "prior_claims_count": 0},
        "coverage_requested": "Tous Risques",
        "area_density": 5
    })
    print("Checkpoint 11: Workflow completed successfully!", flush=True)
    print("Decision Code:", res["provisional_decision"]["decision_code"], flush=True)

asyncio.run(run())
