"""
Agent 3 — Risk Assessment Agent.
Calls the pure statistical Actuarial Engine (GLM Poisson, GLM Gamma, XGBoost benchmark),
computes pure technical risk cost, confidence intervals, and SHAP explainability.
Enforces the strict rule: Pure statistical cost != commercial premium, no autonomous refusal.
"""

from typing import Dict, Any, List

try:
    from app.agents.base import BaseSpecializedAgent
    from app.actuarial.trainer import actuarial_engine
    from app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )
except ImportError:
    from .base import BaseSpecializedAgent
    from backend.app.actuarial.trainer import actuarial_engine
    from backend.app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )


class RiskAssessmentAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="AGENT_03_RISK_ASSESSMENT",
            agent_name="Risk Assessment Agent",
            version="2.1.0"
        )

    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        applicant = case_context.get("applicant", {})
        vehicle = case_context.get("vehicle", {})
        claims_summary = case_context.get("claims_summary", {})

        crm = claims_summary.get("bonus_malus")
        if crm is None:
            crm = applicant.get("bonus_malus")

        actuarial_input = {
            "driver_age": applicant.get("driver_age", 35),
            "licence_years": applicant.get("licence_years", 10),
            "bonus_malus": crm,
            "prior_claims_count": claims_summary.get("prior_claims_count", 0),
            "vehicle_power": vehicle.get("vehicle_power", 6),
            "vehicle_age": vehicle.get("vehicle_age", 4),
            "area_density": case_context.get("area_density", 3),
            "annual_mileage": applicant.get("annual_mileage", 15000),
            "usage": applicant.get("usage", "Commuting")
        }

        actuarial_res = actuarial_engine.evaluate_risk(actuarial_input)
        calc = actuarial_res["calculation"]
        explain = actuarial_res["explainability"]

        findings: List[str] = []
        evidence: List[AgentEvidence] = []
        alerts: List[AgentAlert] = []

        pure_prem = calc["pure_premium_eur"]
        freq = calc["expected_claim_frequency"]
        sev = calc["expected_average_severity_eur"]
        tier = calc["risk_tier"]
        ratio = calc["relative_risk_ratio"]
        ci = calc["uncertainty_interval_90"]

        evidence.append(AgentEvidence(key="pure_premium_eur", value=pure_prem, source_ref="Actuarial GLM Engine"))
        evidence.append(AgentEvidence(key="expected_frequency", value=freq, source_ref="Poisson GLM"))
        evidence.append(AgentEvidence(key="expected_severity_eur", value=sev, source_ref="Gamma GLM"))
        evidence.append(AgentEvidence(key="risk_tier", value=tier))
        evidence.append(AgentEvidence(key="relative_risk_ratio", value=ratio))

        findings.append(
            f"Charge pure technique estimée à {pure_prem:.2f} € / an "
            f"(Fréquence attendue : {freq*100:.2f} %, Coût moyen : {sev:.0f} €)."
        )
        findings.append(
            f"Positionnement portefeuille : {calc['risk_tier_description']} (Ratio relatif : {ratio:.2f}x)."
        )
        findings.append(
            f"Intervalle d'incertitude 90 % : [{ci['lower_eur']} €, {ci['upper_eur']} €]."
        )

        top_drivers = explain.get("top_risk_drivers", [])
        if top_drivers:
            findings.append(f"Facteurs d'influence prépondérants identifiés par SHAP : {', '.join(top_drivers)}.")

        if not calc["is_in_domain"]:
            for warn in calc["domain_warnings"]:
                alerts.append(AgentAlert(
                    code="ACT_OUT_OF_DOMAIN",
                    severity="WARNING",
                    message=warn,
                    action_required="Expertise actuarielle requise pour profil hors enveloppe d'apprentissage."
                ))

        if tier in ["HIGH", "CRITICAL"]:
            alerts.append(AgentAlert(
                code="ACT_ELEVATED_RISK",
                severity="WARNING" if tier == "HIGH" else "CRITICAL",
                message=f"Niveau de risque actuariel '{tier}'. Fréquence ou sévérité nettement supérieure à la moyenne.",
                action_required="Application d'une surprime technique ou majoration de franchise par le souscripteur."
            ))

        if any(a.severity == "CRITICAL" for a in alerts):
            status = "ESCALATED"
            confidence = 0.75
        elif any(a.severity == "WARNING" for a in alerts):
            status = "WARNING"
            confidence = 0.88
        else:
            status = "SUCCESS"
            confidence = 0.95

        return AgentOutputContract(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            version=self.version,
            status=status,
            confidence_score=confidence,
            findings=findings,
            evidence=evidence,
            sources=[],
            missing_fields=[],
            alerts=alerts,
            metadata={
                "actuarial_calculation": calc,
                "explainability": explain,
                "disclaimer": calc["disclaimer"]
            }
        )
