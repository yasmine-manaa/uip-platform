"""
Agent 4 — Historical Claims Agent.
Analyzes prior claims, frequency, severity, recency, CRM coefficient consistency,
and checks prior insurer cancellation history.
"""

from typing import Dict, Any, List

try:
    from app.agents.base import BaseSpecializedAgent
    from app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )
except ImportError:
    from .base import BaseSpecializedAgent
    from backend.app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )


class HistoricalClaimsAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="AGENT_04_HISTORICAL_CLAIMS",
            agent_name="Historical Claims Agent",
            version="1.2.0"
        )

    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        claims_data = case_context.get("claims_summary", {})
        prior_claims = case_context.get("claims_list", [])

        findings: List[str] = []
        evidence: List[AgentEvidence] = []
        alerts: List[AgentAlert] = []
        missing_fields: List[str] = []

        bonus_malus = claims_data.get("bonus_malus")
        prior_count = claims_data.get("prior_claims_count", len(prior_claims))
        has_cancellation = claims_data.get("cancelled_by_previous_insurer", False)
        cancellation_reason = claims_data.get("cancellation_reason", "")

        # 1. Verification of Bonus-Malus
        if bonus_malus is None:
            missing_fields.append("bonus_malus")
            alerts.append(AgentAlert(
                code="CLM_MISSING_CRM",
                severity="WARNING",
                message="Le relevé d'information officiel attestant du coefficient Bonus-Malus n'est pas fourni.",
                action_required="Exiger le Relevé d'Information 36 mois de la précédente compagnie."
            ))
        else:
            evidence.append(AgentEvidence(key="bonus_malus", value=bonus_malus, source_ref="Relevé d'information"))
            if bonus_malus <= 0.50:
                findings.append(f"Excellent historique de conduite : Bonus maximum atteint (CRM {bonus_malus:.2f}).")
            elif bonus_malus > 1.20:
                alerts.append(AgentAlert(
                    code="CLM_HIGH_MALUS",
                    severity="WARNING",
                    message=f"Malus élevé ({bonus_malus:.2f}). Sinistralité antérieure significative.",
                    action_required="Vérifier l'historique détaillé des sinistres sur 36 mois."
                ))

        # 2. Responsible Claims Frequency & Recency
        evidence.append(AgentEvidence(key="prior_claims_count", value=prior_count))
        if prior_count == 0:
            findings.append("Aucun sinistre responsable déclaré au cours des 36 derniers mois.")
        elif prior_count == 1:
            findings.append("1 sinistre responsable enregistré sur les 36 derniers mois.")
        elif prior_count >= 2:
            alerts.append(AgentAlert(
                code="CLM_REPEAT_OFFENDER",
                severity="CRITICAL" if prior_count >= 3 else "WARNING",
                message=f"Fréquence de sinistralité anormale : {prior_count} sinistres responsables récents.",
                action_required="Application obligatoire d'une surprime technique ou limitation de garantie (Règle R-SIN-01)."
            ))

        # 3. CRM vs Claims Consistency Guardrail
        if bonus_malus is not None and bonus_malus <= 0.50 and prior_count > 0:
            alerts.append(AgentAlert(
                code="CLM_CRM_CONTRADICTION",
                severity="CRITICAL",
                message=f"Incohérence majeure : CRM déclaré à {bonus_malus:.2f} (bonus maximal) alors que {prior_count} sinistre(s) responsable(s) sont déclarés.",
                action_required="Contrôle d'authenticité du Relevé d'Information via le fichier AGIRA."
            ))

        # 4. Previous Insurer Cancellation
        if has_cancellation:
            alerts.append(AgentAlert(
                code="CLM_PREVIOUS_CANCELLATION",
                severity="CRITICAL",
                message=f"Résiliation par l'assureur précédent signalée. Motif : '{cancellation_reason or 'Non communiqué'}'.",
                action_required="Revue experte souscripteur obligatoire (Règle R-SIN-02)."
            ))

        if any(a.severity == "CRITICAL" for a in alerts):
            status = "ESCALATED"
            confidence = 0.70
        elif missing_fields:
            status = "DATA_DEFICIENT"
            confidence = 0.75
        elif any(a.severity == "WARNING" for a in alerts):
            status = "WARNING"
            confidence = 0.88
        else:
            status = "SUCCESS"
            confidence = 0.96

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
            alerts=alerts
        )
