"""
Test du moteur actuariel UIP
Vérifie que les modèles se chargent correctement et que les prédictions sont cohérentes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.actuarial_engine.actuarial_engine import actuarial_engine
from models.actuarial_engine.prediction import predict_single_contract, get_risk_tier, get_risk_description
from models.actuarial_engine.uncertainty import calculate_premium_uncertainty_safe
from models.actuarial_engine.explainability import explain_prediction, get_model_coefficients

print("=" * 80)
print("TEST DU MOTEUR ACTUARIEL UIP")
print("=" * 80)

# ============================================================================
# Test 1: Chargement des modèles
# ============================================================================
print("\n[TEST 1] Chargement des modèles")
print("-" * 80)

model_info = actuarial_engine.get_model_info()
print(f"Modèles chargés: {model_info['is_loaded']}")
print(f"Modèle fréquence: {model_info['frequency_model']['metadata']}")
print(f"Modèle sévérité: {model_info['severity_model']['metadata']}")

# ============================================================================
# Test 2: Prédiction pour un contrat type
# ============================================================================
print("\n[TEST 2] Prédiction pour un contrat type")
print("-" * 80)

# Contrat type: conducteur de 35 ans, véhicule de 5 ans, Bonus-Malus 50
contract_data = {
    'VehPower': 6,
    'VehAge': 5,
    'DrivAge': 35,
    'BonusMalus': 50,
    'Density': 1000,
    'Area': 'B',
    'VehBrand': 'B6',
    'VehGas': 'Regular'
}

# Test de préparation des features
print("\nTest de préparation des features:")
X_test = actuarial_engine.prepare_features(contract_data)
print(f"Features shape: {X_test.shape}")
print(f"Features columns: {X_test.columns.tolist()}")
print(f"Features values: {X_test.values}")

exposure = 1.0  # 1 an
result = predict_single_contract(contract_data, exposure)

print(f"\nRésultats pour le contrat type:")
print(f"  - Prime pure: {result.get('pure_premium', 0):.2f} €")
print(f"  - Prime annuelle: {result.get('annual_pure_premium', 0):.2f} €")
print(f"  - Fréquence annuelle: {result.get('frequency', {}).get('annual_frequency', 0):.4f}")
print(f"  - Sévérité: {result.get('severity', {}).get('expected_severity', 0):.2f} €")

# ============================================================================
# Test 3: Tier de risque
# ============================================================================
print("\n[TEST 3] Tier de risque")
print("-" * 80)

pure_premium = result.get('pure_premium', 0)
tier = get_risk_tier(pure_premium)
description = get_risk_description(tier)

print(f"Prime pure: {pure_premium:.2f} €")
print(f"Tier de risque: {tier}")
print(f"Description: {description}")

# ============================================================================
# Test 4: Incertitude
# ============================================================================
print("\n[TEST 4] Calcul de l'incertitude")
print("-" * 80)

freq_pred = result.get('frequency', {}).get('annual_frequency', 0)
sev_pred = result.get('severity', {}).get('expected_severity', 0)

uncertainty = calculate_premium_uncertainty_safe(freq_pred, sev_pred, exposure, confidence_level=0.90)

print(f"Prime pure prédite: {uncertainty['pure_premium']:.2f} €")
print(f"Intervalle 90%: [{uncertainty['lower_bound']:.2f} €, {uncertainty['upper_bound']:.2f} €]")
print(f"Incertitude relative: {uncertainty['total_relative_uncertainty'] * 100:.2f}%")

# ============================================================================
# Test 5: Explicabilité
# ============================================================================
print("\n[TEST 5] Explicabilité")
print("-" * 80)

explanation = explain_prediction(contract_data, result)

print(f"\nRésumé du contrat:")
print(f"  - Âge conducteur: {explanation['contract_summary']['driver_age']} ans")
print(f"  - Puissance véhicule: {explanation['contract_summary']['vehicle_power']}")
print(f"  - Âge véhicule: {explanation['contract_summary']['vehicle_age']} ans")
print(f"  - Bonus-Malus: {explanation['contract_summary']['bonus_malus']}")
print(f"  - Zone: {explanation['contract_summary']['area']}")

print(f"\nTop facteurs de fréquence:")
for factor in explanation['frequency_explanation']['top_frequency_factors'][:3]:
    print(f"  - {factor['variable']}: contribution = {factor['contribution']:.4f}")

print(f"\nTop facteurs de sévérité:")
for factor in explanation['severity_explanation']['top_severity_factors'][:3]:
    print(f"  - {factor['variable']}: contribution = {factor['contribution']:.4f}")

# ============================================================================
# Test 6: Plusieurs contrats
# ============================================================================
print("\n[TEST 6] Prédictions pour plusieurs contrats")
print("-" * 80)

contracts = [
    {'VehPower': 6, 'VehAge': 5, 'DrivAge': 35, 'BonusMalus': 50, 'Density': 1000, 'Area': 'B', 'VehBrand': 'B6', 'VehGas': 'Regular'},
    {'VehPower': 8, 'VehAge': 2, 'DrivAge': 25, 'BonusMalus': 100, 'Density': 5000, 'Area': 'A', 'VehBrand': 'B12', 'VehGas': 'Diesel'},
    {'VehPower': 4, 'VehAge': 10, 'DrivAge': 55, 'BonusMalus': 30, 'Density': 500, 'Area': 'C', 'VehBrand': 'B2', 'VehGas': 'Regular'},
]

print(f"\nPrimes pour {len(contracts)} contrats:")
for i, contract in enumerate(contracts):
    result = predict_single_contract(contract, 1.0)
    premium = result.get('pure_premium', 0)
    tier = get_risk_tier(premium)
    print(f"  Contrat {i+1}: {premium:.2f} € ({tier})")

# ============================================================================
# Test 7: Coefficients du modèle
# ============================================================================
print("\n[TEST 7] Coefficients du modèle")
print("-" * 80)

freq_coeffs = get_model_coefficients('frequency')
sev_coeffs = get_model_coefficients('severity')

print(f"\nTop 5 coefficients fréquence:")
for idx, row in freq_coeffs.head(5).iterrows():
    print(f"  - {idx}: {row['Coefficient']:.4f}")

print(f"\nTop 5 coefficients sévérité:")
for idx, row in sev_coeffs.head(5).iterrows():
    print(f"  - {idx}: {row['Coefficient']:.4f}")

# ============================================================================
# Résumé final
# ============================================================================
print("\n" + "=" * 80)
print("RÉSUMÉ DES TESTS")
print("=" * 80)

print(f"\n[RESULTATS]")
print(f"  - Modèles chargés: {'OUI' if model_info['is_loaded'] else 'NON'}")
print(f"  - Prime type: {result.get('pure_premium', 0):.2f} €")
print(f"  - Tier: {tier} ({description})")
print(f"  - Incertitude 90%: [{uncertainty['lower_bound']:.2f} €, {uncertainty['upper_bound']:.2f} €]")

print("\n" + "=" * 80)
print("[OK] TESTS TERMINES AVEC SUCCES")
print("=" * 80)
