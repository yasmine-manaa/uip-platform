"""
Agent 5 — Governance & Validation Agent
Contrôle la qualité des données, les incohérences, les incertitudes et les cas nécessitant une validation humaine.
Assure la conformité et la traçabilité des décisions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json


class AgentResult:
    """Contrat commun pour tous les agents"""
    def __init__(self, agent_name: str, status: str, result: Dict[str, Any],
                 confidence: float = 0.0, warnings: List[str] = None,
                 evidence: List[Dict[str, Any]] = None, requires_human_review: bool = False):
        self.agent_name = agent_name
        self.status = status
        self.result = result
        self.confidence = confidence
        self.warnings = warnings or []
        self.evidence = evidence or []
        self.requires_human_review = requires_human_review
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "result": self.result,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "evidence": self.evidence,
            "requires_human_review": self.requires_human_review,
            "timestamp": self.timestamp
        }


class GovernanceValidationAgent:
    """
    Agent de gouvernance et validation.
    Contrôle la qualité des données, détecte les incohérences et détermine si une validation humaine est requise.
    """

    def __init__(self):
        self.agent_name = "governance_validation"
        self.version = "1.0.0"

        # Seuils pour la validation
        self.thresholds = {
            "min_confidence": 0.7,  # Confiance minimale requise
            "max_uncertainty": 0.5,  # Incertitude maximale tolérée
            "max_warnings": 3,  # Nombre maximum d'avertissements
            "critical_issues": 1  # Nombre maximum de problèmes critiques
        }

        # Types de validation
        self.validation_types = [
            "data_quality", "consistency", "completeness",
            "accuracy", "compliance", "traceability"
        ]

    def execute(self, case_context: Dict[str, Any]) -> AgentResult:
        """
        Exécute la validation et la gouvernance.

        Args:
            case_context: Contexte du dossier avec les résultats des autres agents

        Returns:
            AgentResult avec les résultats de la validation
        """
        warnings = []
        evidence = []

        # Extraire les résultats des autres agents
        agent_results = case_context.get("agent_results", {})

        # Effectuer les validations
        validations = self._perform_validations(agent_results, case_context)

        # Calculer le score de qualité global
        quality_score = self._calculate_quality_score(validations)

        # Déterminer si une validation humaine est requise
        requires_review = self._requires_human_review(validations, quality_score)

        # Générer les recommandations
        recommendations = self._generate_recommendations(validations, quality_score)

        # Collecter les preuves pour l'audit
        evidence.extend(self._collect_audit_evidence(case_context, validations))

        # Déterminer le statut
        status = self._determine_status(validations, quality_score, requires_review)

        # Calculer la confiance
        confidence = self._calculate_confidence(validations, quality_score)

        # Générer les avertissements
        warnings.extend(self._generate_warnings(validations, quality_score))

        # Résultat
        result = {
            "quality_score": quality_score,
            "validations": validations,
            "requires_human_review": requires_review,
            "recommendations": recommendations,
            "audit_trail": self._create_audit_trail(case_context),
            "compliance_status": self._check_compliance(case_context),
            "data_quality_metrics": self._calculate_data_quality_metrics(agent_results)
        }

        return AgentResult(
            agent_name=self.agent_name,
            status=status,
            result=result,
            confidence=confidence,
            warnings=warnings,
            evidence=evidence,
            requires_human_review=requires_review
        )

    def _perform_validations(self, agent_results: Dict[str, Any],
                            case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue toutes les validations sur les résultats des agents.
        """
        validations = {}

        # Validation 1: Qualité des données
        validations["data_quality"] = self._validate_data_quality(agent_results)

        # Validation 2: Cohérence
        validations["consistency"] = self._validate_consistency(agent_results, case_context)

        # Validation 3: Complétude
        validations["completeness"] = self._validate_completeness(agent_results)

        # Validation 4: Précision
        validations["accuracy"] = self._validate_accuracy(agent_results)

        # Validation 5: Conformité
        validations["compliance"] = self._validate_compliance(case_context)

        # Validation 6: Traçabilité
        validations["traceability"] = self._validate_traceability(agent_results)

        return validations

    def _validate_data_quality(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la qualité des données"""
        issues = []
        score = 1.0

        # Vérifier les résultats des agents
        for agent_name, result in agent_results.items():
            if result.get("status") == "ERROR":
                issues.append(f"Agent {agent_name} en erreur")
                score -= 0.3

            # Vérifier les avertissements
            warnings = result.get("warnings", [])
            if len(warnings) > self.thresholds["max_warnings"]:
                issues.append(f"Agent {agent_name}: trop d'avertissements ({len(warnings)})")
                score -= 0.1

            # Vérifier la confiance
            confidence = result.get("confidence", 0)
            if confidence < self.thresholds["min_confidence"]:
                issues.append(f"Agent {agent_name}: confiance faible ({confidence:.2f})")
                score -= 0.2

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": issues,
            "details": "Validation de la qualité des données des agents"
        }

    def _validate_consistency(self, agent_results: Dict[str, Any],
                             case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la cohérence des données"""
        issues = []
        inconsistencies = []

        # Vérifier la cohérence entre les agents
        profile_result = agent_results.get("customer_profile", {})
        risk_result = agent_results.get("risk_assessment", {})
        claims_result = agent_results.get("claims_analysis", {})

        # Cohérence profil/risque
        if profile_result.get("status") == "SUCCESS" and risk_result.get("status") == "SUCCESS":
            profile_data = profile_result.get("result", {}).get("profile_summary", {})
            risk_data = risk_result.get("result", {}).get("actuarial_calculation", {})

            # Vérifier que les données du profil sont cohérentes avec le risque
            driver_age = profile_data.get("driver_age")
            if driver_age and driver_age < 25:
                if risk_data.get("frequency", 0) < 0.05:
                    inconsistencies.append("Âge jeune mais fréquence de sinistres faible")

        # Cohérence documents/profil
        doc_result = agent_results.get("document_intelligence", {})
        if doc_result.get("status") == "WARNING":
            inconsistencies.extend(doc_result.get("result", {}).get("inconsistencies", []))

        # Cohérence sinistres/profil
        if claims_result.get("status") == "CRITICAL":
            inconsistencies.append("Historique de sinistres critique")

        score = 1.0 - (len(inconsistencies) * 0.2)

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": inconsistencies,
            "details": "Validation de la cohérence entre les agents"
        }

    def _validate_completeness(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la complétude des données"""
        missing_data = []
        incomplete_agents = []

        # Vérifier chaque agent
        for agent_name, result in agent_results.items():
            status = result.get("status", "UNKNOWN")
            if status in ["DATA_INCOMPLETE", "INCOMPLETE", "NO_DOCUMENTS", "NO_CLAIMS"]:
                incomplete_agents.append(agent_name)
                missing_data.append(f"{agent_name}: données incomplètes")

        score = 1.0 - (len(incomplete_agents) * 0.15)

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": missing_data,
            "details": "Validation de la complétude des données"
        }

    def _validate_accuracy(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la précision des prédictions"""
        issues = []
        score = 1.0

        # Vérifier le risque actuariel
        risk_result = agent_results.get("risk_assessment", {})
        if risk_result.get("status") == "SUCCESS":
            risk_data = risk_result.get("result", {})
            uncertainty = risk_data.get("uncertainty", {})

            # Vérifier l'incertitude
            if uncertainty.get("level") == "HIGH":
                issues.append("Incertitude élevée sur la prime pure")
                score -= 0.3

            # Vérifier la cohérence des prédictions
            actuarial = risk_data.get("actuarial_calculation", {})
            frequency = actuarial.get("frequency", 0)
            severity = actuarial.get("severity", 0)
            premium = actuarial.get("pure_premium", 0)

            # Vérifier que premium = frequency * severity * exposure
            expected_premium = frequency * severity * actuarial.get("exposure", 1.0)
            if abs(premium - expected_premium) > 0.01:
                issues.append("Incohérence dans le calcul de la prime pure")
                score -= 0.2

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": issues,
            "details": "Validation de la précision des prédictions"
        }

    def _validate_compliance(self, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la conformité aux réglementations"""
        issues = []
        score = 1.0

        # Vérifier les données sensibles (RGPD)
        applicant = case_context.get("applicant", {})
        sensitive_fields = ["religion", "ethnicity", "political_views", "health_data", "genetic_data"]

        for field in sensitive_fields:
            if field in applicant:
                issues.append(f"Donnée sensible détectée: {field}")
                score -= 0.5

        # Vérifier l'âge minimum
        driver_age = applicant.get("driver_age")
        if driver_age and driver_age < 18:
            issues.append("Conducteur mineur détecté")
            score -= 0.8

        # Vérifier la cohérence du permis
        licence_years = applicant.get("licence_years")
        if driver_age and licence_years and licence_years > driver_age - 18:
            issues.append("Incohérence âge/permis")
            score -= 0.3

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": issues,
            "details": "Validation de la conformité RGPD et réglementaire"
        }

    def _validate_traceability(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la traçabilité des décisions"""
        issues = []
        score = 1.0

        # Vérifier que chaque agent a des preuves
        for agent_name, result in agent_results.items():
            evidence = result.get("evidence", [])
            if not evidence:
                issues.append(f"Agent {agent_name}: pas de preuves d'audit")
                score -= 0.2

            # Vérifier le timestamp (mais ne pas pénaliser si absent car peut être ajouté par l'orchestrateur)
            timestamp = result.get("timestamp")
            if not timestamp:
                # Ne pas pénaliser fortement pour timestamp manquant car il peut être ajouté plus tard
                issues.append(f"Agent {agent_name}: timestamp manquant (ajouté par orchestrateur)")
                score -= 0.05  # Pénalité réduite

        return {
            "status": "PASS" if score >= 0.7 else "FAIL",
            "score": max(0.0, score),
            "issues": issues,
            "details": "Validation de la traçabilité et de l'audit"
        }

    def _calculate_quality_score(self, validations: Dict[str, Any]) -> float:
        """Calcule le score de qualité global"""
        scores = [v.get("score", 0) for v in validations.values()]
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def _requires_human_review(self, validations: Dict[str, Any],
                              quality_score: float) -> bool:
        """Détermine si une validation humaine est requise"""
        # Révision requise si score de qualité faible
        if quality_score < self.thresholds["min_confidence"]:
            return True

        # Révision requise si validations critiques échouent
        critical_validations = ["compliance", "consistency"]
        for val_name in critical_validations:
            if validations.get(val_name, {}).get("status") == "FAIL":
                return True

        # Révision requise si trop de problèmes
        total_issues = sum(len(v.get("issues", [])) for v in validations.values())
        if total_issues > 5:
            return True

        return False

    def _generate_recommendations(self, validations: Dict[str, Any],
                                 quality_score: float) -> List[str]:
        """Génère des recommandations basées sur les validations"""
        recommendations = []

        if quality_score < 0.5:
            recommendations.append("Revue complète du dossier recommandée")
        elif quality_score < 0.7:
            recommendations.append("Validation partielle recommandée")

        # Recommandations spécifiques par type de validation
        for val_name, val_result in validations.items():
            if val_result.get("status") == "FAIL":
                issues = val_result.get("issues", [])
                if issues:
                    recommendations.append(f"Corriger les problèmes de {val_name}: {', '.join(issues[:2])}")

        if not recommendations:
            recommendations.append("Dossier conforme - validation standard")

        return recommendations

    def _collect_audit_evidence(self, case_context: Dict[str, Any],
                               validations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collecte les preuves pour l'audit"""
        evidence = []

        # Preuve de la validation
        evidence.append({
            "type": "governance_validation",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validations_performed": len(validations),
            "quality_score": self._calculate_quality_score(validations)
        })

        # Preuve des validations critiques
        critical_validations = ["compliance", "consistency", "accuracy"]
        for val_name in critical_validations:
            if val_name in validations:
                evidence.append({
                    "type": f"validation_{val_name}",
                    "status": validations[val_name].get("status", "UNKNOWN"),
                    "score": validations[val_name].get("score", 0),
                    "issues": len(validations[val_name].get("issues", []))
                })

        return evidence

    def _create_audit_trail(self, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une piste d'audit pour le dossier"""
        audit_trail = {
            "case_id": case_context.get("case_id", "UNKNOWN"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agents_executed": list(case_context.get("agent_results", {}).keys()),
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "data_hash": self._calculate_data_hash(case_context)
        }

        return audit_trail

    def _check_compliance(self, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie la conformité globale"""
        compliance_issues = []

        # Vérifier les données sensibles
        applicant = case_context.get("applicant", {})
        sensitive_fields = ["religion", "ethnicity", "political_views", "health_data"]

        for field in sensitive_fields:
            if field in applicant:
                compliance_issues.append(f"Donnée sensible: {field}")

        # Vérifier l'âge
        driver_age = applicant.get("driver_age")
        if driver_age and driver_age < 18:
            compliance_issues.append("Conducteur mineur")

        return {
            "compliant": len(compliance_issues) == 0,
            "issues": compliance_issues,
            "regulations": ["RGPD", "Code des assurances", "Loi sur la protection des données"]
        }

    def _calculate_data_quality_metrics(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les métriques de qualité des données"""
        metrics = {
            "total_agents": len(agent_results),
            "successful_agents": len([r for r in agent_results.values() if r.get("status") == "SUCCESS"]),
            "warning_agents": len([r for r in agent_results.values() if r.get("status") == "WARNING"]),
            "error_agents": len([r for r in agent_results.values() if r.get("status") == "ERROR"]),
            "average_confidence": 0.0,
            "total_warnings": 0
        }

        # Calculer la confiance moyenne
        confidences = [r.get("confidence", 0) for r in agent_results.values()]
        if confidences:
            metrics["average_confidence"] = round(sum(confidences) / len(confidences), 2)

        # Calculer le total des avertissements
        metrics["total_warnings"] = sum(len(r.get("warnings", [])) for r in agent_results.values())

        return metrics

    def _calculate_data_hash(self, case_context: Dict[str, Any]) -> str:
        """Calcule un hash des données pour la traçabilité"""
        try:
            data_str = json.dumps(case_context, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
        except:
            return "UNKNOWN"

    def _determine_status(self, validations: Dict[str, Any], quality_score: float,
                         requires_review: bool) -> str:
        """Détermine le statut global"""
        if requires_review:
            return "REVIEW_REQUIRED"
        elif quality_score >= 0.8:
            return "APPROVED"
        elif quality_score >= 0.6:
            return "CONDITIONAL"
        else:
            return "REJECTED"

    def _calculate_confidence(self, validations: Dict[str, Any],
                             quality_score: float) -> float:
        """Calcule le score de confiance global"""
        # La confiance est basée sur le score de qualité et la cohérence des validations
        validation_scores = [v.get("score", 0) for v in validations.values()]
        avg_validation_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0

        # Combiner le score de qualité et la moyenne des validations
        # Donner plus de poids au score de qualité global
        confidence = (quality_score * 0.7) + (avg_validation_score * 0.3)

        return round(max(0.0, min(1.0, confidence)), 2)

    def _generate_warnings(self, validations: Dict[str, Any],
                          quality_score: float) -> List[str]:
        """Génère les avertissements globaux"""
        warnings = []

        if quality_score < 0.5:
            warnings.append("Score de qualité global faible")
        elif quality_score < 0.7:
            warnings.append("Score de qualité global modéré")

        # Avertissements par validation
        for val_name, val_result in validations.items():
            if val_result.get("status") == "FAIL":
                issues = val_result.get("issues", [])
                if issues:
                    warnings.append(f"{val_name}: {len(issues)} problème(s) détecté(s)")

        return warnings


# Instance globale de l'agent
governance_validation_agent = GovernanceValidationAgent()
