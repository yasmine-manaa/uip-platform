import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.actuarial.dataset import generate_synthetic_actuarial_dataset, prepare_features
print("1. Generating dataset...")
df = generate_synthetic_actuarial_dataset(500)
X, exp, y_freq, y_sev = prepare_features(df)
print(f"Dataset generated: {len(df)} rows.")

from app.actuarial.frequency_model import PoissonFrequencyModel
print("2. Fitting Poisson...")
p = PoissonFrequencyModel().fit(X, y_freq, exp)
print(f"Poisson AIC: {p.get_summary()['aic']:.2f}")

from app.actuarial.severity_model import GammaSeverityModel
print("3. Fitting Gamma...")
g = GammaSeverityModel().fit(X, y_sev, y_freq)
print(f"Gamma summary: {g.get_summary()['model_type']}")

from app.actuarial.ml_benchmark import XGBoostBenchmarkModel
print("4. Fitting XGBoost...")
xb = XGBoostBenchmarkModel().fit(X, y_sev)
print(f"XGBoost RMSE: {xb.get_summary()['rmse']:.2f}")

from app.actuarial.trainer import actuarial_engine
print("5. Full Actuarial Engine check...")
actuarial_engine.train_and_calibrate(n_samples=500)
res = actuarial_engine.evaluate_risk({"driver_age": 22, "vehicle_power": 9, "bonus_malus": 1.15})
print(f"Evaluation succeeded: Pure Premium = {res['calculation']['pure_premium_eur']} EUR, Tier = {res['calculation']['risk_tier']}")
print("SUCCESS!")
