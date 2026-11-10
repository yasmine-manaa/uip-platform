"""
Actuarial GLM Poisson Frequency Model for Auto Insurance.
Estimates expected annual claim frequency: E[N] = exposure * exp(X * beta + intercept0).
Includes diagnostic metrics: Poisson Deviance, AIC, Score statistics.
Uses sklearn PoissonRegressor (C-optimized GLM with Log Link).
"""

from typing import Dict, Any, Optional
import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import d2_tweedie_score


class PoissonFrequencyModel:
    def __init__(self, alpha: float = 1e-4):
        self.alpha = alpha
        self.model = PoissonRegressor(alpha=self.alpha, max_iter=300)
        self.feature_names = []
        self.is_fitted = False
        self.training_summary: Dict[str, Any] = {}
        self.mean_features: Dict[str, float] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series, exposure: Optional[pd.Series] = None):
        """
        Fits a Poisson GLM with log link and exposure weights.
        """
        self.feature_names = list(X.columns)
        self.mean_features = {col: float(X[col].mean()) for col in self.feature_names}
        
        sample_weight = np.clip(exposure.to_numpy(), 0.05, 1.0) if exposure is not None else None
        self.model.fit(X, y, sample_weight=sample_weight)
        self.is_fitted = True

        pred = self.model.predict(X)
        y_val = y.to_numpy()
        pred_val = np.clip(pred, 1e-6, None)
        # Poisson deviance: 2 * sum( y * log(y / mu) - (y - mu) )
        with np.errstate(divide='ignore', invalid='ignore'):
            term = np.where(y_val > 0, y_val * np.log(y_val / pred_val), 0.0)
            deviance = float(2.0 * np.sum(term - (y_val - pred_val)))

        k = len(self.feature_names) + 1
        n = len(y)
        # AIC approximation for Poisson GLM
        aic = float(deviance + 2 * k)

        coeffs = dict(zip(self.feature_names, [float(c) for c in self.model.coef_]))
        coeffs["_intercept"] = float(self.model.intercept_)

        self.training_summary = {
            "model_type": "GLM Poisson (Log Link)",
            "aic": round(aic, 2),
            "deviance": round(deviance, 2),
            "n_observations": int(n),
            "n_features": int(len(self.feature_names)),
            "coefficients": coeffs
        }
        return self

    def predict(self, X: pd.DataFrame, exposure: float = 1.0) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Poisson model must be fitted before predict.")
        X_aligned = X.reindex(columns=self.feature_names, fill_value=0.0)
        base_rate = self.model.predict(X_aligned)
        return base_rate * float(exposure)

    def get_summary(self) -> Dict[str, Any]:
        return self.training_summary
