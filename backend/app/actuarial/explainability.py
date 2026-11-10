"""
Actuarial Explainability Module using Native TreeSHAP and Linear Shapley Attributions.
Provides mathematically exact feature contributions and risk driver direction.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import xgboost as xgb


class ActuarialExplainer:
    def __init__(self, xgb_model=None, glm_freq_model=None, glm_sev_model=None):
        self.xgb_model = xgb_model
        self.glm_freq_model = glm_freq_model
        self.glm_sev_model = glm_sev_model

    def explain_case(self, X_case: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates local feature contributions for an insurance applicant.
        Returns:
        1. TreeSHAP feature attributions from XGBoost.
        2. Exact linear Shapley values for GLM Poisson Frequency: phi_j = beta_j * (x_j - E[X_j]).
        """
        if len(X_case) != 1:
            raise ValueError("explain_case expects a single-row DataFrame.")

        features = list(X_case.columns)
        values = X_case.iloc[0].to_dict()

        # 1. Native C++ TreeSHAP via XGBoost booster
        shap_factors: List[Dict[str, Any]] = []
        if self.xgb_model is not None and self.xgb_model.is_fitted:
            try:
                booster = self.xgb_model.model.get_booster()
                dmat = xgb.DMatrix(X_case)
                # pred_contribs=True returns TreeSHAP values for all features + bias term as the last column
                contribs = booster.predict(dmat, pred_contribs=True)[0]
                feature_contribs = contribs[:-1]  # exclude bias
                base_bias = float(contribs[-1])

                for feat, val, contrib in zip(features, X_case.iloc[0], feature_contribs):
                    shap_factors.append({
                        "feature": feat,
                        "value": float(val),
                        "contribution": float(round(contrib, 2)),
                        "impact": "INCREASES_RISK" if contrib > 0 else "DECREASES_RISK"
                    })
                shap_factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
            except Exception as e:
                shap_factors = []

        # 2. Linear Shapley Decomposition for GLM Poisson: phi_j = beta_j * (x_j - mean_j)
        glm_freq_factors: List[Dict[str, Any]] = []
        if self.glm_freq_model is not None and self.glm_freq_model.is_fitted:
            coeffs = self.glm_freq_model.training_summary.get("coefficients", {})
            means = self.glm_freq_model.mean_features
            for feat in features:
                if feat in coeffs and feat != "_intercept":
                    beta = coeffs[feat]
                    val = values.get(feat, 0.0)
                    mean_val = means.get(feat, val)
                    # Shapley attribution: deviation from portfolio mean
                    shapley_val = float(beta * (val - mean_val))
                    relative_multiplier = float(np.exp(shapley_val))
                    glm_freq_factors.append({
                        "feature": feat,
                        "applicant_value": float(val),
                        "portfolio_mean": float(round(mean_val, 2)),
                        "beta": float(round(beta, 4)),
                        "shapley_contribution": float(round(shapley_val, 4)),
                        "relative_risk_multiplier": float(round(relative_multiplier, 3)),
                        "direction": "Risk Aggravating" if shapley_val > 0 else "Risk Mitigating"
                    })
            glm_freq_factors.sort(key=lambda x: abs(x["shapley_contribution"]), reverse=True)

        return {
            "shap_factors": shap_factors,
            "glm_frequency_factors": glm_freq_factors,
            "top_risk_drivers": [f["feature"] for f in shap_factors[:3]] if shap_factors else [f["feature"] for f in glm_freq_factors[:3]],
            "interpretation": (
                "Feature impacts show relative deviation from portfolio baseline. "
                "Positive contributions increase expected claim cost; negative mitigate risk."
            )
        }
