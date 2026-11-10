"""
Orchestration LangGraph pour l'UIP
Coordonne l'exécution des agents et gère le flux de travail.
"""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Importer les agents
from agents.customer_profile_agent import customer_profile_agent
from agents.document_intelligence_agent import document_intelligence_agent
from agents.risk_assessment_agent import risk_assessment_agent
from agents.claims_analysis_agent import claims_analysis_agent
from agents.governance_validation_agent import governance_validation_agent


class AgentState(TypedDict):
    """État partagé entre les agents"""
    case_id: str
    case_context: Dict[str, Any]
    agent_results: Dict[str, Any]
    current_agent: str
    status: str
    final_decision: Optional[Dict[str, Any]]
    error: Optional[str]


def create_orchestration_graph() -> StateGraph:
    """
    Crée le graphe d'orchestration LangGraph.

    Returns:
        StateGraph configuré avec les agents
    """
    # Créer le graphe
    workflow = StateGraph(AgentState)

    # Ajouter les nœuds pour chaque agent
    workflow.add_node("customer_profile", customer_profile_node)
    workflow.add_node("document_intelligence", document_intelligence_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("claims_analysis", claims_analysis_node)
    workflow.add_node("governance_validation", governance_validation_node)
    workflow.add_node("final_decision", final_decision_node)

    # Définir le point d'entrée
    workflow.set_entry_point("customer_profile")

    # Définir les transitions
    workflow.add_edge("customer_profile", "document_intelligence")
    workflow.add_edge("document_intelligence", "risk_assessment")
    workflow.add_edge("risk_assessment", "claims_analysis")
    workflow.add_edge("claims_analysis", "governance_validation")
    workflow.add_edge("governance_validation", "final_decision")
    workflow.add_edge("final_decision", END)

    return workflow


def customer_profile_node(state: AgentState) -> AgentState:
    """
    Nœud pour l'agent Customer Profile.

    Args:
        state: État actuel du graphe

    Returns:
        État mis à jour avec les résultats de l'agent
    """
    try:
        # Exécuter l'agent
        result = customer_profile_agent.execute(state["case_context"])

        # Mettre à jour l'état
        state["agent_results"]["customer_profile"] = result.to_dict()
        state["current_agent"] = "customer_profile"
        state["status"] = result.status

        # Si erreur critique, arrêter le workflow
        if result.status == "ERROR":
            state["status"] = "ERROR"
            state["error"] = f"Customer Profile Agent: {result.warnings}"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur Customer Profile Agent: {str(e)}"

    return state


def document_intelligence_node(state: AgentState) -> AgentState:
    """
    Nœud pour l'agent Document Intelligence.

    Args:
        state: État actuel du graphe

    Returns:
        État mis à jour avec les résultats de l'agent
    """
    # Vérifier si on peut continuer
    if state["status"] == "ERROR":
        return state

    try:
        # Exécuter l'agent
        result = document_intelligence_agent.execute(state["case_context"])

        # Mettre à jour l'état
        state["agent_results"]["document_intelligence"] = result.to_dict()
        state["current_agent"] = "document_intelligence"
        state["status"] = result.status

        # Si erreur critique, arrêter le workflow
        if result.status == "ERROR":
            state["status"] = "ERROR"
            state["error"] = f"Document Intelligence Agent: {result.warnings}"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur Document Intelligence Agent: {str(e)}"

    return state


def risk_assessment_node(state: AgentState) -> AgentState:
    """
    Nœud pour l'agent Risk Assessment.

    Args:
        state: État actuel du graphe

    Returns:
        État mis à jour avec les résultats de l'agent
    """
    # Vérifier si on peut continuer
    if state["status"] == "ERROR":
        return state

    try:
        # Préparer le contexte avec les résultats précédents
        context_with_results = {
            **state["case_context"],
            "agent_results": state["agent_results"]
        }

        # Exécuter l'agent
        result = risk_assessment_agent.execute(context_with_results)

        # Mettre à jour l'état
        state["agent_results"]["risk_assessment"] = result.to_dict()
        state["current_agent"] = "risk_assessment"
        state["status"] = result.status

        # Si erreur critique, arrêter le workflow
        if result.status == "ERROR":
            state["status"] = "ERROR"
            state["error"] = f"Risk Assessment Agent: {result.warnings}"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur Risk Assessment Agent: {str(e)}"

    return state


def claims_analysis_node(state: AgentState) -> AgentState:
    """
    Nœud pour l'agent Claims Analysis.

    Args:
        state: État actuel du graphe

    Returns:
        État mis à jour avec les résultats de l'agent
    """
    # Vérifier si on peut continuer
    if state["status"] == "ERROR":
        return state

    try:
        # Préparer le contexte avec les résultats précédents
        context_with_results = {
            **state["case_context"],
            "agent_results": state["agent_results"]
        }

        # Exécuter l'agent
        result = claims_analysis_agent.execute(context_with_results)

        # Mettre à jour l'état
        state["agent_results"]["claims_analysis"] = result.to_dict()
        state["current_agent"] = "claims_analysis"
        state["status"] = result.status

        # Si erreur critique, arrêter le workflow
        if result.status == "ERROR":
            state["status"] = "ERROR"
            state["error"] = f"Claims Analysis Agent: {result.warnings}"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur Claims Analysis Agent: {str(e)}"

    return state


def governance_validation_node(state: AgentState) -> AgentState:
    """
    Nœud pour l'agent Governance & Validation.

    Args:
        state: État actuel du graphe

    Returns:
        État mis à jour avec les résultats de l'agent
    """
    # Vérifier si on peut continuer
    if state["status"] == "ERROR":
        return state

    try:
        # Préparer le contexte avec tous les résultats des agents
        context_with_results = {
            **state["case_context"],
            "agent_results": state["agent_results"]
        }

        # Exécuter l'agent
        result = governance_validation_agent.execute(context_with_results)

        # Mettre à jour l'état
        state["agent_results"]["governance_validation"] = result.to_dict()
        state["current_agent"] = "governance_validation"
        state["status"] = result.status

        # Si erreur critique, arrêter le workflow
        if result.status == "ERROR":
            state["status"] = "ERROR"
            state["error"] = f"Governance Validation Agent: {result.warnings}"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur Governance Validation Agent: {str(e)}"

    return state


def final_decision_node(state: AgentState) -> AgentState:
    """
    Nœud final pour la décision.

    Args:
        state: État actuel du graphe

    Returns:
        État final avec la décision
    """
    try:
        # Agréger tous les résultats
        all_results = state["agent_results"]

        # Déterminer la décision finale
        decision = {
            "case_id": state["case_id"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": state["status"],
            "agents_executed": list(all_results.keys()),
            "summary": {
                "total_agents": len(all_results),
                "successful_agents": len([r for r in all_results.values() if r.get("status") == "SUCCESS"]),
                "warning_agents": len([r for r in all_results.values() if r.get("status") == "WARNING"]),
                "error_agents": len([r for r in all_results.values() if r.get("status") == "ERROR"]),
                "requires_human_review": any(r.get("requires_human_review", False) for r in all_results.values())
            },
            "key_findings": _extract_key_findings(all_results),
            "recommendations": _generate_final_recommendations(all_results),
            "risk_assessment": all_results.get("risk_assessment", {}).get("result", {}),
            "governance_validation": all_results.get("governance_validation", {}).get("result", {})
        }

        # Ajouter des métadonnées
        decision["metadata"] = {
            "execution_time": datetime.utcnow().isoformat() + "Z",
            "agents_version": "1.0.0",
            "orchestration_version": "1.0.0"
        }

        state["final_decision"] = decision
        state["status"] = "COMPLETED"

    except Exception as e:
        state["status"] = "ERROR"
        state["error"] = f"Erreur dans la décision finale: {str(e)}"

    return state


def _extract_key_findings(agent_results: Dict[str, Any]) -> List[str]:
    """Extrait les principales conclusions des agents"""
    findings = []

    # Customer Profile
    profile = agent_results.get("customer_profile", {}).get("result", {})
    if profile.get("data_quality_score", 0) < 0.7:
        findings.append("Qualité des données du profil insuffisante")

    # Document Intelligence
    docs = agent_results.get("document_intelligence", {}).get("result", {})
    if docs.get("inconsistencies"):
        findings.append(f"{len(docs.get('inconsistencies', []))} incohérences documentaires détectées")

    # Risk Assessment
    risk = agent_results.get("risk_assessment", {}).get("result", {})
    if risk.get("risk_tier") in ["HIGH", "CRITICAL"]:
        findings.append(f"Risque {risk.get('risk_tier', 'UNKNOWN')} détecté")

    # Claims Analysis
    claims = agent_results.get("claims_analysis", {}).get("result", {})
    if claims.get("claims_summary", {}).get("total_claims", 0) > 0:
        findings.append(f"{claims.get('claims_summary', {}).get('total_claims', 0)} sinistres dans l'historique")

    # Governance
    governance = agent_results.get("governance_validation", {}).get("result", {})
    if governance.get("requires_human_review"):
        findings.append("Validation humaine requise")

    return findings


def _generate_final_recommendations(agent_results: Dict[str, Any]) -> List[str]:
    """Génère les recommandations finales"""
    recommendations = []

    # Recommandations basées sur la gouvernance
    governance = agent_results.get("governance_validation", {}).get("result", {})
    if governance.get("recommendations"):
        recommendations.extend(governance.get("recommendations", []))

    # Recommandations spécifiques
    risk = agent_results.get("risk_assessment", {}).get("result", {})
    if risk.get("risk_tier") == "CRITICAL":
        recommendations.append("Refuser la souscription - risque critique")
    elif risk.get("risk_tier") == "HIGH":
        recommendations.append("Conditions spéciales requises - prime majorée")

    # Recommandations pour les documents
    docs = agent_results.get("document_intelligence", {}).get("result", {})
    if docs.get("missing_fields"):
        recommendations.append("Compléter les documents manquants")

    # Recommandations pour les sinistres
    claims = agent_results.get("claims_analysis", {}).get("result", {})
    if claims.get("anomalies"):
        recommendations.append("Investiguer les anomalies de sinistres")

    return recommendations


class UIPOrchestrator:
    """
    Orchestrateur principal pour l'UIP.
    Gère l'exécution du workflow LangGraph.
    """

    def __init__(self):
        self.graph = create_orchestration_graph()
        self.compiled_graph = self.graph.compile()

    def process_case(self, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un dossier client à travers tous les agents.

        Args:
            case_context: Contexte du dossier client

        Returns:
            Résultat final de l'orchestration
        """
        # Initialiser l'état
        initial_state = {
            "case_id": case_context.get("case_id", f"CASE_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
            "case_context": case_context,
            "agent_results": {},
            "current_agent": "init",
            "status": "PENDING",
            "final_decision": None,
            "error": None
        }

        # Exécuter le graphe
        try:
            final_state = self.compiled_graph.invoke(initial_state)

            # Retourner le résultat final
            return {
                "success": final_state.get("status") == "COMPLETED",
                "case_id": final_state.get("case_id"),
                "status": final_state.get("status"),
                "final_decision": final_state.get("final_decision"),
                "agent_results": final_state.get("agent_results"),
                "error": final_state.get("error"),
                "execution_time": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            return {
                "success": False,
                "case_id": initial_state["case_id"],
                "status": "ERROR",
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat() + "Z"
            }

    def get_agent_status(self, case_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un dossier.

        Args:
            case_id: ID du dossier

        Returns:
            Statut du dossier
        """
        # Pour l'instant, retourne un statut basique
        # Dans une implémentation complète, cela interrogerait une base de données
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "message": "Fonctionnalité à implémenter"
        }


# Instance globale de l'orchestrateur
uip_orchestrator = UIPOrchestrator()
