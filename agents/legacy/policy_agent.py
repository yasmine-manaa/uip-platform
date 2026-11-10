"""
Agent 2 — Policy & Document Agent.
Analyzes contractual corpus, checks guarantees, exclusions, and deductibles,
and returns exact verifiable citations (document, page, article).
"""

from typing import Dict, Any, List

try:
    from app.agents.base import BaseSpecializedAgent
    from app.document_engine.vector_store import policy_vector_store
    from app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )
except ImportError:
    from .base import BaseSpecializedAgent
    from backend.app.document_engine.vector_store import policy_vector_store
    from backend.app.schemas.agent_contracts import (
        AgentOutputContract,
        AgentAlert,
        AgentEvidence,
        CitationRef
    )


class PolicyDocumentAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="AGENT_02_POLICY_DOCUMENT",
            agent_name="Policy & Document Agent",
            version="1.2.0"
        )

    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        applicant = case_context.get("applicant", {})
        vehicle = case_context.get("vehicle", {})
        coverage_requested = case_context.get("coverage_requested", "Tous Risques")

        findings: List[str] = []
        evidence: List[AgentEvidence] = []
        alerts: List[AgentAlert] = []
        sources: List[CitationRef] = []
        missing_fields: List[str] = []

        usage = applicant.get("usage", "Commuting")
        vehicle_power = vehicle.get("vehicle_power", 6)
        licence_years = applicant.get("licence_years", 5)

        # 1. RAG Search on Policy Corpus for requested coverage
        search_results = policy_vector_store.search(f"Garantie {coverage_requested} exclusions franchise conditions", top_k=3)
        for r in search_results:
            sources.append(CitationRef(
                citation_id=r["citation_id"],
                doc_id=r["doc_id"],
                doc_title=r["doc_title"],
                page=r["page"],
                article=r["article"],
                snippet=r["content_snippet"],
                relevance_score=r["relevance_score"]
            ))

        findings.append(f"Garantie demandée : '{coverage_requested}'. Rapprochement contractuel effectué avec {len(sources)} clauses référencées.")

        # 2. Check Vehicle Power & Novice Rules (CS-PNO-2026 Art. 1.2 & 2.1)
        if vehicle_power >= 10:
            evidence.append(AgentEvidence(key="vehicle_power", value=vehicle_power, source_ref="Carte Grise"))
            high_power_search = policy_vector_store.search("véhicule puissant chevaux fiscaux supérieur 10 CV", top_k=1)
            for hp in high_power_search:
                sources.append(CitationRef(
                    citation_id=hp["citation_id"],
                    doc_id=hp["doc_id"],
                    doc_title=hp["doc_title"],
                    page=hp["page"],
                    article=hp["article"],
                    snippet=hp["content_snippet"],
                    relevance_score=hp["relevance_score"]
                ))

            if licence_years < 3:
                alerts.append(AgentAlert(
                    code="POL_SPORT_NOVICE_EXCLUSION",
                    severity="CRITICAL",
                    message=(
                        f"Véhicule puissant ({vehicle_power} CV) avec conducteur novice ({licence_years} ans de permis). "
                        "Non conforme aux critères d'acceptation de la Convention Spéciale CS-PNO-2026 Art. 1.2."
                    ),
                    action_required="Examen obligatoire par le comité de souscription senior ou proposition d'un véhicule de moindre puissance."
                ))
            else:
                findings.append(f"Véhicule de forte puissance ({vehicle_power} CV), souscripteur éligible sous réserve d'approbation standard.")

        # 3. Check Commercial / VTC Usage Exclusion (CG-AUTO-2026 Art. 4.1)
        if usage == "Taxi_VTC":
            vtc_search = policy_vector_store.search("transport onéreux personnes taxi VTC exclusion avenant", top_k=1)
            for vtc in vtc_search:
                sources.append(CitationRef(
                    citation_id=vtc["citation_id"],
                    doc_id=vtc["doc_id"],
                    doc_title=vtc["doc_title"],
                    page=vtc["page"],
                    article=vtc["article"],
                    snippet=vtc["content_snippet"],
                    relevance_score=vtc["relevance_score"]
                ))
            alerts.append(AgentAlert(
                code="POL_USAGE_VTC_EXCLUSION",
                severity="CRITICAL",
                message="Usage déclaré 'Taxi_VTC' formellement exclu du contrat standard (CG-AUTO-2026 Art. 4.1).",
                action_required="Souscription obligatoire de l'Avenant Spécifique Professionnel VTC avec tarification dédiée."
            ))

        # Status and confidence
        if any(a.severity == "CRITICAL" for a in alerts):
            status = "ESCALATED"
            confidence = 0.85
        elif any(a.severity == "WARNING" for a in alerts):
            status = "WARNING"
            confidence = 0.90
        else:
            status = "SUCCESS"
            confidence = 0.96
            findings.append("Dossier pleinement conforme aux conditions générales et particulières applicables.")

        return AgentOutputContract(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            version=self.version,
            status=status,
            confidence_score=confidence,
            findings=findings,
            evidence=evidence,
            sources=sources,
            missing_fields=missing_fields,
            alerts=alerts
        )
