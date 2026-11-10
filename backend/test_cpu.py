import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import sys

backend_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from app.actuarial.trainer import actuarial_engine

print("Evaluating risk in test_cpu...", flush=True)
res = actuarial_engine.evaluate_risk({"driver_age": 30, "vehicle_power": 6})
print("Risk evaluation completed:", res["calculation"]["pure_premium_eur"], flush=True)
