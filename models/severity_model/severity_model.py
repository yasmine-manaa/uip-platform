"""
Actuarial GLM Gamma Severity Model for Auto Insurance.
Estimates expected conditional claim cost: E[Y | N > 0] = exp(X * beta + intercept0).
Trained strictly on positive claim records (claims > 0).
Uses sklearn GammaRegressor (C-optimized GLM with Log Link).
"""

from typing import Dict, Any, Optional
import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import numpy as np
import pandas as pd
from sklearn.linear_model import GammaRegressor


class GammaSeverityModel:
    def __init__(self, alpha: float = 1e-4):
        self.alpha = alpha
        self.model = GammaRegressor(alpha=self.alpha, max_iter=300)
        self.feature_names = []
        self.is_fitted = False
        self.mean_fallback = 2200.0
        self.training_summary: Dict[str, Any] = {}
        self.mean_features: Dict[str, float] = {}

    def fit(self, X: pd.DataFrame, y_cost: pd.Series, claim_count: pd.Series):
        """
        Fits a Gamma GLM on policies with positive claims (claim_count > 0).
        y_cost / claim_count represents the average cost per claim.
        """
        self.feature_names = list(X.columns)
        self.mean_features = {col: float(X[col].mean()) for col in self.feature_names}
        
        # Filter strictly positive claims
        mask = (claim_count > 0) & (y_cost > 0)
        X_pos = X[mask]
        avg_claim_cost = (y_cost[mask] / claim_count[mask]).to_numpy()

        if len(X_pos) < 15:
            self.mean_fallback = float(np.mean(avg_claim_cost)) if len(avg_claim_cost) > 0 else 2200.0
            self.is_fitted = True
            self.training_summary = {
                "model_type": "Gamma GLM Baseline (Sparse Sample)",
                "mean_cost": round(self.mean_fallback, 2),
                "n_observations": int(len(X_pos))
            }
            return self

        self.model.fit(X_pos, avg_claim_cost)
        self.is_fitted = True
        self.mean_fallback = float(np.mean(avg_claim_cost))

        pred = np.clip(self.model.predict(X_pos), 1.0, None)
        # Gamma deviance: 2 * sum( -log(y/mu) + (y - mu)/mu )
        with np.errstate(divide='ignore', invalid='ignore'):
            term = -np.log(avg_claim_cost / pred) + ((avg_claim_cost - pred) / pred)
            gamma_dev = float(2.0 * np.sum(term))

        k = len(self.feature_names) + 1
        aic = float(gamma_dev + 2 * k)

        coeffs = dict(zip(self.feature_names, [float(c) for c in self.model.coef_]))
        coeffs["_intercept"] = float(self.model.intercept_)

        self.training_summary = {
            "model_type": "GLM Gamma (Log Link)",
            "aic": round(aic, 2),
            "deviance": round(gamma_dev, 2),
            "n_observations": int(len(X_pos)),
            "mean_observed_cost": round(self.mean_fallback, 2),
            "coefficients": coeffs
        }
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Gamma severity model must be fitted before predict.")
        X_aligned = X.reindex(columns=self.feature_names, fill_value=0.0)
        return self.model.predict(X_aligned)

    def get_summary(self) -> Dict[str, Any]:
        return self.training_summary
