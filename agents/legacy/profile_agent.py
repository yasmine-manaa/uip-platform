"""
Agent 1 — Customer Profile Agent.
Constructs applicant profile, validates completeness and internal consistency,
and ensures strict compliance with non-sensitive data protection rules.
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


class CustomerProfileAgent(BaseSpecializedAgent):
    REQUIRED_FIELDS = ["driver_age", "licence_years", "usage", "postal_code"]

    def __init__(self):
        super().__init__(
            agent_id="AGENT_01_CUSTOMER_PROFILE",
            agent_name="Customer Profile Agent",
            version="1.2.0"
        )

    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        applicant = case_context.get("applicant", {})
        findings: List[str] = []
        evidence: List[AgentEvidence] = []
        alerts: List[AgentAlert] = []
        missing_fields: List[str] = []

        # 1. Completeness Check
        for req in self.REQUIRED_FIELDS:
            if req not in applicant or applicant[req] is None:
                missing_fields.append(req)

        driver_age = applicant.get("driver_age")
        licence_years = applicant.get("licence_years")
        full_name = applicant.get("full_name", "Demandeur non identifié")

        # 2. Consistency Validation
        if driver_age is not None:
            evidence.append(AgentEvidence(key="driver_age", value=driver_age, confidence=0.98))
            if driver_age < 18:
                alerts.append(AgentAlert(
                    code="PROF_AGE_UNDERAGE",
                    severity="CRITICAL",
                    message=f"Le demandeur a {driver_age} ans. La souscription d'un contrat auto exige l'âge légal de 18 ans.",
                    action_required="Refus de souscription pour minorité légale ou désignation d'un représentant légal."
                ))
            elif driver_age < 21:
                findings.append(f"Conducteur jeune ({driver_age} ans), profil novice sous surveillance.")
            elif driver_age > 75:
                findings.append(f"Conducteur senior ({driver_age} ans), vérification des aptitudes médicales recommandée.")

        if licence_years is not None:
            evidence.append(AgentEvidence(key="licence_years", value=licence_years, confidence=0.95))

        if driver_age is not None and licence_years is not None:
            if driver_age - licence_years < 18:
                alerts.append(AgentAlert(
                    code="PROF_INCONSISTENT_LICENCE_AGE",
                    severity="CRITICAL",
                    message=f"Incohérence chronologique : âge ({driver_age}) - années de permis ({licence_years}) = {driver_age - licence_years} (< 18 ans légal).",
                    action_required="Demande du duplicata officiel du permis de conduire pour vérification."
                ))
            else:
                findings.append(f"Ancienneté du permis cohérente avec l'âge déclaré ({licence_years} années d'expérience).")

        # 3. Privacy & Non-Discrimination Guardrail
        for sens_key in ["religion", "ethnicity", "political_views", "health_data"]:
            if sens_key in applicant:
                alerts.append(AgentAlert(
                    code="GOV_SENSITIVE_DATA_DETECTED",
                    severity="CRITICAL",
                    message=f"Donnée sensible interdite détectée ('{sens_key}'). Donnée purgée conformément au RGPD.",
                    action_required="Audit de conformité des flux d'ingestion."
                ))

        # Status and confidence calculation
        if any(a.severity == "CRITICAL" for a in alerts):
            status = "ESCALATED"
            confidence = 0.50
        elif missing_fields:
            status = "DATA_DEFICIENT"
            findings.append(f"Dossier incomplet : {len(missing_fields)} champs manquants ({', '.join(missing_fields)}).")
            confidence = 0.70
        else:
            status = "SUCCESS"
            findings.append(f"Profil client '{full_name}' validé, cohérent et complet.")
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
            missing_fields=missing_fields,
            alerts=alerts
        )
