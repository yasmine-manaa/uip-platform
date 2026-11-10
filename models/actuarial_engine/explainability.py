"""
Module d'explicabilité actuarielle
Fournit des explications sur les prédictions basées sur les coefficients des modèles.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import pickle
from pathlib import Path

# Chemin vers les métadonnées
MODELS_DIR = Path(__file__).parent.parent
FREQ_METADATA_PATH = MODELS_DIR / "frequency_model" / "artifacts" / "model_metadata.pkl"
SEV_METADATA_PATH = MODELS_DIR / "severity_model" / "artifacts" / "model_metadata.pkl"


def get_top_risk_factors(
    contract_data: Dict[str, Any],
    model_type: str = 'frequency',
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Identifie les facteurs de risque les plus importants pour un contrat.

    Args:
        contract_data: Caractéristiques du contrat
        model_type: Type de modèle ('frequency' ou 'severity')
        top_n: Nombre de facteurs à retourner

    Returns:
        Liste des facteurs de risque les plus importants
    """
    # Charger les métadonnées
    if model_type == 'frequency':
        with open(FREQ_METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)
    else:
        with open(SEV_METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)

    # Extraire les coefficients
    coefficients = pd.DataFrame(metadata['coefficients'])
    coefficients.index.name = 'Variable'

    # Mapper les données du contrat aux variables du modèle
    feature_contributions = []

    # Variables numériques
    numeric_features = metadata['numeric_features']
    for feature in numeric_features:
        if feature in contract_data:
            value = contract_data[feature]
            if feature in coefficients.index:
                coeff = coefficients.loc[feature, 'Coefficient']
                contribution = value * coeff
                feature_contributions.append({
                    'variable': feature,
                    'value': value,
                    'coefficient': float(coeff),
                    'contribution': float(contribution),
                    'exp_coeff': float(np.exp(coeff)) if coeff > 0 else float(np.exp(coeff))
                })

    # Variables catégorielles
    categorical_features = metadata['categorical_features']
    for cat_feature in categorical_features:
        if cat_feature in contract_data:
            value = contract_data[cat_feature]
            # Les variables encodées sont au format {feature}_{category}
            encoded_name = f"{cat_feature}_{value}"
            if encoded_name in coefficients.index:
                coeff = coefficients.loc[encoded_name, 'Coefficient']
                contribution = coeff  # Pour les catégorielles, la contribution est le coefficient
                feature_contributions.append({
                    'variable': encoded_name,
                    'value': value,
                    'coefficient': float(coeff),
                    'contribution': float(contribution),
                    'exp_coeff': float(np.exp(coeff))
                })

    # Trier par contribution absolue
    feature_contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)

    return feature_contributions[:top_n]


def explain_prediction(
    contract_data: Dict[str, Any],
    prediction_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Génère une explication complète d'une prédiction.

    Args:
        contract_data: Caractéristiques du contrat
        prediction_result: Résultat de la prédiction

    Returns:
        Dictionnaire avec l'explication
    """
    explanations = {
        'contract_summary': {
            'driver_age': contract_data.get('DrivAge', 'N/A'),
            'vehicle_power': contract_data.get('VehPower', 'N/A'),
            'vehicle_age': contract_data.get('VehAge', 'N/A'),
            'bonus_malus': contract_data.get('BonusMalus', 'N/A'),
            'area': contract_data.get('Area', 'N/A'),
            'vehicle_brand': contract_data.get('VehBrand', 'N/A'),
            'vehicle_gas': contract_data.get('VehGas', 'N/A')
        },
        'frequency_explanation': {
            'predicted_frequency': prediction_result.get('frequency', {}).get('annual_frequency', 0),
            'top_frequency_factors': get_top_risk_factors(contract_data, 'frequency', 3)
        },
        'severity_explanation': {
            'predicted_severity': prediction_result.get('severity', {}).get('expected_severity', 0),
            'top_severity_factors': get_top_risk_factors(contract_data, 'severity', 3)
        },
        'premium_breakdown': {
            'pure_premium': prediction_result.get('pure_premium', 0),
            'annual_premium': prediction_result.get('annual_pure_premium', 0),
            'calculation': prediction_result.get('calculation', {})
        }
    }

    return explanations


def get_model_coefficients(model_type: str = 'frequency') -> pd.DataFrame:
    """
    Retourne les coefficients du modèle pour l'interprétation.

    Args:
        model_type: Type de modèle ('frequency' ou 'severity')

    Returns:
        DataFrame avec les coefficients
    """
    if model_type == 'frequency':
        with open(FREQ_METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)
    else:
        with open(SEV_METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)

    coefficients = pd.DataFrame(metadata['coefficients'])
    coefficients.index.name = 'Variable'

    # Ajouter des colonnes pour l'interprétation
    coefficients['abs_coefficient'] = coefficients['Coefficient'].abs()
    coefficients['significant'] = coefficients.get('p_value', pd.Series([1.0] * len(coefficients))) < 0.05

    return coefficients.sort_values('abs_coefficient', ascending=False)
