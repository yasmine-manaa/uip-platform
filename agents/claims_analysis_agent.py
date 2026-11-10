"""
Agent 4 — Claims Analysis Agent
Analyse les sinistres antérieurs, les coûts et les éventuelles anomalies.
Examine l'historique des sinistres pour identifier les patterns et les risques.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
from collections import defaultdict


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


class ClaimsAnalysisAgent:
    """
    Agent d'analyse des sinistres.
    Analyse l'historique des sinistres pour identifier les patterns et les anomalies.
    """

    def __init__(self):
        self.agent_name = "claims_analysis"
        self.version = "1.0.0"

        # Seuils pour l'analyse (basés sur les données freMTPL2)
        self.thresholds = {
            "high_frequency": 3,  # Plus de 3 sinistres = fréquence élevée (moyenne ~0.1/an)
            "high_severity": 8000,  # Sinistre > 8000 € = sévérité élevée (moyenne ~2200 €)
            "recent_claim_months": 12,  # Sinistre dans les 12 derniers mois
            "total_cost_threshold": 15000  # Coût total > 15000 € = risque
        }

        # Types de sinistres
        self.claim_types = [
            "collision", "theft", "fire", "natural_disaster",
            "glass_breakage", "vandalism", "other"
        ]

    def execute(self, case_context: Dict[str, Any]) -> AgentResult:
        """
        Exécute l'analyse des sinistres.

        Args:
            case_context: Contexte du dossier avec l'historique des sinistres

        Returns:
            AgentResult avec les résultats de l'analyse
        """
        warnings = []
        evidence = []

        # Extraire l'historique des sinistres
        claims_history = case_context.get("claims_history", [])
        claims_summary = case_context.get("claims_summary", {})

        # Si pas d'historique, utiliser le résumé
        if not claims_history and claims_summary:
            claims_history = self._create_claims_from_summary(claims_summary)

        # Analyser l'historique
        analysis = self._analyze_claims_history(claims_history)

        # Identifier les anomalies
        anomalies = self._identify_anomalies(claims_history, analysis)

        # Calculer les statistiques
        statistics = self._calculate_statistics(claims_history)

        # Déterminer le statut et la confiance
        status, confidence = self._determine_status_and_confidence(analysis, anomalies, statistics)

        # Générer les avertissements
        warnings.extend(self._generate_warnings(analysis, anomalies, statistics))

        # Collecter les preuves
        evidence.extend(self._collect_evidence(claims_history, analysis, anomalies))

        # Résultat
        result = {
            "claims_summary": {
                "total_claims": len(claims_history),
                "total_cost": statistics.get("total_cost", 0),
                "average_cost": statistics.get("average_cost", 0),
                "most_recent_claim": statistics.get("most_recent_claim"),
                "claim_frequency": statistics.get("claim_frequency", 0)
            },
            "analysis": analysis,
            "anomalies": anomalies,
            "statistics": statistics,
            "risk_indicators": self._identify_risk_indicators(analysis, anomalies)
        }

        return AgentResult(
            agent_name=self.agent_name,
            status=status,
            result=result,
            confidence=confidence,
            warnings=warnings,
            evidence=evidence,
            requires_human_review=self._requires_human_review(status, anomalies, analysis)
        )

    def _create_claims_from_summary(self, claims_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Crée un historique de sinistres à partir du résumé.
        """
        claims = []
        prior_claims_count = claims_summary.get("prior_claims_count", 0)
        bonus_malus = claims_summary.get("bonus_malus", 1.0)

        # Si bonus_malus > 1, il y a probablement eu des sinistres
        if prior_claims_count > 0:
            # Créer des sinistres génériques basés sur le nombre
            for i in range(prior_claims_count):
                claims.append({
                    "claim_id": f"SUMMARY_{i+1}",
                    "date": None,  # Date inconnue
                    "type": "unknown",
                    "amount": 0,  # Montant inconnu
                    "description": "Sinistre antérieur (résumé)"
                })

        return claims

    def _analyze_claims_history(self, claims_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse l'historique des sinistres.
        """
        if not claims_history:
            return {
                "has_claims": False,
                "frequency_level": "NONE",
                "severity_level": "NONE",
                "recency_level": "NONE",
                "pattern_analysis": "Aucun sinistre"
            }

        # Fréquence
        total_claims = len(claims_history)
        frequency_level = "HIGH" if total_claims >= self.thresholds["high_frequency"] else "MEDIUM" if total_claims > 0 else "NONE"

        # Sévérité
        total_cost = sum(claim.get("amount") or 0 for claim in claims_history)
        avg_cost = total_cost / total_claims if total_claims > 0 else 0
        severity_level = "HIGH" if avg_cost > self.thresholds["high_severity"] else "MEDIUM" if avg_cost > 0 else "NONE"

        # Récence
        most_recent = self._get_most_recent_claim(claims_history)
        recency_level = "RECENT" if most_recent and self._is_recent_claim(most_recent) else "OLD" if most_recent else "NONE"

        # Analyse des patterns
        pattern_analysis = self._analyze_patterns(claims_history)

        return {
            "has_claims": True,
            "frequency_level": frequency_level,
            "severity_level": severity_level,
            "recency_level": recency_level,
            "total_claims": total_claims,
            "total_cost": total_cost,
            "average_cost": avg_cost,
            "pattern_analysis": pattern_analysis
        }

    def _identify_anomalies(self, claims_history: List[Dict[str, Any]],
                           analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie les anomalies dans l'historique des sinistres.
        """
        anomalies = []

        if not claims_history:
            return anomalies

        # Anomalie : Fréquence élevée
        if analysis.get("frequency_level") == "HIGH":
            anomalies.append({
                "type": "high_frequency",
                "severity": "WARNING",
                "description": f"Fréquence élevée de sinistres ({analysis.get('total_claims', 0)} sinistres)",
                "recommendation": "Surveillance accrue recommandée"
            })

        # Anomalie : Sévérité élevée
        if analysis.get("severity_level") == "HIGH":
            anomalies.append({
                "type": "high_severity",
                "severity": "WARNING",
                "description": f"Sévérité moyenne élevée ({analysis.get('average_cost', 0):.0f} €)",
                "recommendation": "Vérification des conditions de garantie"
            })

        # Anomalie : Sinistre récent
        if analysis.get("recency_level") == "RECENT":
            anomalies.append({
                "type": "recent_claim",
                "severity": "INFO",
                "description": "Sinistre récent détecté",
                "recommendation": "Surveillance de la période de carence"
            })

        # Anomalie : Coût total élevé
        total_cost = analysis.get("total_cost", 0)
        if total_cost > self.thresholds["total_cost_threshold"]:
            anomalies.append({
                "type": "high_total_cost",
                "severity": "CRITICAL",
                "description": f"Coût total des sinistres élevé ({total_cost:.0f} €)",
                "recommendation": "Révision du profil de risque"
            })

        # Anomalie : Sinistres multiples du même type
        type_counts = defaultdict(int)
        for claim in claims_history:
            claim_type = claim.get("type", "unknown")
            type_counts[claim_type] += 1

        for claim_type, count in type_counts.items():
            if count >= 3:
                anomalies.append({
                    "type": "repeated_claim_type",
                    "severity": "WARNING",
                    "description": f"Sinistres multiples de type '{claim_type}' ({count} occurrences)",
                    "recommendation": "Analyse des causes récurrentes"
                })

        return anomalies

    def _calculate_statistics(self, claims_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les statistiques sur les sinistres.
        """
        if not claims_history:
            return {
                "total_claims": 0,
                "total_cost": 0,
                "average_cost": 0,
                "most_recent_claim": None,
                "claim_frequency": 0,
                "claims_by_type": {},
                "claims_by_year": {}
            }

        total_claims = len(claims_history)
        total_cost = sum(claim.get("amount") or 0 for claim in claims_history)
        average_cost = total_cost / total_claims if total_claims > 0 else 0

        # Sinistre le plus récent
        most_recent = self._get_most_recent_claim(claims_history)

        # Fréquence (sinistres par an)
        claim_frequency = self._calculate_claim_frequency(claims_history)

        # Sinistres par type
        claims_by_type = defaultdict(int)
        for claim in claims_history:
            claim_type = claim.get("type", "unknown")
            claims_by_type[claim_type] += 1

        # Sinistres par année
        claims_by_year = defaultdict(int)
        for claim in claims_history:
            claim_date = claim.get("date")
            if claim_date:
                try:
                    year = self._extract_year(claim_date)
                    claims_by_year[year] += 1
                except:
                    pass

        return {
            "total_claims": total_claims,
            "total_cost": total_cost,
            "average_cost": average_cost,
            "most_recent_claim": most_recent,
            "claim_frequency": claim_frequency,
            "claims_by_type": dict(claims_by_type),
            "claims_by_year": dict(claims_by_year)
        }

    def _analyze_patterns(self, claims_history: List[Dict[str, Any]]) -> str:
        """
        Analyse les patterns dans les sinistres.
        """
        if not claims_history:
            return "Aucun sinistre"

        # Analyser la distribution temporelle
        temporal_pattern = self._analyze_temporal_pattern(claims_history)

        # Analyser la distribution par type
        type_pattern = self._analyze_type_pattern(claims_history)

        return f"{temporal_pattern}. {type_pattern}"

    def _analyze_temporal_pattern(self, claims_history: List[Dict[str, Any]]) -> str:
        """Analyse le pattern temporel des sinistres"""
        # Compter les sinistres par année
        claims_by_year = defaultdict(int)
        for claim in claims_history:
            claim_date = claim.get("date")
            if claim_date:
                try:
                    year = self._extract_year(claim_date)
                    claims_by_year[year] += 1
                except:
                    pass

        if not claims_by_year:
            return "Distribution temporelle inconnue"

        # Identifier les années avec le plus de sinistres
        max_year = max(claims_by_year.items(), key=lambda x: x[1])
        return f"Pic de sinistres en {max_year[0]} ({max_year[1]} sinistres)"

    def _analyze_type_pattern(self, claims_history: List[Dict[str, Any]]) -> str:
        """Analyse le pattern par type de sinistre"""
        type_counts = defaultdict(int)
        for claim in claims_history:
            claim_type = claim.get("type", "unknown")
            type_counts[claim_type] += 1

        if not type_counts:
            return "Types de sinistres inconnus"

        # Identifier le type le plus fréquent
        most_common_type = max(type_counts.items(), key=lambda x: x[1])
        return f"Type le plus fréquent: {most_common_type[0]} ({most_common_type[1]} occurrences)"

    def _identify_risk_indicators(self, analysis: Dict[str, Any],
                                  anomalies: List[Dict[str, Any]]) -> List[str]:
        """
        Identifie les indicateurs de risque.
        """
        indicators = []

        # Indicateurs basés sur l'analyse
        if analysis.get("frequency_level") == "HIGH":
            indicators.append("Fréquence de sinistres élevée")

        if analysis.get("severity_level") == "HIGH":
            indicators.append("Sévérité des sinistres élevée")

        if analysis.get("recency_level") == "RECENT":
            indicators.append("Sinistre récent")

        # Indicateurs basés sur les anomalies
        for anomaly in anomalies:
            if anomaly.get("severity") in ["WARNING", "CRITICAL"]:
                indicators.append(anomaly.get("description", "Anomalie détectée"))

        return indicators

    def _determine_status_and_confidence(self, analysis: Dict[str, Any],
                                        anomalies: List[Dict[str, Any]],
                                        statistics: Dict[str, Any]) -> tuple:
        """
        Détermine le statut et la confiance de l'analyse.
        """
        # Facteurs pour déterminer le statut
        critical_anomalies = [a for a in anomalies if a.get("severity") == "CRITICAL"]
        warning_anomalies = [a for a in anomalies if a.get("severity") == "WARNING"]

        # Déterminer le statut
        if critical_anomalies:
            status = "CRITICAL"
        elif warning_anomalies:
            status = "WARNING"
        elif analysis.get("has_claims"):
            status = "SUCCESS"
        else:
            status = "NO_CLAIMS"

        # Calculer la confiance
        confidence = 0.9  # Base

        # Réduire la confiance si anomalies critiques
        if critical_anomalies:
            confidence -= 0.4
        elif warning_anomalies:
            confidence -= 0.2

        # Réduire la confiance si peu de données
        if statistics.get("total_claims", 0) < 3:
            confidence -= 0.1

        # Augmenter la confiance si historique complet
        if statistics.get("total_claims", 0) >= 5:
            confidence += 0.05

        confidence = max(0.0, min(1.0, confidence))

        return status, round(confidence, 2)

    def _generate_warnings(self, analysis: Dict[str, Any], anomalies: List[Dict[str, Any]],
                          statistics: Dict[str, Any]) -> List[str]:
        """Génère les avertissements basés sur l'analyse"""
        warnings = []

        # Avertissements sur les anomalies
        for anomaly in anomalies:
            if anomaly.get("severity") in ["WARNING", "CRITICAL"]:
                warnings.append(f"{anomaly.get('type', 'unknown')}: {anomaly.get('description', '')}")

        # Avertissement sur l'absence de sinistres
        if not analysis.get("has_claims"):
            warnings.append("Aucun sinistre dans l'historique")

        # Avertissement sur les données manquantes
        if statistics.get("total_claims", 0) > 0 and statistics.get("average_cost", 0) == 0:
            warnings.append("Montants des sinistres non disponibles")

        return warnings

    def _collect_evidence(self, claims_history: List[Dict[str, Any]],
                         analysis: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collecte les preuves pour l'audit"""
        evidence = []

        # Preuve de l'historique
        evidence.append({
            "type": "claims_history",
            "total_claims": len(claims_history),
            "total_cost": sum(claim.get("amount") or 0 for claim in claims_history),
            "period": self._get_claims_period(claims_history)
        })

        # Preuve de l'analyse
        evidence.append({
            "type": "claims_analysis",
            "frequency_level": analysis.get("frequency_level", "UNKNOWN"),
            "severity_level": analysis.get("severity_level", "UNKNOWN"),
            "recency_level": analysis.get("recency_level", "UNKNOWN")
        })

        # Preuve des anomalies
        if anomalies:
            evidence.append({
                "type": "anomalies",
                "count": len(anomalies),
                "critical": len([a for a in anomalies if a.get("severity") == "CRITICAL"]),
                "warnings": len([a for a in anomalies if a.get("severity") == "WARNING"])
            })

        return evidence

    def _get_most_recent_claim(self, claims_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Retourne le sinistre le plus récent"""
        dated_claims = [c for c in claims_history if c.get("date")]
        if not dated_claims:
            return None

        return max(dated_claims, key=lambda x: self._parse_date(x.get("date", "")))

    def _is_recent_claim(self, claim: Dict[str, Any]) -> bool:
        """Vérifie si un sinistre est récent (dans les 12 derniers mois)"""
        claim_date = claim.get("date")
        if not claim_date:
            return False

        try:
            claim_dt = self._parse_date(claim_date)
            now = datetime.now()
            months_diff = (now.year - claim_dt.year) * 12 + (now.month - claim_dt.month)
            return months_diff <= self.thresholds["recent_claim_months"]
        except:
            return False

    def _calculate_claim_frequency(self, claims_history: List[Dict[str, Any]]) -> float:
        """Calcule la fréquence des sinistres (par an)"""
        if not claims_history:
            return 0

        # Trouver la période couverte
        dates = [self._parse_date(c.get("date", "")) for c in claims_history if c.get("date")]
        if not dates:
            return 0

        min_date = min(dates)
        max_date = max(dates)

        # Calculer la durée en années
        years = (max_date - min_date).days / 365.25
        if years <= 0:
            years = 1  # Minimum 1 an

        return len(claims_history) / years

    def _get_claims_period(self, claims_history: List[Dict[str, Any]]) -> str:
        """Retourne la période couverte par les sinistres"""
        dates = [self._parse_date(c.get("date", "")) for c in claims_history if c.get("date")]
        if not dates:
            return "Période inconnue"

        min_date = min(dates)
        max_date = max(dates)

        return f"{min_date.strftime('%Y-%m-%d')} à {max_date.strftime('%Y-%m-%d')}"

    def _parse_date(self, date_str: str) -> datetime:
        """Parse une date dans différents formats"""
        if not date_str:
            return datetime.now()

        # Essayer différents formats
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        # Si aucun format ne fonctionne, retourner la date actuelle
        return datetime.now()

    def _extract_year(self, date_str: str) -> int:
        """Extrait l'année d'une date"""
        try:
            return self._parse_date(date_str).year
        except:
            return datetime.now().year

    def _requires_human_review(self, status: str, anomalies: List[Dict[str, Any]],
                              analysis: Dict[str, Any]) -> bool:
        """Détermine si une révision humaine est requise"""
        # Révision requise si statut CRITICAL ou WARNING
        if status in ["CRITICAL", "WARNING"]:
            return True

        # Révision requise si anomalies critiques
        critical_anomalies = [a for a in anomalies if a.get("severity") == "CRITICAL"]
        if critical_anomalies:
            return True

        # Révision requise si fréquence élevée
        if analysis.get("frequency_level") == "HIGH":
            return True

        return False


# Instance globale de l'agent
claims_analysis_agent = ClaimsAnalysisAgent()
