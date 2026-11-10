"""
Modèle de prédiction de fréquence des sinistres - GLM Poisson
Entraînement d'un modèle GLM Poisson avec offset d'exposition pour prédire
le nombre attendu de sinistres par année d'exposition.

Formule du modèle:
log(λ_i) = log(Exposure_i) + β₀ + Σ βⱼ X_{ij}

Où λ_i est le nombre attendu de sinistres pour le contrat i.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Poisson
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path("../../datasets/raw")
ARTIFACTS_DIR = Path("./artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("ENTRAÎNEMENT DU MODÈLE DE FRÉQUENCE - GLM POISSON")
print("=" * 80)

# ============================================================================
# ÉTAPE 1: Charger et préparer les données
# ============================================================================
print("\n[ÉTAPE 1] Chargement et préparation des données")
print("-" * 80)

df = pd.read_csv(DATA_DIR / "freMTPL2freq.csv")
print(f"Données chargées: {df.shape[0]:,} lignes, {df.shape[1]} colonnes")

# Vérifier les valeurs manquantes
print(f"\nValeurs manquantes par colonne:")
missing = df.isnull().sum()
if missing.sum() > 0:
    print(missing[missing > 0])
else:
    print("[OK] Aucune valeur manquante")

# Supprimer les lignes avec exposition nulle (éviter log(0))
df = df[df['Exposure'] > 0].copy()
print(f"\nContrats avec exposition > 0: {len(df):,}")

# ============================================================================
# ÉTAPE 2: Encoder les variables catégorielles
# ============================================================================
print("\n[ÉTAPE 2] Encodage des variables catégorielles")
print("-" * 80)

# Variables catégorielles à encoder
categorical_cols = ['Area', 'VehBrand', 'VehGas']
print(f"Variables catégorielles: {categorical_cols}")

# One-hot encoding
encoder = OneHotEncoder(sparse_output=False, drop='first')
encoder.fit(df[categorical_cols])

# Créer les features encodées
encoded_features = encoder.transform(df[categorical_cols])
encoded_feature_names = encoder.get_feature_names_out(categorical_cols)

df_encoded = pd.DataFrame(encoded_features, columns=encoded_feature_names, index=df.index)
print(f"Features encodées créées: {len(encoded_feature_names)}")

# Combiner avec les variables numériques
numeric_features = ['VehPower', 'VehAge', 'DrivAge', 'BonusMalus', 'Density']
X = pd.concat([df[numeric_features], df_encoded], axis=1)

# Variable cible: nombre de sinistres
y = df['ClaimNb'].values

# Exposition (pour l'offset)
exposure = df['Exposure'].values

print(f"\nVariables explicatives totales: {X.shape[1]}")
print(f"Variables numériques: {len(numeric_features)}")
print(f"Variables catégorielles encodées: {len(encoded_feature_names)}")

# ============================================================================
# ÉTAPE 3: Diviser les données en entraînement et test
# ============================================================================
print("\n[ÉTAPE 3] Division entraînement/test")
print("-" * 80)

X_train, X_test, y_train, y_test, exp_train, exp_test = train_test_split(
    X, y, exposure, test_size=0.2, random_state=42, stratify=None
)

print(f"Entraînement: {len(X_train):,} contrats")
print(f"Test: {len(X_test):,} contrats")
print(f"Ratio test: {len(X_test) / len(X) * 100:.1f}%")

# Statistiques des cibles
print(f"\nSinistres totaux (entraînement): {y_train.sum():,}")
print(f"Sinistres totaux (test): {y_test.sum():,}")
print(f"Fréquence (entraînement): {y_train.sum() / exp_train.sum():.4f} sinistres/an")
print(f"Fréquence (test): {y_test.sum() / exp_test.sum():.4f} sinistres/an")

# ============================================================================
# ÉTAPE 4: Entraîner le GLM Poisson avec offset d'exposition
# ============================================================================
print("\n[ÉTAPE 4] Entraînement du GLM Poisson")
print("-" * 80)

# Ajouter une constante pour l'intercept
X_train_const = sm.add_constant(X_train)
X_test_const = sm.add_constant(X_test)

# Offset logarithmique de l'exposition
log_exposure_train = np.log(exp_train)
log_exposure_test = np.log(exp_test)

print(f"Offset d'exposition (log): moyenne = {log_exposure_train.mean():.4f}")

# Entraîner le modèle GLM Poisson
print("\nEntraînement en cours...")
poisson_model = sm.GLM(
    y_train,
    X_train_const,
    family=Poisson(),
    offset=log_exposure_train
)

poisson_results = poisson_model.fit()
print("[OK] Modèle entraîné avec succès")

# Afficher le résumé
print("\n=== RÉSUMÉ DU MODÈLE ===")
print(poisson_results.summary())

# ============================================================================
# ÉTAPE 5: Évaluer le modèle
# ============================================================================
print("\n[ÉTAPE 5] Évaluation du modèle")
print("-" * 80)

# Prédictions
y_pred_train = poisson_results.predict(X_train_const, offset=log_exposure_train)
y_pred_test = poisson_results.predict(X_test_const, offset=log_exposure_test)

# Calculer les métriques
def poisson_deviance(y_true, y_pred):
    """Calcule la Poisson Deviance"""
    with np.errstate(divide='ignore', invalid='ignore'):
        term = np.where(y_true > 0, y_true * np.log(y_true / y_pred), 0.0)
        deviance = 2.0 * np.sum(term - (y_true - y_pred))
    return deviance

def calculate_metrics(y_true, y_pred, exposure, dataset_name):
    """Calcule les métriques d'évaluation"""
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    deviance = poisson_deviance(y_true, y_pred)

    # Fréquence observée vs prédite
    obs_freq = y_true.sum() / exposure.sum()
    pred_freq = y_pred.sum() / exposure.sum()

    print(f"\n--- {dataset_name} ---")
    print(f"MAE (Mean Absolute Error): {mae:.4f}")
    print(f"RMSE (Root Mean Squared Error): {rmse:.4f}")
    print(f"Poisson Deviance: {deviance:.2f}")
    print(f"Fréquence observée: {obs_freq:.4f} sinistres/an")
    print(f"Fréquence prédite: {pred_freq:.4f} sinistres/an")
    print(f"Ratio prédit/observé: {pred_freq / obs_freq:.4f}")

    return {
        'mae': mae,
        'rmse': rmse,
        'deviance': deviance,
        'obs_freq': obs_freq,
        'pred_freq': pred_freq
    }

metrics_train = calculate_metrics(y_train, y_pred_train, exp_train, "ENSEMBLE D'ENTRAÎNEMENT")
metrics_test = calculate_metrics(y_test, y_pred_test, exp_test, "ENSEMBLE DE TEST")

# ============================================================================
# ÉTAPE 6: Interpréter les coefficients
# ============================================================================
print("\n[ÉTAPE 6] Interprétation des coefficients")
print("-" * 80)

# Extraire les coefficients
coefficients = pd.DataFrame({
    'Variable': X_train_const.columns,
    'Coefficient': poisson_results.params,
    'Std_Err': poisson_results.bse,
    'z_value': poisson_results.tvalues,
    'p_value': poisson_results.pvalues,
    'Exp_Coeff': np.exp(poisson_results.params)  # Incidence Rate Ratio
})

# Filtrer pour afficher les variables significatives
sig_coeff = coefficients[coefficients['p_value'] < 0.05].sort_values('Coefficient', ascending=False)

print(f"\nVariables significatives (p < 0.05): {len(sig_coeff)}")
print("\nTop 10 variables par effet sur le risque:")
print(sig_coeff.head(10).to_string(index=False))

print("\nInterprétation des coefficients:")
print("- Coefficient positif: augmente le risque de sinistre")
print("- Coefficient négatif: réduit le risque de sinistre")
print("- Exp(Coeff) > 1: multiplie le risque par ce facteur")
print("- Exp(Coeff) < 1: divise le risque par ce facteur")

# ============================================================================
# ÉTAPE 7: Sauvegarder le modèle et les artefacts
# ============================================================================
print("\n[ÉTAPE 7] Sauvegarde du modèle et des artefacts")
print("-" * 80)

# Sauvegarder le modèle
model_path = ARTIFACTS_DIR / "poisson_frequency_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(poisson_results, f)
print(f"[OK] Modèle sauvegardé: {model_path}")

# Sauvegarder l'encoder
encoder_path = ARTIFACTS_DIR / "feature_encoder.pkl"
with open(encoder_path, 'wb') as f:
    pickle.dump(encoder, f)
print(f"[OK] Encoder sauvegardé: {encoder_path}")

# Sauvegarder les métadonnées
metadata = {
    'model_type': 'GLM Poisson',
    'target': 'ClaimNb (nombre de sinistres)',
    'offset': 'log(Exposure)',
    'features': X_train_const.columns.tolist(),
    'numeric_features': numeric_features,
    'categorical_features': categorical_cols,
    'n_observations_train': len(X_train),
    'n_observations_test': len(X_test),
    'metrics_train': metrics_train,
    'metrics_test': metrics_test,
    'coefficients': coefficients.to_dict(),
    'aic': poisson_results.aic,
    'bic': poisson_results.bic
}

metadata_path = ARTIFACTS_DIR / "model_metadata.pkl"
with open(metadata_path, 'wb') as f:
    pickle.dump(metadata, f)
print(f"[OK] Métadonnées sauvegardées: {metadata_path}")

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RÉSUMÉ DE L'ENTRAÎNEMENT")
print("=" * 80)

print(f"\n[STATISTIQUES DU MODÈLE]")
print(f"  - Type: GLM Poisson avec offset d'exposition")
print(f"  - Observations entraînement: {len(X_train):,}")
print(f"  - Observations test: {len(X_test):,}")
print(f"  - Variables explicatives: {X_train_const.shape[1]}")
print(f"  - AIC: {poisson_results.aic:.2f}")
print(f"  - BIC: {poisson_results.bic:.2f}")

print(f"\n[PERFORMANCE (TEST)]")
print(f"  - MAE: {metrics_test['mae']:.4f}")
print(f"  - RMSE: {metrics_test['rmse']:.4f}")
print(f"  - Poisson Deviance: {metrics_test['deviance']:.2f}")
print(f"  - Fréquence observée: {metrics_test['obs_freq']:.4f} sinistres/an")
print(f"  - Fréquence prédite: {metrics_test['pred_freq']:.4f} sinistres/an")
print(f"  - Ratio prédit/observé: {metrics_test['pred_freq'] / metrics_test['obs_freq']:.4f}")

print(f"\n[FACTEURS DE RISQUE PRINCIPAUX]")
print(f"  - Variables significatives: {len(sig_coeff)}")
print(f"  - Top variable: {sig_coeff.iloc[0]['Variable']} (Exp(Coeff) = {sig_coeff.iloc[0]['Exp_Coeff']:.4f})")

print(f"\n[ARTEFACTS SAUVEGARDÉS]")
print(f"  - {model_path}")
print(f"  - {encoder_path}")
print(f"  - {metadata_path}")

print("\n" + "=" * 80)
print("[OK] ENTRAINEMENT TERMINE AVEC SUCCES")
print("=" * 80)
