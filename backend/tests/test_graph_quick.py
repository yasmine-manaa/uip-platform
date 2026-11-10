import sys
import os
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.actuarial.trainer import actuarial_engine
from app.orchestrator.graph import underwriting_graph

async def test_run():
    print("Pre-training actuarial models (1000 samples)...", flush=True)
    actuarial_engine.train_and_calibrate(n_samples=1000)

    test_case = {
        "case_id": "CASE-TEST-001",
        "applicant": {
            "full_name": "Jean Dupont",
            "driver_age": 32,
            "licence_years": 12,
            "usage": "Commuting",
            "postal_code": "75011",
            "annual_mileage": 12000
        },
        "vehicle": {
            "vehicle_model": "PEUGEOT 208",
            "vehicle_power": 5,
            "vehicle_age": 3,
            "vehicle_genre": "VP"
        },
        "claims_summary": {
            "bonus_malus": 0.68,
            "prior_claims_count": 0
        },
        "coverage_requested": "Tous Risques",
        "area_density": 5
    }

    print("Executing LangGraph multi-agent workflow...", flush=True)
    result = await underwriting_graph.ainvoke(test_case)
    print("Graph execution complete!", flush=True)
    print(f"Agents run count: {len(result.get('agent_outputs', {}))}", flush=True)
    dec = result.get("provisional_decision", {})
    print(f"Decision code: {dec.get('decision_code')}", flush=True)
    print(f"Decision title: {dec.get('decision_title')}", flush=True)
    print(f"Provisional Reco: {dec.get('provisional_recommendation')}", flush=True)
    print("Timeline steps:", [t['step'] for t in result.get('execution_timeline', [])], flush=True)
    print("SUCCESS!", flush=True)

if __name__ == "__main__":
    asyncio.run(test_run())
