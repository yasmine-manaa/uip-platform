"""
Actuarial Engine Manager and Orchestrator.
Trains or initializes GLM Poisson, GLM Gamma, and XGBoost models.
Provides unified inference, SHAP explanations, and model metadata tracking (Section 10.4 & 12).
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
import numpy as np

from app.actuarial.dataset import generate_synthetic_actuarial_dataset, prepare_features
from app.actuarial.fre_mtpl2_loader import fre_mtpl2_loader
from app.actuarial.frequency_model import PoissonFrequencyModel
from app.actuarial.severity_model import GammaSeverityModel
from app.actuarial.ml_benchmark import XGBoostBenchmarkModel
from app.actuarial.explainability import ActuarialExplainer
from app.actuarial.pure_premium import PurePremiumCalculator


class ActuarialEngine:
    VERSION = "2.1.0-actuarial"

    def __init__(self, artifacts_dir: Optional[str] = None):
        self.artifacts_dir = artifacts_dir or os.path.join(os.path.dirname(__file__), "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        self.freq_model = PoissonFrequencyModel()
        self.sev_model = GammaSeverityModel()
        self.benchmark_model = XGBoostBenchmarkModel()
        self.explainer: Optional[ActuarialExplainer] = None
        self.calculator: Optional[PurePremiumCalculator] = None
        self.feature_columns = []
        self.is_initialized = False

    def train_and_calibrate(self, n_samples: int = 1500, random_seed: int = 42):
        """
        Trains GLM Frequency, GLM Severity, and XGBoost models on the real freMTPL2 dataset.
        Falls back to synthetic data if freMTPL2 is not available.
        """
        try:
            # Try to load real freMTPL2 dataset
            df = fre_mtpl2_loader.merge_datasets()
            if len(df) > n_samples:
                df = df.sample(n=n_samples, random_state=random_seed)
            X, y_freq, y_sev = fre_mtpl2_loader.prepare_features(df)
            self.feature_columns = list(X.columns)
            exposure = pd.Series([1.0] * len(X))  # Default exposure for freMTPL2
            print(f"[Actuarial Engine] Using real freMTPL2 dataset: {len(df)} samples")
        except Exception as e:
            print(f"[Actuarial Engine] freMTPL2 not available ({e}), using synthetic data")
            df = generate_synthetic_actuarial_dataset(n_samples=n_samples, random_seed=random_seed)
            X, exposure, y_freq, y_sev = prepare_features(df)
            self.feature_columns = list(X.columns)

        # 1. Fit Poisson Frequency
        self.freq_model.fit(X, y_freq, exposure=exposure)

        # 2. Fit Gamma Severity
        self.sev_model.fit(X, y_sev, claim_count=y_freq)

        # 3. Fit XGBoost Regressor
        self.benchmark_model.fit(X, y_sev)

        # 4. Initialize Explainer and Calculator
        self.explainer = ActuarialExplainer(
            xgb_model=self.benchmark_model,
            glm_freq_model=self.freq_model,
            glm_sev_model=self.sev_model
        )
        self.calculator = PurePremiumCalculator(
            freq_model=self.freq_model,
            sev_model=self.sev_model,
            benchmark_model=self.benchmark_model
        )
        self.is_initialized = True

    def _prepare_single_case(self, applicant_data: Dict[str, Any]) -> pd.DataFrame:
        usage_val = applicant_data.get("usage") or "Private"
        mileage = float(applicant_data.get("annual_mileage") or 15000)
        crm_val = float(applicant_data.get("bonus_malus") if applicant_data.get("bonus_malus") is not None else 0.85)
        age_val = float(applicant_data.get("driver_age") or 35)
        licence_val = float(applicant_data.get("licence_years") or 10)
        claims_val = float(applicant_data.get("prior_claims_count") or 0)
        power_val = float(applicant_data.get("vehicle_power") or 6)
        v_age = float(applicant_data.get("vehicle_age") or 4)
        density_val = float(applicant_data.get("area_density") or 3)

        # Clamp out-of-domain values to freMTPL2 ranges
        warnings = []
        if power_val > 25 or power_val < 3:
            warnings.append(f"vehicle_power {power_val} hors domaine [3,25], clampé à 25")
            power_val = min(max(power_val, 3), 25)
        if age_val < 18 or age_val > 85:
            warnings.append(f"driver_age {age_val} hors domaine [18,85], clampé")
            age_val = min(max(age_val, 18), 85)
        if crm_val < 0.50 or crm_val > 2.50:
            warnings.append(f"bonus_malus {crm_val} hors domaine [0.50,2.50], clampé")
            crm_val = min(max(crm_val, 0.50), 2.50)
        if licence_val < 0 or licence_val > 67:
            warnings.append(f"licence_years {licence_val} hors domaine [0,67], clampé")
            licence_val = min(max(licence_val, 0), 67)
        if mileage < 4000 or mileage > 70000:
            warnings.append(f"annual_mileage {mileage} hors domaine [4000,70000], clampé")
            mileage = min(max(mileage, 4000), 70000)
        if density_val < 1 or density_val > 6:
            warnings.append(f"area_density {density_val} hors domaine [1,6], clampé")
            density_val = min(max(density_val, 1), 6)

        row = {
            "driver_age": age_val,
            "licence_years": licence_val,
            "bonus_malus": crm_val,
            "prior_claims_count": claims_val,
            "vehicle_power": power_val,
            "vehicle_age": v_age,
            "area_density": density_val,
            "annual_mileage_10k": mileage / 10000.0,
            "usage_Commuting": 1.0 if usage_val == "Commuting" else 0.0,
            "usage_Private": 1.0 if usage_val == "Private" else 0.0,
            "usage_Professional": 1.0 if usage_val == "Professional" else 0.0,
            "usage_Taxi_VTC": 1.0 if usage_val == "Taxi_VTC" else 0.0,
        }
        df_case = pd.DataFrame([row])
        for col in self.feature_columns:
            if col not in df_case.columns:
                df_case[col] = 0.0
        return df_case[self.feature_columns]

    def evaluate_risk(self, applicant_data: Dict[str, Any], exposure: float = 1.0) -> Dict[str, Any]:
        if not self.is_initialized:
            self.train_and_calibrate()

        X_case = self._prepare_single_case(applicant_data)
        calc_results = self.calculator.calculate(X_case, applicant_data, exposure=exposure)
        explain_results = self.explainer.explain_case(X_case)

        return {
            "model_version": self.VERSION,
            "calculation": calc_results,
            "explainability": explain_results,
            "model_metrics": {
                "frequency_model": self.freq_model.get_summary(),
                "severity_model": self.sev_model.get_summary(),
                "ml_benchmark": self.benchmark_model.get_summary()
            }
        }


# Global singleton instance for backend reuse
actuarial_engine = ActuarialEngine()
