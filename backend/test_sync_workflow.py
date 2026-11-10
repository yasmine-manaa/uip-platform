import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import sys, time

backend_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from app.orchestrator.graph import execute_underwriting_workflow

print("Starting sync workflow execution...", flush=True)
t0 = time.time()

res = execute_underwriting_workflow({
    "case_id": "CASE-DEMO-001",
    "applicant": {"full_name": "Jean Dupont", "driver_age": 32, "licence_years": 12, "usage": "Commuting", "postal_code": "75011"},
    "vehicle": {"vehicle_model": "PEUGEOT 208", "vehicle_power": 5, "vehicle_age": 3, "vehicle_genre": "VP"},
    "claims_summary": {"bonus_malus": 0.68, "prior_claims_count": 0},
    "coverage_requested": "Tous Risques",
    "area_density": 5
})

print(f"Workflow finished in {time.time()-t0:.2f}s!", flush=True)
print("Decision Code:", res["provisional_decision"]["decision_code"], flush=True)
print("Decision Title:", res["provisional_decision"]["decision_title"], flush=True)
print("Provisional Reco:", res["provisional_decision"]["provisional_recommendation"], flush=True)
print("Agents count:", len(res["agent_outputs"]), flush=True)
for a_id, out in res["agent_outputs"].items():
    print(f"  [{a_id}] status={out['status']}, conf={out['confidence_score']:.2f}, findings={len(out['findings'])}, alerts={len(out['alerts'])}", flush=True)
print("SUCCESS!")
