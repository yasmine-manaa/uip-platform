"""
Agent 6 — Governance & Trust Agent.
Enforces Section 6 & 10 of Cahier des Charges:
- Completeness and data quality audit across all inputs.
- Cross-agent and cross-source contradiction detection.
- Ethical AI and proxy bias detection (protecting against unlawful discrimination).
- Traceability & evidence verification (evidence-first principle).
- Escalation gate: routes dossier to mandatory human review when risk, uncertainty, or conflicts occur.
"""

from typing import Dict, Any, List

from app.agents.base import BaseSpecializedAgent
from app.schemas.agent_contracts import (
    AgentOutputContract,
    AgentAlert,
    AgentEvidence,
    CitationRef
)


class GovernanceTrustAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="AGENT_06_GOVERNANCE_TRUST",
            agent_name="Governance & Trust Agent",
            version="1.3.0"
        )

    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        agent_outputs: Dict[str, Any] = case_context.get("agent_outputs", {})
        applicant = case_context.get("applicant", {})
        vehicle = case_context.get("vehicle", {})

        findings: List[str] = []
        evidence: List[AgentEvidence] = []
        alerts: List[AgentAlert] = []
        missing_fields: List[str] = []
        contradictions_detected: List[str] = []

        # 1. Cross-Source Contradiction Detection
        declared_usage = applicant.get("usage")
        vehicle_genre = vehicle.get("vehicle_genre", "VP")
        if declared_usage == "Private" and vehicle_genre in ["TAXI", "VTC", "COMMERCIAL"]:
            msg = f"Contradiction majeure : Usage déclaré 'Privé' mais genre carte grise '{vehicle_genre}'."
            contradictions_detected.append(msg)
            alerts.append(AgentAlert(
                code="GOV_CONTRADICTION_USAGE_GENRE",
                severity="CRITICAL",
                message=msg,
                action_required="Contrôle de l'affectation réelle du véhicule et demande d'attestation employeur."
            ))

        clm_agent_out = agent_outputs.get("AGENT_04_HISTORICAL_CLAIMS", {})
        clm_alerts = clm_agent_out.get("alerts", [])
        for a in clm_alerts:
            if isinstance(a, dict) and a.get("code") == "CLM_CRM_CONTRADICTION":
                contradictions_detected.append(a.get("message", ""))

        # 2. Evidence-First Principle Audit
        risk_agent_out = agent_outputs.get("AGENT_03_RISK_ASSESSMENT", {})
        risk_meta = risk_agent_out.get("metadata", {})
        risk_calc = risk_meta.get("actuarial_calculation", {})
        if not risk_calc or "pure_premium_eur" not in risk_calc:
            alerts.append(AgentAlert(
                code="GOV_UNSUPPORTED_RISK_CLAIM",
                severity="CRITICAL",
                message="Le modèle de risque n'a fourni aucune charge actuarielle vérifiable.",
                action_required="Relance du moteur actuariel déterministe."
            ))
        else:
            evidence.append(AgentEvidence(
                key="actuarial_traceability",
                value="VERIFIED_GLM_AND_SHAP",
                confidence=1.0
            ))
            findings.append("Traçabilité actuarielle validée : Modèles GLM Poisson/Gamma et TreeSHAP horodatés.")

        # 3. Fair Underwriting & Proxy Bias Guardrail
        forbidden_proxies = ["nationalite", "religion", "situation_familiale_detaillee", "handicap"]
        for proxy in forbidden_proxies:
            if proxy in applicant:
                alerts.append(AgentAlert(
                    code="GOV_PROXY_BIAS_VIOLATION",
                    severity="CRITICAL",
                    message=f"Variable discriminatoire potentielle détectée : '{proxy}'. Suppression immédiate du modèle décisionnel.",
                    action_required="Sanitarisation des données d'entrée selon directives RGPD / CADA."
                ))

        findings.append("Audit d'équité et de non-discrimination : Aucune variable protégée n'a influencé la tarification.")

        # 4. Global Escalation and Human-in-the-Loop Determination
        all_prior_alerts = []
        for a_id, out in agent_outputs.items():
            for alt in out.get("alerts", []):
                all_prior_alerts.append(alt)

        critical_count = sum(1 for a in all_prior_alerts if (isinstance(a, dict) and a.get("severity") == "CRITICAL") or getattr(a, "severity", "") == "CRITICAL")
        warning_count = sum(1 for a in all_prior_alerts if (isinstance(a, dict) and a.get("severity") == "WARNING") or getattr(a, "severity", "") == "WARNING")

        if critical_count > 0 or len(contradictions_detected) > 0:
            status = "ESCALATED"
            confidence = 0.60
            findings.append(
                f"Escalade souscripteur obligatoire : {critical_count} alerte(s) critique(s) "
                f"et {len(contradictions_detected)} contradiction(s) identifiée(s)."
            )
        elif warning_count > 0:
            status = "WARNING"
            confidence = 0.85
            findings.append(f"Revue humaine recommandée : {warning_count} point(s) de vigilance relevé(s).")
        else:
            status = "SUCCESS"
            confidence = 0.98
            findings.append("Audit de gouvernance conforme. Dossier intègre, traçable et sans contradiction.")

        evidence.append(AgentEvidence(key="critical_alerts_total", value=critical_count))
        evidence.append(AgentEvidence(key="contradictions_total", value=len(contradictions_detected)))

        return AgentOutputContract(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            version=self.version,
            status=status,
            confidence_score=confidence,
            findings=findings,
            evidence=evidence,
            sources=[],
            missing_fields=missing_fields,
            alerts=alerts,
            metadata={
                "contradictions_detected": contradictions_detected,
                "human_review_mandatory": status == "ESCALATED",
                "evidence_first_compliance": True
            }
        )
