"""
Agent 3 — Risk Assessment Agent
Appelle le moteur actuariel pour obtenir la fréquence, la sévérité, la prime pure et les facteurs explicatifs.
Transforme les résultats du moteur en indicateurs de risque actionnables.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Ajouter le chemin vers les modèles
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.actuarial_engine.actuarial_engine import actuarial_engine
from models.actuarial_engine.uncertainty import calculate_premium_uncertainty_safe
from models.actuarial_engine.explainability import explain_prediction, get_top_risk_factors


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


class RiskAssessmentAgent:
    """
    Agent d'évaluation du risque.
    Utilise le moteur actuariel pour calculer la prime pure et analyser les facteurs de risque.
    """

    def __init__(self):
        self.agent_name = "risk_assessment"
        self.version = "1.0.0"

        # Seuils de risque basés sur la prime pure
        self.risk_thresholds = {
            "LOW": 0,
            "MEDIUM": 500,
            "HIGH": 1500,
            "CRITICAL": 3000
        }

        # Seuils pour l'incertitude (basés sur l'incertitude relative)
        # Ajustés pour être plus réalistes avec les prédictions actuarielles
        self.uncertainty_thresholds = {
            "LOW": 0.5,
            "MEDIUM": 1.2,
            "HIGH": 2.0
        }

    def execute(self, case_context: Dict[str, Any]) -> AgentResult:
        """
        Exécute l'évaluation du risque actuariel.

        Args:
            case_context: Contexte du dossier avec les informations du profil

        Returns:
            AgentResult avec les résultats de l'évaluation
        """
        warnings = []
        evidence = []

        # Extraire les données nécessaires pour le moteur actuariel
        applicant = case_context.get("applicant", {})
        vehicle = case_context.get("vehicle", {})

        # Préparer les données pour le moteur actuariel
        contract_data = self._prepare_contract_data(applicant, vehicle, case_context)
        exposure = self._calculate_exposure(case_context)

        # Appeler le moteur actuariel
        try:
            actuarial_result = actuarial_engine.calculate_pure_premium(contract_data, exposure)
        except Exception as e:
            return AgentResult(
                agent_name=self.agent_name,
                status="ERROR",
                result={"error": str(e)},
                confidence=0.0,
                warnings=[f"Erreur lors de l'appel au moteur actuariel: {e}"],
                evidence=evidence,
                requires_human_review=True
            )

        # Analyser les résultats
        analysis = self._analyze_actuarial_results(actuarial_result, contract_data, exposure)

        # Calculer l'incertitude
        uncertainty = self._calculate_uncertainty(actuarial_result, exposure)

        # Identifier les facteurs de risque
        risk_factors = self._identify_risk_factors(contract_data, actuarial_result)

        # Déterminer le statut et la confiance
        status, confidence = self._determine_status_and_confidence(analysis, uncertainty, risk_factors)

        # Collecter les avertissements
        warnings.extend(self._generate_warnings(analysis, uncertainty, risk_factors))

        # Collecter les preuves
        evidence.extend(self._collect_evidence(actuarial_result, analysis, uncertainty))

        # Résultat
        result = {
            "actuarial_calculation": {
                "pure_premium": actuarial_result.get("pure_premium", 0),
                "annual_premium": actuarial_result.get("annual_pure_premium", 0),
                "frequency": actuarial_result.get("frequency", {}).get("annual_frequency", 0),
                "severity": actuarial_result.get("severity", {}).get("expected_severity", 0),
                "exposure": exposure
            },
            "risk_analysis": analysis,
            "uncertainty": uncertainty,
            "risk_factors": risk_factors,
            "risk_tier": self._get_risk_tier(actuarial_result.get("pure_premium", 0)),
            "confidence_score": confidence
        }

        return AgentResult(
            agent_name=self.agent_name,
            status=status,
            result=result,
            confidence=confidence,
            warnings=warnings,
            evidence=evidence,
            requires_human_review=self._requires_human_review(status, uncertainty, risk_factors)
        )

    def _prepare_contract_data(self, applicant: Dict[str, Any], vehicle: Dict[str, Any],
                              case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare les données du contrat pour le moteur actuariel.
        """
        return {
            "VehPower": vehicle.get("vehicle_power", 6),
            "VehAge": vehicle.get("vehicle_age", 5),
            "DrivAge": applicant.get("driver_age", 35),
            "BonusMalus": applicant.get("bonus_malus", 0.85),
            "Density": case_context.get("area_density", 1000),
            "Area": case_context.get("area", "B"),
            "VehBrand": vehicle.get("vehicle_brand", "B6"),
            "VehGas": vehicle.get("vehicle_gas", "Regular")
        }

    def _calculate_exposure(self, case_context: Dict[str, Any]) -> float:
        """
        Calcule l'exposition en années.
        Par défaut, on utilise 1 an pour une nouvelle souscription.
        """
        # Pour l'instant, on utilise 1 an par défaut
        # Dans un système réel, cela viendrait de la durée de la police
        return 1.0

    def _analyze_actuarial_results(self, actuarial_result: Dict[str, Any],
                                  contract_data: Dict[str, Any], exposure: float) -> Dict[str, Any]:
        """
        Analyse les résultats du moteur actuariel.
        """
        pure_premium = actuarial_result.get("pure_premium", 0)
        frequency = actuarial_result.get("frequency", {}).get("annual_frequency", 0)
        severity = actuarial_result.get("severity", {}).get("expected_severity", 0)

        # Analyser la fréquence
        freq_analysis = self._analyze_frequency(frequency)

        # Analyser la sévérité
        sev_analysis = self._analyze_severity(severity)

        # Analyser la prime pure
        premium_analysis = self._analyze_premium(pure_premium)

        return {
            "frequency_analysis": freq_analysis,
            "severity_analysis": sev_analysis,
            "premium_analysis": premium_analysis,
            "overall_risk_level": self._get_overall_risk_level(freq_analysis, sev_analysis, premium_analysis)
        }

    def _analyze_frequency(self, frequency: float) -> Dict[str, Any]:
        """Analyse la fréquence des sinistres"""
        # Fréquence moyenne dans le dataset: ~0.10 sinistres/an
        avg_frequency = 0.10

        if frequency < avg_frequency * 0.5:
            level = "LOW"
            description = "Fréquence très faible"
        elif frequency < avg_frequency:
            level = "MEDIUM"
            description = "Fréquence inférieure à la moyenne"
        elif frequency < avg_frequency * 1.5:
            level = "MEDIUM"
            description = "Fréquence proche de la moyenne"
        else:
            level = "HIGH"
            description = "Fréquence élevée"

        return {
            "value": frequency,
            "level": level,
            "description": description,
            "relative_to_average": frequency / avg_frequency if avg_frequency > 0 else 0
        }

    def _analyze_severity(self, severity: float) -> Dict[str, Any]:
        """Analyse la sévérité des sinistres"""
        # Sévérité moyenne dans le dataset: ~2200 €
        avg_severity = 2200

        if severity < avg_severity * 0.5:
            level = "LOW"
            description = "Sévérité très faible"
        elif severity < avg_severity:
            level = "MEDIUM"
            description = "Sévérité inférieure à la moyenne"
        elif severity < avg_severity * 1.5:
            level = "MEDIUM"
            description = "Sévérité proche de la moyenne"
        else:
            level = "HIGH"
            description = "Sévérité élevée"

        return {
            "value": severity,
            "level": level,
            "description": description,
            "relative_to_average": severity / avg_severity if avg_severity > 0 else 0
        }

    def _analyze_premium(self, premium: float) -> Dict[str, Any]:
        """Analyse la prime pure"""
        tier = self._get_risk_tier(premium)

        return {
            "value": premium,
            "tier": tier,
            "description": self._get_risk_description(tier)
        }

    def _calculate_uncertainty(self, actuarial_result: Dict[str, Any], exposure: float) -> Dict[str, Any]:
        """
        Calcule l'incertitude sur la prime pure.
        """
        frequency = actuarial_result.get("frequency", {}).get("annual_frequency", 0)
        severity = actuarial_result.get("severity", {}).get("expected_severity", 0)

        uncertainty = calculate_premium_uncertainty_safe(
            frequency, severity, exposure, confidence_level=0.90
        )

        # Ajouter le niveau d'incertitude
        uncertainty["level"] = self._get_uncertainty_level(uncertainty)

        return uncertainty

    def _identify_risk_factors(self, contract_data: Dict[str, Any],
                              actuarial_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie les principaux facteurs de risque.
        """
        factors = []

        # Facteurs du profil
        driver_age = contract_data.get("DrivAge", 35)
        bonus_malus = contract_data.get("BonusMalus", 0.85)
        vehicle_power = contract_data.get("VehPower", 6)
        vehicle_age = contract_data.get("VehAge", 5)
        area = contract_data.get("Area", "B")
        density = contract_data.get("Density", 1000)

        # Analyser chaque facteur
        if driver_age < 25:
            factors.append({
                "factor": "driver_age",
                "value": driver_age,
                "impact": "HIGH",
                "description": "Conducteur jeune - risque élevé"
            })
        elif driver_age > 70:
            factors.append({
                "factor": "driver_age",
                "value": driver_age,
                "impact": "MEDIUM",
                "description": "Conducteur senior - risque modéré"
            })

        if bonus_malus > 1.5:
            factors.append({
                "factor": "bonus_malus",
                "value": bonus_malus,
                "impact": "HIGH",
                "description": "Bonus-Malus élevé - historique de sinistres"
            })

        if vehicle_power > 10:
            factors.append({
                "factor": "vehicle_power",
                "value": vehicle_power,
                "impact": "MEDIUM",
                "description": "Véhicule puissant - risque accru"
            })

        if vehicle_age > 10:
            factors.append({
                "factor": "vehicle_age",
                "value": vehicle_age,
                "impact": "MEDIUM",
                "description": "Véhicule ancien - risque mécanique"
            })

        if area in ["A", "B"]:
            factors.append({
                "factor": "area",
                "value": area,
                "impact": "MEDIUM",
                "description": "Zone urbaine dense - risque accru"
            })

        if density > 5000:
            factors.append({
                "factor": "density",
                "value": density,
                "impact": "MEDIUM",
                "description": "Haute densité - risque accru"
            })

        return factors

    def _determine_status_and_confidence(self, analysis: Dict[str, Any],
                                        uncertainty: Dict[str, Any],
                                        risk_factors: List[Dict[str, Any]]) -> tuple:
        """
        Détermine le statut et la confiance de l'analyse.
        """
        # Facteurs pour déterminer le statut
        high_risk_factors = [f for f in risk_factors if f.get("impact") == "HIGH"]
        uncertainty_level = uncertainty.get("level", "MEDIUM")
        overall_risk = analysis.get("overall_risk_level", "MEDIUM")

        # Déterminer le statut
        if high_risk_factors or uncertainty_level == "HIGH" or overall_risk == "CRITICAL":
            status = "WARNING"
        elif overall_risk == "HIGH" or uncertainty_level == "MEDIUM":
            status = "CAUTION"
        else:
            status = "SUCCESS"

        # Calculer la confiance
        confidence = 0.9  # Base

        # Réduire la confiance si incertitude élevée
        if uncertainty_level == "HIGH":
            confidence -= 0.3
        elif uncertainty_level == "MEDIUM":
            confidence -= 0.1

        # Réduire la confiance si nombreux facteurs de risque
        if len(high_risk_factors) > 2:
            confidence -= 0.2
        elif len(risk_factors) > 3:
            confidence -= 0.1

        # Augmenter la confiance si risque faible
        if overall_risk == "LOW" and uncertainty_level == "LOW":
            confidence += 0.05

        confidence = max(0.0, min(1.0, confidence))

        return status, round(confidence, 2)

    def _generate_warnings(self, analysis: Dict[str, Any], uncertainty: Dict[str, Any],
                          risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Génère les avertissements basés sur l'analyse"""
        warnings = []

        # Avertissements sur le risque élevé
        if analysis.get("overall_risk_level") == "CRITICAL":
            warnings.append("Risque critique détecté - révision approfondie recommandée")
        elif analysis.get("overall_risk_level") == "HIGH":
            warnings.append("Risque élevé détecté - attention particulière requise")

        # Avertissements sur l'incertitude
        if uncertainty.get("level") == "HIGH":
            warnings.append("Incertitude élevée sur la prime - validation supplémentaire recommandée")

        # Avertissements sur les facteurs de risque
        high_risk_factors = [f for f in risk_factors if f.get("impact") == "HIGH"]
        if high_risk_factors:
            factor_names = [f["factor"] for f in high_risk_factors]
            warnings.append(f"Facteurs de risque élevé: {', '.join(factor_names)}")

        return warnings

    def _collect_evidence(self, actuarial_result: Dict[str, Any], analysis: Dict[str, Any],
                         uncertainty: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collecte les preuves pour l'audit"""
        evidence = []

        # Preuve de la prime pure
        evidence.append({
            "type": "actuarial_calculation",
            "pure_premium": actuarial_result.get("pure_premium", 0),
            "frequency": actuarial_result.get("frequency", {}).get("annual_frequency", 0),
            "severity": actuarial_result.get("severity", {}).get("expected_severity", 0)
        })

        # Preuve de l'incertitude
        evidence.append({
            "type": "uncertainty",
            "confidence_level": uncertainty.get("confidence_level", 0.90),
            "lower_bound": uncertainty.get("lower_bound", 0),
            "upper_bound": uncertainty.get("upper_bound", 0)
        })

        # Preuve du niveau de risque
        evidence.append({
            "type": "risk_level",
            "overall_risk": analysis.get("overall_risk_level", "UNKNOWN"),
            "premium_tier": analysis.get("premium_analysis", {}).get("tier", "UNKNOWN")
        })

        return evidence

    def _get_risk_tier(self, premium: float) -> str:
        """Détermine le tier de risque basé sur la prime pure"""
        if premium < self.risk_thresholds["MEDIUM"]:
            return "LOW"
        elif premium < self.risk_thresholds["HIGH"]:
            return "MEDIUM"
        elif premium < self.risk_thresholds["CRITICAL"]:
            return "HIGH"
        else:
            return "CRITICAL"

    def _get_risk_description(self, tier: str) -> str:
        """Retourne la description du tier de risque"""
        descriptions = {
            "LOW": "Risque faible",
            "MEDIUM": "Risque moyen",
            "HIGH": "Risque élevé",
            "CRITICAL": "Risque critique"
        }
        return descriptions.get(tier, "Inconnu")

    def _get_overall_risk_level(self, freq_analysis: Dict[str, Any],
                               sev_analysis: Dict[str, Any],
                               premium_analysis: Dict[str, Any]) -> str:
        """Détermine le niveau de risque global"""
        # Prendre le maximum des niveaux
        levels = [freq_analysis.get("level", "MEDIUM"),
                  sev_analysis.get("level", "MEDIUM"),
                  premium_analysis.get("tier", "MEDIUM")]

        if "CRITICAL" in levels:
            return "CRITICAL"
        elif "HIGH" in levels:
            return "HIGH"
        elif "MEDIUM" in levels:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_uncertainty_level(self, uncertainty: Dict[str, Any]) -> str:
        """Détermine le niveau d'incertitude"""
        # Utiliser l'incertitude relative calculée
        relative_uncertainty = uncertainty.get("total_relative_uncertainty", 0)

        # Seuils basés sur les valeurs réalistes pour les prédictions actuarielles
        if relative_uncertainty < self.uncertainty_thresholds["LOW"]:
            return "LOW"
        elif relative_uncertainty < self.uncertainty_thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "HIGH"

    def _requires_human_review(self, status: str, uncertainty: Dict[str, Any],
                              risk_factors: List[Dict[str, Any]]) -> bool:
        """Détermine si une révision humaine est requise"""
        # Révision requise si statut WARNING ou incertitude HIGH
        if status == "WARNING":
            return True

        if uncertainty.get("level") == "HIGH":
            return True

        # Révision requise si nombreux facteurs de risque élevé
        high_risk_factors = [f for f in risk_factors if f.get("impact") == "HIGH"]
        if len(high_risk_factors) > 2:
            return True

        return False


# Instance globale de l'agent
risk_assessment_agent = RiskAssessmentAgent()
