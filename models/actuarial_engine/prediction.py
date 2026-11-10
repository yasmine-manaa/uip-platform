"""
Module de prédiction actuarielle
Contient les fonctions pour effectuer des prédictions sur plusieurs contrats
et générer des résultats structurés.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .actuarial_engine import actuarial_engine


def predict_batch_contracts(contracts_data: List[Dict[str, Any]], exposure: float = 1.0) -> List[Dict[str, Any]]:
    """
    Prédit la prime pure pour plusieurs contrats.

    Args:
        contracts_data: Liste de dictionnaires contenant les caractéristiques des contrats
        exposure: Exposition en années (par défaut 1.0)

    Returns:
        Liste de dictionnaires avec les résultats actuariels pour chaque contrat
    """
    results = []

    for i, contract_data in enumerate(contracts_data):
        try:
            result = actuarial_engine.calculate_pure_premium(contract_data, exposure)
            result['contract_index'] = i
            result['contract_data'] = contract_data
            results.append(result)
        except Exception as e:
            results.append({
                'contract_index': i,
                'contract_data': contract_data,
                'error': str(e)
            })

    return results


def predict_single_contract(contract_data: Dict[str, Any], exposure: float = 1.0) -> Dict[str, Any]:
    """
    Prédit la prime pure pour un seul contrat.

    Args:
        contract_data: Dictionnaire contenant les caractéristiques du contrat
        exposure: Exposition en années (par défaut 1.0)

    Returns:
        Dictionnaire avec les résultats actuariels
    """
    return actuarial_engine.calculate_pure_premium(contract_data, exposure)


def get_risk_tier(pure_premium: float) -> str:
    """
    Détermine le tier de risque basé sur la prime pure.

    Args:
        pure_premium: Prime pure calculée

    Returns:
        Tier de risque (LOW, MEDIUM, HIGH, CRITICAL)
    """
    # Seuils basés sur la distribution des primes
    if pure_premium < 500:
        return 'LOW'
    elif pure_premium < 1500:
        return 'MEDIUM'
    elif pure_premium < 3000:
        return 'HIGH'
    else:
        return 'CRITICAL'


def get_risk_description(tier: str) -> str:
    """
    Retourne une description du tier de risque.

    Args:
        tier: Tier de risque

    Returns:
        Description du tier
    """
    descriptions = {
        'LOW': 'Risque faible - Profil favorable',
        'MEDIUM': 'Risque moyen - Profil standard',
        'HIGH': 'Risque élevé - Profil à risque',
        'CRITICAL': 'Risque critique - Profil très à risque'
    }
    return descriptions.get(tier, 'Inconnu')
