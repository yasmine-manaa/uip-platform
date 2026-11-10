"""
Pure Premium and Actuarial Risk Assessment Calculation.
Combines Frequency GLM and Severity GLM: Pure Technical Cost E[S] = E[N] * E[Y].
Calculates uncertainty intervals, domain of validity checks, and strict actuarial disclaimers.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class PurePremiumCalculator:
    # Explicit domain of validity thresholds based on French auto underwriting standards
    VALIDITY_BOUNDS = {
        "driver_age": (18, 85),
        "licence_years": (0, 67),
        "bonus_malus": (0.50, 2.50),
        "vehicle_power": (3, 22),
        "vehicle_age": (0, 25),
        "area_density": (1, 6),
        "annual_mileage": (1000, 100000)
    }

    def __init__(self, freq_model, sev_model, benchmark_model=None):
        self.freq_model = freq_model
        self.sev_model = sev_model
        self.benchmark_model = benchmark_model

    def validate_domain(self, applicant_data: Dict[str, Any]) -> List[str]:
        """
        Checks whether applicant features fall within the empirical training distribution.
        Flags any out-of-domain (OOD) risks.
        """
        warnings: List[str] = []
        for feature, (low, high) in self.VALIDITY_BOUNDS.items():
            if feature in applicant_data and applicant_data[feature] is not None:
                val = applicant_data[feature]
                if val < low or val > high:
                    warnings.append(
                        f"Out-of-domain parameter: '{feature}' = {val} outside training envelope [{low}, {high}]."
                    )
        return warnings

    def calculate(
        self,
        X_case: pd.DataFrame,
        applicant_raw: Dict[str, Any],
        exposure: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates expected claim frequency, expected severity, pure premium,
        confidence interval, and out-of-domain flags.
        """
        # 1. Domain of validity
        domain_warnings = self.validate_domain(applicant_raw)
        is_in_domain = len(domain_warnings) == 0

        # 2. Model predictions
        pred_freq = float(self.freq_model.predict(X_case, exposure=exposure)[0])
        pred_sev = float(self.sev_model.predict(X_case)[0])
        pure_premium = float(pred_freq * pred_sev)

        # 3. Benchmark prediction (XGBoost)
        xgb_loss = None
        if self.benchmark_model and self.benchmark_model.is_fitted:
            xgb_loss = float(self.benchmark_model.predict(X_case)[0])

        # 4. Uncertainty Estimation (90% interval on pure premium)
        # Using compound Poisson-Gamma variance: Var(S) = E[N]*Var(Y) + (E[Y])^2 * Var(N)
        # For Poisson, Var(N) = lambda. For Gamma with shape k=1.8, Var(Y) = mu^2 / k
        k_shape = 1.8
        var_n = pred_freq
        var_y = (pred_sev ** 2) / k_shape
        var_s = (pred_freq * var_y) + ((pred_sev ** 2) * var_n)
        std_s = np.sqrt(max(var_s, 1.0))

        # Prediction interval (asymmetric lognormal approximation)
        ci_lower = max(0.0, float(np.round(pure_premium - 1.645 * (std_s * 0.3), 2)))
        ci_upper = float(np.round(pure_premium + 1.645 * (std_s * 0.4), 2))

        # Risk score categorization (Relative to portfolio benchmark mean ~ 240 EUR pure loss)
        portfolio_baseline_cost = 240.0
        relative_risk_ratio = pure_premium / portfolio_baseline_cost

        if relative_risk_ratio < 0.75:
            risk_tier = "LOW"
            risk_tier_description = "Risque faible (inférieur à la moyenne du portefeuille)"
        elif relative_risk_ratio <= 1.25:
            risk_tier = "MODERATE"
            risk_tier_description = "Risque modéré (conforme au standard portefeuille)"
        elif relative_risk_ratio <= 1.85:
            risk_tier = "HIGH"
            risk_tier_description = "Risque aggravé (surprime technique recommandée)"
        else:
            risk_tier = "CRITICAL"
            risk_tier_description = "Risque très élevé / profil atypique (revue humaine requise)"

        # Model uncertainty rating
        uncertainty_level = "LOW"
        if not is_in_domain:
            uncertainty_level = "HIGH"
        elif xgb_loss is not None and abs(pure_premium - xgb_loss) / max(pure_premium, 1.0) > 0.40:
            uncertainty_level = "MODERATE"

        return {
            "pure_premium_eur": round(pure_premium, 2),
            "expected_claim_frequency": round(pred_freq, 4),
            "expected_average_severity_eur": round(pred_sev, 2),
            "benchmark_ml_loss_eur": round(xgb_loss, 2) if xgb_loss is not None else None,
            "uncertainty_interval_90": {
                "lower_eur": ci_lower,
                "upper_eur": ci_upper,
                "std_error": round(float(std_s), 2)
            },
            "relative_risk_ratio": round(relative_risk_ratio, 2),
            "risk_tier": risk_tier,
            "risk_tier_description": risk_tier_description,
            "uncertainty_level": uncertainty_level,
            "is_in_domain": is_in_domain,
            "domain_warnings": domain_warnings,
            "disclaimer": (
                "AVERTISSEMENT ACTUARIEL : Cette estimation représente la charge pure attendue (E[S]) "
                "et ne constitue en aucun cas une prime commerciale. Les frais de gestion, taxes (TSCA), "
                "chargements de sécurité/réassurance et marges commerciales n'y sont pas inclus. "
                "Conformément au cahier des charges, ce modèle ne décide ni n'autorise un refus autonome."
            )
        }
