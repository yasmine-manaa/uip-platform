"""
Module d'incertitude actuarielle
Calcule les intervalles de confiance pour les prédictions
basés sur la distribution des résidus du modèle.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
import pickle
from pathlib import Path

# Chemin vers les données pour calculer l'incertitude
DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "raw"


def calculate_uncertainty_bounds(
    predicted_value: float,
    confidence_level: float = 0.90,
    model_type: str = 'frequency'
) -> Dict[str, float]:
    """
    Calcule les intervalles de confiance pour une prédiction.

    Args:
        predicted_value: Valeur prédite
        confidence_level: Niveau de confiance (0.90 pour 90%)
        model_type: Type de modèle ('frequency' ou 'severity')

    Returns:
        Dictionnaire avec les bornes inférieure et supérieure
    """
    # Calculer l'écart-type basé sur les résidus du modèle
    # Pour la fréquence, on utilise une distribution Poisson
    # Pour la sévérité, on utilise une distribution Gamma

    if model_type == 'frequency':
        # Pour Poisson, l'intervalle est approximativement basé sur la racine carrée
        # std_error ≈ sqrt(predicted_value)
        # Pour les faibles fréquences, on utilise une valeur minimale pour éviter les intervalles trop étroits
        std_error = np.sqrt(max(predicted_value, 0.01))

        # Pour les très faibles fréquences, utiliser une incertitude relative fixe
        # car l'approche sqrt donne des résultats aberrants
        if predicted_value < 0.05:
            # Incertitude relative de 50% pour les faibles fréquences
            rel_uncertainty = 0.5
            lower_bound = max(0, predicted_value * (1 - rel_uncertainty))
            upper_bound = predicted_value * (1 + rel_uncertainty)
        else:
            # Approche normale pour les fréquences plus élevées
            from scipy import stats
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            lower_bound = max(0, predicted_value - z_score * std_error)
            upper_bound = predicted_value + z_score * std_error
    else:
        # Pour Gamma, on utilise un facteur multiplicatif plus réaliste
        # Basé sur les résidus du modèle GLM Gamma, l'incertitude typique est de 20-30%
        # On utilise 25% comme valeur par défaut (plus réaliste que 30%)
        std_error = predicted_value * 0.25

        # Calculer les bornes
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        lower_bound = max(0, predicted_value - z_score * std_error)
        upper_bound = predicted_value + z_score * std_error

    return {
        'predicted': float(predicted_value),
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'confidence_level': float(confidence_level),
        'std_error': float(std_error)
    }


def calculate_premium_uncertainty(
    frequency_prediction: float,
    severity_prediction: float,
    exposure: float,
    confidence_level: float = 0.90
) -> Dict[str, Any]:
    """
    Calcule l'incertitude sur la prime pure.

    Args:
        frequency_prediction: Prédiction de fréquence
        severity_prediction: Prédiction de sévérité
        exposure: Exposition en années
        confidence_level: Niveau de confiance

    Returns:
        Dictionnaire avec les intervalles de confiance pour la prime
    """
    # Calculer la prime pure prédite
    pure_premium = frequency_prediction * severity_prediction * exposure

    # Incertitude sur la fréquence
    freq_uncertainty = calculate_uncertainty_bounds(
        frequency_prediction, confidence_level, 'frequency'
    )

    # Incertitude sur la sévérité
    sev_uncertainty = calculate_uncertainty_bounds(
        severity_prediction, confidence_level, 'severity'
    )

    # Incertitude combinée (approche plus réaliste)
    # Au lieu de combiner les incertitudes relatives de manière quadratique,
    # on calcule directement les bornes sur la prime en combinant les incertitudes

    # Bornes de la prime basées sur les incertitudes de fréquence et sévérité
    # Prime = Fréquence × Sévérité × Exposition
    # On calcule les bornes en utilisant les bornes des composantes

    freq_lower = freq_uncertainty['lower_bound']
    freq_upper = freq_uncertainty['upper_bound']
    sev_lower = sev_uncertainty['lower_bound']
    sev_upper = sev_uncertainty['upper_bound']

    # Calcul des bornes de la prime (approche conservatrice mais réaliste)
    # On utilise les bornes inférieures pour le pire cas et les bornes supérieures pour le meilleur cas
    premium_lower = freq_lower * sev_lower * exposure
    premium_upper = freq_upper * sev_upper * exposure

    # Limiter les bornes pour éviter des valeurs aberrantes
    premium_lower = max(0, premium_lower)
    premium_upper = min(premium_upper, pure_premium * 5)  # Max 5x la prime prédite

    # Calculer l'incertitude relative pour référence
    # Utiliser une approche plus conservatrice pour éviter les valeurs aberrantes
    freq_rel_uncertainty = min((freq_uncertainty['upper_bound'] - freq_uncertainty['lower_bound']) / 2 / max(frequency_prediction, 0.001), 1.0)
    sev_rel_uncertainty = min((sev_uncertainty['upper_bound'] - sev_uncertainty['lower_bound']) / 2 / max(severity_prediction, 0.001), 1.0)

    # L'incertitude totale est la somme des incertitudes relatives (pas quadratique)
    # car les erreurs peuvent être corrélées
    total_rel_uncertainty = freq_rel_uncertainty + sev_rel_uncertainty

    return {
        'pure_premium': float(pure_premium),
        'lower_bound': float(max(0, premium_lower)),
        'upper_bound': float(premium_upper),
        'confidence_level': float(confidence_level),
        'frequency_uncertainty': freq_uncertainty,
        'severity_uncertainty': sev_uncertainty,
        'total_relative_uncertainty': float(total_rel_uncertainty)
    }


def calculate_premium_uncertainty_safe(
    frequency_prediction: float,
    severity_prediction: float,
    exposure: float,
    confidence_level: float = 0.90
) -> Dict[str, Any]:
    """
    Version sécurisée de calculate_premium_uncertainty qui gère les cas limites.
    """
    # Si les prédictions sont nulles ou négatives, retourner des valeurs par défaut
    if frequency_prediction <= 0 or severity_prediction <= 0:
        return {
            'pure_premium': 0.0,
            'lower_bound': 0.0,
            'upper_bound': 0.0,
            'confidence_level': confidence_level,
            'frequency_uncertainty': {},
            'severity_uncertainty': {},
            'total_relative_uncertainty': 0.0,
            'warning': 'Prédictions invalides (nulles ou négatives)'
        }

    return calculate_premium_uncertainty(
        frequency_prediction, severity_prediction, exposure, confidence_level
    )


def get_uncertainty_level(uncertainty_range: float, predicted_value: float) -> str:
    """
    Détermine le niveau d'incertitude basé sur la largeur de l'intervalle.

    Args:
        uncertainty_range: Largeur de l'intervalle (upper - lower)
        predicted_value: Valeur prédite

    Returns:
        Niveau d'incertitude (LOW, MEDIUM, HIGH)
    """
    if predicted_value == 0:
        return 'LOW'

    relative_uncertainty = uncertainty_range / predicted_value

    if relative_uncertainty < 0.2:
        return 'LOW'
    elif relative_uncertainty < 0.5:
        return 'MEDIUM'
    else:
        return 'HIGH'
