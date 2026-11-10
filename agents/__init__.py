"""
Agents indépendants pour l'UIP
Contient les agents spécialisés pour l'analyse des dossiers d'assurance.
"""

# Importer les agents indépendants
try:
    from .customer_profile_agent import customer_profile_agent, AgentResult
    from .document_intelligence_agent import document_intelligence_agent
    from .risk_assessment_agent import risk_assessment_agent
    from .claims_analysis_agent import claims_analysis_agent
    from .governance_validation_agent import governance_validation_agent
    __all__ = [
        "customer_profile_agent",
        "document_intelligence_agent",
        "risk_assessment_agent",
        "claims_analysis_agent",
        "governance_validation_agent",
        "AgentResult"
    ]
except ImportError:
    __all__ = []

# Importer le système RAG
try:
    from rag.rag_system import rag_system
    __all__.append("rag_system")
except ImportError:
    pass
