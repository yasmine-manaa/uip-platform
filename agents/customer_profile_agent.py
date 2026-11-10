"""
Agent 1 — Customer Profile Agent
Analyse les informations du conducteur, son historique et les caractéristiques du véhicule.
Valide la complétude et la cohérence des données du profil client.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re


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


class CustomerProfileAgent:
    """
    Agent d'analyse du profil client.
    Valide les informations du conducteur et du véhicule.
    """

    def __init__(self):
        self.agent_name = "customer_profile"
        self.version = "1.0.0"

        # Champs requis pour un profil complet
        self.required_fields = [
            "driver_age", "licence_years", "vehicle_power", "vehicle_age",
            "bonus_malus", "area", "vehicle_brand", "vehicle_gas", "density"
        ]

        # Plages valides pour les champs numériques
        self.valid_ranges = {
            "driver_age": (18, 100),
            "licence_years": (0, 60),
            "vehicle_power": (1, 20),
            "vehicle_age": (0, 30),
            "bonus_malus": (0.5, 3.0),
            "density": (1, 50000)
        }

        # Catégories valides
        self.valid_categories = {
            "area": ["A", "B", "C", "D", "E", "F"],
            "vehicle_gas": ["Regular", "Diesel"],
            "vehicle_brand": [f"B{i}" for i in range(1, 15)]
        }

    def execute(self, case_context: Dict[str, Any]) -> AgentResult:
        """
        Exécute l'analyse du profil client.

        Args:
            case_context: Contexte du dossier contenant les informations du client

        Returns:
            AgentResult avec les résultats de l'analyse
        """
        warnings = []
        evidence = []
        missing_fields = []
        validation_errors = []

        # Extraire les données du profil
        profile = case_context.get("applicant", {})
        vehicle = case_context.get("vehicle", {})

        # Fusionner les données et mapper les noms de champs
        profile_data = {
            "driver_age": profile.get("driver_age"),
            "licence_years": profile.get("licence_years"),
            "vehicle_power": vehicle.get("vehicle_power"),
            "vehicle_age": vehicle.get("vehicle_age"),
            "bonus_malus": profile.get("bonus_malus"),
            "area": case_context.get("area"),
            "vehicle_brand": vehicle.get("vehicle_brand"),
            "vehicle_gas": vehicle.get("vehicle_gas"),
            "density": profile.get("density") or case_context.get("area_density")
        }

        # 1. Vérification de la complétude
        for field in self.required_fields:
            if field not in profile_data or profile_data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            warnings.append(f"Champs manquants: {', '.join(missing_fields)}")

        # 2. Validation des plages numériques
        for field, (min_val, max_val) in self.valid_ranges.items():
            if field in profile_data and profile_data[field] is not None:
                value = profile_data[field]
                if not (min_val <= value <= max_val):
                    validation_errors.append(f"{field}={value} hors plage valide [{min_val}, {max_val}]")
                    warnings.append(f"Valeur invalide pour {field}: {value}")

        # 3. Validation des catégories
        for field, valid_values in self.valid_categories.items():
            if field in profile_data and profile_data[field] is not None:
                value = profile_data[field]
                if value not in valid_values:
                    validation_errors.append(f"{field}={value} non valide. Valeurs acceptées: {valid_values}")
                    warnings.append(f"Catégorie invalide pour {field}: {value}")

        # 4. Cohérence âge/permis
        driver_age = profile_data.get("driver_age")
        licence_years = profile_data.get("licence_years")

        if driver_age is not None and licence_years is not None:
            if licence_years > driver_age - 18:
                warnings.append(f"Incohérence: {licence_years} ans de permis pour {driver_age} ans")
                validation_errors.append("Âge au permis incohérent")

        # 5. Calcul du score de confiance
        confidence = self._calculate_confidence(profile_data, missing_fields, validation_errors)

        # 6. Détermination du statut
        if validation_errors:
            status = "WARNING"
        elif missing_fields:
            status = "DATA_INCOMPLETE"
        else:
            status = "SUCCESS"

        # 7. Collecte des preuves
        evidence.append({
            "type": "profile_validation",
            "fields_checked": len(self.required_fields),
            "fields_present": len(self.required_fields) - len(missing_fields),
            "validation_errors": len(validation_errors)
        })

        # Résultat
        result = {
            "profile_summary": {
                "driver_age": profile_data.get("driver_age"),
                "vehicle_power": profile_data.get("vehicle_power"),
                "vehicle_age": profile_data.get("vehicle_age"),
                "bonus_malus": profile_data.get("bonus_malus"),
                "area": profile_data.get("area"),
                "vehicle_brand": profile_data.get("vehicle_brand"),
                "vehicle_gas": profile_data.get("vehicle_gas")
            },
            "missing_fields": missing_fields,
            "validation_errors": validation_errors,
            "data_quality_score": confidence
        }

        return AgentResult(
            agent_name=self.agent_name,
            status=status,
            result=result,
            confidence=confidence,
            warnings=warnings,
            evidence=evidence,
            requires_human_review=len(validation_errors) > 0
        )

    def _calculate_confidence(self, profile_data: Dict[str, Any], missing_fields: List[str],
                             validation_errors: List[str]) -> float:
        """
        Calcule le score de confiance basé sur la complétude et la validité des données.
        """
        # Score de base
        base_score = 1.0

        # Pénalité pour les champs manquants
        missing_penalty = len(missing_fields) * 0.1

        # Pénalité pour les erreurs de validation
        error_penalty = len(validation_errors) * 0.2

        # Pénalité pour les valeurs aux limites
        boundary_penalty = 0.0
        for field, (min_val, max_val) in self.valid_ranges.items():
            if field in profile_data and profile_data[field] is not None:
                value = profile_data[field]
                # Vérifier si la valeur est proche des limites
                range_size = max_val - min_val
                if value < min_val + range_size * 0.1 or value > max_val - range_size * 0.1:
                    boundary_penalty += 0.05

        confidence = max(0.0, base_score - missing_penalty - error_penalty - boundary_penalty)
        return round(confidence, 2)


# Instance globale de l'agent
customer_profile_agent = CustomerProfileAgent()
