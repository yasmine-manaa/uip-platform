"""
Verification globale de l'UIP - Tous les composants
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Ajouter le chemin racine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("VERIFICATION GLOBALE DE L'UIP")
print("=" * 80)
print(f"Date: {datetime.now().isoformat()}")
print("=" * 80)

results = {
    "models": {},
    "agents": {},
    "orchestration": {},
    "rag": {},
    "overall_status": "UNKNOWN"
}

# ============================================================================
# 1. VERIFICATION DES MODELES ACTUARIAUX
# ============================================================================
print("\n[1] VERIFICATION DES MODELES ACTUARIAUX")
print("-" * 80)

try:
    # Tester le moteur actuariel
    from models.actuarial_engine.actuarial_engine import actuarial_engine

    # Test de prediction
    contract_data = {
        "VehPower": 6,
        "VehAge": 5,
        "DrivAge": 35,
        "BonusMalus": 50,
        "Density": 1000,
        "Area": "B",
        "VehBrand": "B6",
        "VehGas": "Regular"
    }

    result = actuarial_engine.calculate_pure_premium(contract_data, 1.0)

    if result and "pure_premium" in result:
        results["models"]["actuarial_engine"] = {
            "status": "SUCCESS",
            "pure_premium": result["pure_premium"],
            "frequency": result.get("frequency", {}).get("annual_frequency", 0),
            "severity": result.get("severity", {}).get("expected_severity", 0)
        }
        print(f"  [OK] Moteur actuariel: Prime pure = {result['pure_premium']:.2f} EUR")
    else:
        results["models"]["actuarial_engine"] = {"status": "ERROR", "error": "Prediction failed"}
        print("  [FAIL] Moteur actuariel: Prediction failed")

except Exception as e:
    results["models"]["actuarial_engine"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Moteur actuariel: {str(e)}")

# ============================================================================
# 2. VERIFICATION DES AGENTS
# ============================================================================
print("\n[2] VERIFICATION DES AGENTS")
print("-" * 80)

# Test Customer Profile Agent
try:
    from agents.customer_profile_agent import customer_profile_agent

    test_context = {
        "applicant": {
            "full_name": "Test User",
            "driver_age": 35,
            "licence_years": 10,
            "bonus_malus": 0.85,
            "density": 1000
        },
        "vehicle": {
            "vehicle_power": 6,
            "vehicle_age": 5,
            "vehicle_brand": "B6",
            "vehicle_gas": "Regular"
        },
        "area": "B"
    }

    result = customer_profile_agent.execute(test_context)
    results["agents"]["customer_profile"] = {
        "status": result.status,
        "confidence": result.confidence,
        "requires_review": result.requires_human_review
    }
    print(f"  [OK] Customer Profile: {result.status} (confiance {result.confidence})")

except Exception as e:
    results["agents"]["customer_profile"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Customer Profile: {str(e)}")

# Test Document Intelligence Agent
try:
    from agents.document_intelligence_agent import document_intelligence_agent

    test_context = {
        "applicant": {"full_name": "Test User", "driver_age": 35},
        "documents": [
            {
                "type": "policy",
                "content": "POL123456 - Nom: Test User - Couverture: 01/01/2024 - 31/12/2024",
                "metadata": {}
            }
        ]
    }

    result = document_intelligence_agent.execute(test_context)
    results["agents"]["document_intelligence"] = {
        "status": result.status,
        "confidence": result.confidence,
        "requires_review": result.requires_human_review
    }
    print(f"  [OK] Document Intelligence: {result.status} (confiance {result.confidence})")

except Exception as e:
    results["agents"]["document_intelligence"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Document Intelligence: {str(e)}")

# Test Risk Assessment Agent
try:
    from agents.risk_assessment_agent import risk_assessment_agent

    test_context = {
        "applicant": {
            "full_name": "Test User",
            "driver_age": 35,
            "licence_years": 10,
            "bonus_malus": 0.85,
            "density": 1000
        },
        "vehicle": {
            "vehicle_power": 6,
            "vehicle_age": 5,
            "vehicle_brand": "B6",
            "vehicle_gas": "Regular"
        },
        "area": "B",
        "area_density": 1000,
        "postal_code": "75001"
    }

    result = risk_assessment_agent.execute(test_context)
    results["agents"]["risk_assessment"] = {
        "status": result.status,
        "confidence": result.confidence,
        "requires_review": result.requires_human_review,
        "premium": result.result.get("actuarial_calculation", {}).get("pure_premium", 0)
    }
    print(f"  [OK] Risk Assessment: {result.status} (prime {result.result.get('actuarial_calculation', {}).get('pure_premium', 0):.2f} EUR)")

except Exception as e:
    results["agents"]["risk_assessment"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Risk Assessment: {str(e)}")

# Test Claims Analysis Agent
try:
    from agents.claims_analysis_agent import claims_analysis_agent

    test_context = {
        "applicant": {"full_name": "Test User", "driver_age": 35, "bonus_malus": 0.85},
        "claims_history": [
            {
                "claim_id": "CLM001",
                "date": "2023-05-15",
                "type": "collision",
                "amount": 2500,
                "description": "Accident mineur"
            }
        ],
        "claims_summary": {"prior_claims_count": 1, "bonus_malus": 0.85}
    }

    result = claims_analysis_agent.execute(test_context)
    results["agents"]["claims_analysis"] = {
        "status": result.status,
        "confidence": result.confidence,
        "requires_review": result.requires_human_review
    }
    print(f"  [OK] Claims Analysis: {result.status} (confiance {result.confidence})")

except Exception as e:
    results["agents"]["claims_analysis"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Claims Analysis: {str(e)}")

# Test Governance Validation Agent
try:
    from agents.governance_validation_agent import governance_validation_agent

    test_context = {
        "case_id": "TEST_001",
        "applicant": {"full_name": "Test User", "driver_age": 35},
        "agent_results": {
            "customer_profile": {
                "status": "SUCCESS",
                "confidence": 0.9,
                "warnings": [],
                "evidence": [{"type": "profile_validation"}],
                "result": {"profile_summary": {"driver_age": 35}}
            },
            "document_intelligence": {
                "status": "SUCCESS",
                "confidence": 0.9,
                "warnings": [],
                "evidence": [{"type": "document_extraction"}],
                "result": {"documents_processed": 1}
            },
            "risk_assessment": {
                "status": "SUCCESS",
                "confidence": 0.8,
                "warnings": [],
                "evidence": [{"type": "actuarial_calculation"}],
                "result": {
                    "actuarial_calculation": {"pure_premium": 150.0},
                    "uncertainty": {"level": "LOW"}
                }
            },
            "claims_analysis": {
                "status": "SUCCESS",
                "confidence": 0.8,
                "warnings": [],
                "evidence": [{"type": "claims_analysis"}],
                "result": {"claims_summary": {"total_claims": 1}}
            }
        }
    }

    result = governance_validation_agent.execute(test_context)
    results["agents"]["governance_validation"] = {
        "status": result.status,
        "confidence": result.confidence,
        "requires_review": result.requires_human_review,
        "quality_score": result.result.get("quality_score", 0)
    }
    print(f"  [OK] Governance Validation: {result.status} (qualite {result.result.get('quality_score', 0)})")

except Exception as e:
    results["agents"]["governance_validation"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Governance Validation: {str(e)}")

# ============================================================================
# 3. VERIFICATION DE L'ORCHESTRATION
# ============================================================================
print("\n[3] VERIFICATION DE L'ORCHESTRATION LANGGRAPH")
print("-" * 80)

try:
    from orchestration.langgraph_orchestrator import uip_orchestrator

    # Test d'orchestration complet
    test_case = {
        "case_id": "TEST_CASE_001",
        "applicant": {
            "full_name": "Jean Test",
            "driver_age": 40,
            "licence_years": 15,
            "bonus_malus": 0.8,
            "density": 800
        },
        "vehicle": {
            "vehicle_power": 5,
            "vehicle_age": 3,
            "vehicle_brand": "B4",
            "vehicle_gas": "Regular"
        },
        "area": "C",
        "area_density": 800,
        "postal_code": "75001",
        "documents": [
            {
                "type": "policy",
                "content": "POL999888 - Nom: Jean Test - Couverture: 01/01/2024 - 31/12/2024",
                "metadata": {}
            }
        ],
        "claims_history": [],
        "claims_summary": {"prior_claims_count": 0, "bonus_malus": 0.8}
    }

    result = uip_orchestrator.process_case(test_case)

    if result["success"]:
        results["orchestration"]["langgraph"] = {
            "status": "SUCCESS",
            "case_id": result["case_id"],
            "agents_executed": result.get("final_decision", {}).get("agents_executed", []),
            "requires_review": result.get("final_decision", {}).get("summary", {}).get("requires_human_review", False)
        }
        print(f"  [OK] Orchestration: {len(results['orchestration']['langgraph']['agents_executed'])} agents executes")
        print(f"     Revision humaine: {results['orchestration']['langgraph']['requires_review']}")
    else:
        results["orchestration"]["langgraph"] = {"status": "ERROR", "error": result.get("error", "Unknown")}
        print(f"  [FAIL] Orchestration: {result.get('error', 'Unknown')}")

except Exception as e:
    results["orchestration"]["langgraph"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] Orchestration: {str(e)}")

# ============================================================================
# 4. VERIFICATION DU SYSTEME RAG
# ============================================================================
print("\n[4] VERIFICATION DU SYSTEME RAG")
print("-" * 80)

try:
    from rag.rag_system import rag_system

    # Test de statistiques
    stats = rag_system.get_statistics()

    # Test de recherche
    search_results = rag_system.knowledge_base.search("police assurance", top_k=3)

    results["rag"]["system"] = {
        "status": "SUCCESS",
        "total_documents": stats["knowledge_base"]["total_documents"],
        "vector_store_size": stats["knowledge_base"]["vector_store_size"],
        "search_results": len(search_results),
        "pymupdf_available": stats["document_processor"]["pymupdf_available"],
        "ocr_available": stats["document_processor"]["ocr_available"],
        "sklearn_available": stats["document_processor"]["sklearn_available"]
    }

    print(f"  [OK] RAG System: {stats['knowledge_base']['total_documents']} documents indexes")
    print(f"     Vector store: {stats['knowledge_base']['vector_store_size']} vecteurs")
    print(f"     Recherche: {len(search_results)} resultats trouves")

except Exception as e:
    results["rag"]["system"] = {"status": "ERROR", "error": str(e)}
    print(f"  [FAIL] RAG System: {str(e)}")

# ============================================================================
# 5. VERIFICATION GLOBALE
# ============================================================================
print("\n[5] VERIFICATION GLOBALE")
print("-" * 80)

# Calculer le score global
scores = []

# Modeles
for model, result in results["models"].items():
    if result.get("status") == "SUCCESS":
        scores.append(1.0)
        print(f"  [OK] {model}: OK")
    else:
        scores.append(0.0)
        print(f"  [FAIL] {model}: {result.get('error', 'Unknown')}")

# Agents
for agent, result in results["agents"].items():
    if result.get("status") in ["SUCCESS", "WARNING", "CAUTION", "APPROVED", "REVIEW_REQUIRED", "NO_CLAIMS"]:
        scores.append(0.8)  # Les agents peuvent avoir des warnings
        print(f"  [OK] {agent}: {result.get('status', 'OK')}")
    else:
        scores.append(0.0)
        print(f"  [FAIL] {agent}: {result.get('error', 'Unknown')}")

# Orchestration
for orch, result in results["orchestration"].items():
    if result.get("status") == "SUCCESS":
        scores.append(1.0)
        print(f"  [OK] {orch}: OK")
    else:
        scores.append(0.0)
        print(f"  [FAIL] {orch}: {result.get('error', 'Unknown')}")

# RAG
for rag, result in results["rag"].items():
    if result.get("status") == "SUCCESS":
        scores.append(1.0)
        print(f"  [OK] {rag}: OK")
    else:
        scores.append(0.0)
        print(f"  [FAIL] {rag}: {result.get('error', 'Unknown')}")

# Calculer le score global
global_score = sum(scores) / len(scores) if scores else 0

if global_score >= 0.9:
    results["overall_status"] = "EXCELLENT"
    status_emoji = "[SUCCESS]"
elif global_score >= 0.8:
    results["overall_status"] = "GOOD"
    status_emoji = "[OK]"
elif global_score >= 0.7:
    results["overall_status"] = "ACCEPTABLE"
    status_emoji = "[WARN]"
else:
    results["overall_status"] = "NEEDS_IMPROVEMENT"
    status_emoji = "[FAIL]"

print(f"\n{status_emoji} SCORE GLOBAL: {global_score:.2f} ({results['overall_status']})")

# ============================================================================
# 6. RECOMMANDATIONS
# ============================================================================
print("\n[6] RECOMMANDATIONS")
print("-" * 80)

recommendations = []

if results["models"].get("actuarial_engine", {}).get("status") != "SUCCESS":
    recommendations.append("Verifier le moteur actuariel")

if len([a for a in results["agents"].values() if a.get("status") == "ERROR"]) > 0:
    recommendations.append("Corriger les agents en erreur")

if results["orchestration"].get("langgraph", {}).get("status") != "SUCCESS":
    recommendations.append("Verifier l'orchestration LangGraph")

if results["rag"].get("system", {}).get("status") != "SUCCESS":
    recommendations.append("Verifier le systeme RAG")

if results["rag"].get("system", {}).get("total_documents", 0) == 0:
    recommendations.append("Ajouter des documents a la base de connaissances")

if not recommendations:
    recommendations.append("Tous les composants fonctionnent correctement")
    recommendations.append("Pret pour le developpement frontend")

for rec in recommendations:
    print(f"  - {rec}")

# ============================================================================
# 7. SAUVEGARDE DES RESULTATS
# ============================================================================
print("\n[7] SAUVEGARDE DES RESULTATS")
print("-" * 80)

# Sauvegarder les resultats
results_file = Path("verification_results.json")
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(f"  [OK] Resultats sauvegardes dans: {results_file}")

# ============================================================================
# RESUME FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RESUME FINAL")
print("=" * 80)

print(f"\n{status_emoji} STATUT GLOBAL: {results['overall_status']}")
print(f"Score: {global_score:.2f}/1.00")

print("\n[COMPOSANTS TESTES]")
print(f"  - Modeles actuariels: {len(results['models'])} composants")
print(f"  - Agents: {len(results['agents'])} agents")
print(f"  - Orchestration: {len(results['orchestration'])} systemes")
print(f"  - RAG: {len(results['rag'])} composants")

print("\n[FICHIERS CREES]")
print("  - verification_results.json")
print("  - agents/ (5 agents)")
print("  - orchestration/ (LangGraph)")
print("  - rag/ (systeme RAG)")
print("  - models/actuarial_engine/ (moteur)")

if results["overall_status"] in ["EXCELLENT", "GOOD"]:
    print("\n[SUCCESS] L'UIP est pret pour la prochaine etape !")
    print("   Prochaine etape: Developpement du frontend")
else:
    print("\n[WARN] Des ameliorations sont necessaires avant de continuer")
    print("   Consultez les recommandations ci-dessus")

print("=" * 80)
