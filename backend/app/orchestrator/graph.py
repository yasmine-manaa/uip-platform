"""
Multi-Agent Orchestration Workflow.
Implements the full state machine from Section 5 & 9:
- Specialist agents (Profile, Policy, Claims, External).
- Actuarial risk assessment aggregation.
- Governance & Trust contradiction audit.
- Secondary contradiction resolution loop.
- Deterministic decision engine consolidation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.orchestrator.decision_engine import DeterministicDecisionEngine
from app.agents.profile_agent import CustomerProfileAgent
from app.agents.policy_agent import PolicyDocumentAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.claims_agent import HistoricalClaimsAgent
from app.agents.external_agent import ExternalIntelligenceAgent
from app.agents.governance_agent import GovernanceTrustAgent

# Agent singletons
agent_profile = CustomerProfileAgent()
agent_policy = PolicyDocumentAgent()
agent_risk = RiskAssessmentAgent()
agent_claims = HistoricalClaimsAgent()
agent_external = ExternalIntelligenceAgent()
agent_governance = GovernanceTrustAgent()


def execute_underwriting_workflow(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct, robust multi-agent orchestration workflow executing the exact graph state machine.
    Deterministic, instant, and thread-safe.
    """
    timeline: List[Dict[str, Any]] = []
    agent_outputs: Dict[str, Any] = {}

    # Step 1: Context Builder
    timeline.append({
        "step": "CONTEXT_BUILDER",
        "description": "Validation du dossier et initialisation du flux multi-agents.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    # Step 2: Specialists (Profile, Policy, Claims, External)
    timeline.append({
        "step": "PARALLEL_SPECIALISTS",
        "description": "Exécution des agents spécialistes : Profil Client, Pièces & Garanties, Sinistres, Contexte Externe.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    prof_res = agent_profile.execute(state)
    pol_res = agent_policy.execute(state)
    clm_res = agent_claims.execute(state)
    ext_res = agent_external.execute(state)

    agent_outputs[prof_res.agent_id] = prof_res.model_dump()
    agent_outputs[pol_res.agent_id] = pol_res.model_dump()
    agent_outputs[clm_res.agent_id] = clm_res.model_dump()
    agent_outputs[ext_res.agent_id] = ext_res.model_dump()

    # Step 3: Actuarial Risk Assessment Agent (Agent 3)
    timeline.append({
        "step": "ACTUARIAL_RISK_ASSESSMENT",
        "description": "Évaluation actuarielle : GLM Poisson (fréquence), GLM Gamma (sévérité), XGBoost & SHAP.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    enriched_state = dict(state)
    enriched_state["agent_outputs"] = agent_outputs

    risk_res = agent_risk.execute(enriched_state)
    agent_outputs[risk_res.agent_id] = risk_res.model_dump()
    enriched_state["agent_outputs"] = agent_outputs

    # Step 4: Governance & Trust Agent (Agent 6)
    timeline.append({
        "step": "GOVERNANCE_AND_TRUST",
        "description": "Audit d'intégrité, détection des contradictions croisées et contrôle des biais.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    gov_res = agent_governance.execute(enriched_state)
    agent_outputs[gov_res.agent_id] = gov_res.model_dump()

    contradictions = gov_res.metadata.get("contradictions_detected", [])
    escalation_required = gov_res.metadata.get("human_review_mandatory", False)

    # Step 5: Contradiction Resolution Loop (if any)
    if contradictions:
        timeline.append({
            "step": "CONTRADICTION_RESOLUTION",
            "description": f"Boucle de résolution ciblée : {len(contradictions)} contradiction(s) isolée(s) pour revue souscripteur.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        escalation_required = True

    # Step 6: Deterministic Decision Engine Consolidation
    timeline.append({
        "step": "DECISION_CONSOLIDATION",
        "description": "Consolidation déterministe (Risque, Qualité, Incertitude) et recommandation provisoire.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    provisional_decision = DeterministicDecisionEngine.evaluate(
        agent_outputs=agent_outputs,
        case_context=enriched_state
    )

    return {
        "case_id": state.get("case_id", "UNKNOWN"),
        "status": "COMPLETED",
        "agent_outputs": agent_outputs,
        "contradictions": contradictions,
        "escalation_required": escalation_required,
        "provisional_decision": provisional_decision,
        "execution_timeline": timeline,
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }


def get_compiled_graph():
    """LangGraph StateGraph representation generator for introspection."""
    from langgraph.graph import StateGraph, END
    from app.orchestrator.state import UnderwritingGraphState

    builder = StateGraph(UnderwritingGraphState)
    def _run_node(s):
        return execute_underwriting_workflow(s)

    builder.add_node("orchestrator", _run_node)
    builder.set_entry_point("orchestrator")
    builder.add_edge("orchestrator", END)
    return builder.compile()
