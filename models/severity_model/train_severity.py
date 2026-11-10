"""
Modèle de prédiction de sévérité des sinistres - GLM Gamma
Entraînement d'un modèle GLM Gamma pour prédire le coût moyen des sinistres
par contrat en fonction des caractéristiques du contrat.

Formule du modèle:
log(μ_i) = β₀ + Σ βⱼ X_{ij}

Où μ_i est le coût moyen d'un sinistre pour le contrat i.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Gamma
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
print("ENTRAÎNEMENT DU MODÈLE DE SÉVÉRITÉ - GLM GAMMA")
print("=" * 80)

# ============================================================================
# ÉTAPE 1: Charger les données de sévérité et les joindre aux contrats
# ============================================================================
print("\n[ÉTAPE 1] Chargement et jointure des données")
print("-" * 80)

# Charger les données de fréquence
df_freq = pd.read_csv(DATA_DIR / "freMTPL2freq.csv")
df_freq = df_freq[df_freq['Exposure'] > 0].copy()
print(f"Données de fréquence: {df_freq.shape[0]:,} contrats")

# Charger les données de sévérité
df_sev = pd.read_csv(DATA_DIR / "freMTPL2sev.csv")
print(f"Données de sévérité: {df_sev.shape[0]:,} sinistres")

# Agréger les montants des sinistres par contrat
print("\nAgrégation des sinistres par contrat...")
df_sev_agg = df_sev.groupby('IDpol')['ClaimAmount'].agg(['sum', 'count', 'mean']).reset_index()
df_sev_agg.columns = ['IDpol', 'TotalClaimAmount', 'ClaimCount', 'AvgClaimAmount']
print(f"Contrats avec sinistres: {len(df_sev_agg):,}")
print(f"Sinistres totaux: {df_sev_agg['ClaimCount'].sum():,}")
print(f"Montant total: {df_sev_agg['TotalClaimAmount'].sum():,.2f} €")

# Jointure avec les données de fréquence
df = df_freq.merge(df_sev_agg, on='IDpol', how='left')
print(f"\nDonnées jointes: {df.shape[0]:,} contrats")

# Remplir les valeurs manquantes pour les contrats sans sinistres
df['TotalClaimAmount'] = df['TotalClaimAmount'].fillna(0)
df['ClaimCount'] = df['ClaimCount'].fillna(0)
df['AvgClaimAmount'] = df['AvgClaimAmount'].fillna(0)

# Filtrer uniquement les contrats avec au moins un sinistre pour l'entraînement du modèle de sévérité
df_with_claims = df[df['ClaimCount'] > 0].copy()
print(f"\nContrats avec sinistres (pour entraînement sévérité): {len(df_with_claims):,}")

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
encoder.fit(df_with_claims[categorical_cols])

# Créer les features encodées
encoded_features = encoder.transform(df_with_claims[categorical_cols])
encoded_feature_names = encoder.get_feature_names_out(categorical_cols)

df_encoded = pd.DataFrame(encoded_features, columns=encoded_feature_names, index=df_with_claims.index)
print(f"Features encodées créées: {len(encoded_feature_names)}")

# Combiner avec les variables numériques
numeric_features = ['VehPower', 'VehAge', 'DrivAge', 'BonusMalus', 'Density']
X = pd.concat([df_with_claims[numeric_features], df_encoded], axis=1)

# Variable cible: coût moyen des sinistres par contrat
y = df_with_claims['AvgClaimAmount'].values

print(f"\nVariables explicatives totales: {X.shape[1]}")
print(f"Variables numériques: {len(numeric_features)}")
print(f"Variables catégorielles encodées: {len(encoded_feature_names)}")

# ============================================================================
# ÉTAPE 3: Diviser les données en entraînement et test
# ============================================================================
print("\n[ÉTAPE 3] Division entraînement/test")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=None
)

print(f"Entraînement: {len(X_train):,} contrats avec sinistres")
print(f"Test: {len(X_test):,} contrats avec sinistres")
print(f"Ratio test: {len(X_test) / len(X) * 100:.1f}%")

# Statistiques des cibles
print(f"\nCoût moyen observé (entraînement): {y_train.mean():.2f} €")
print(f"Coût moyen observé (test): {y_test.mean():.2f} €")
print(f"Coût total (entraînement): {y_train.sum():,.2f} €")
print(f"Coût total (test): {y_test.sum():,.2f} €")

# ============================================================================
# ÉTAPE 4: Entraîner le GLM Gamma
# ============================================================================
print("\n[ÉTAPE 4] Entraînement du GLM Gamma")
print("-" * 80)

# Ajouter une constante pour l'intercept
X_train_const = sm.add_constant(X_train)
X_test_const = sm.add_constant(X_test)

print("\nEntraînement en cours...")
gamma_model = sm.GLM(
    y_train,
    X_train_const,
    family=Gamma()
)

gamma_results = gamma_model.fit()
print("[OK] Modèle entraîné avec succès")

# Afficher le résumé
print("\n=== RÉSUMÉ DU MODÈLE ===")
print(gamma_results.summary())

# ============================================================================
# ÉTAPE 5: Évaluer le modèle
# ============================================================================
print("\n[ÉTAPE 5] Évaluation du modèle")
print("-" * 80)

# Prédictions
y_pred_train = gamma_results.predict(X_train_const)
y_pred_test = gamma_results.predict(X_test_const)

# Calculer les métriques
def gamma_deviance(y_true, y_pred):
    """Calcule la Gamma Deviance"""
    with np.errstate(divide='ignore', invalid='ignore'):
        term = -np.log(y_true / y_pred) + (y_true - y_pred) / y_pred
        deviance = 2.0 * np.sum(term)
    return deviance

def calculate_metrics(y_true, y_pred, dataset_name):
    """Calcule les métriques d'évaluation"""
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    deviance = gamma_deviance(y_true, y_pred)

    print(f"\n--- {dataset_name} ---")
    print(f"MAE (Mean Absolute Error): {mae:.2f} €")
    print(f"RMSE (Root Mean Squared Error): {rmse:.2f} €")
    print(f"MAPE (Mean Absolute Percentage Error): {mape:.2f}%")
    print(f"Gamma Deviance: {deviance:.2f}")
    print(f"Coût moyen observé: {y_true.mean():.2f} €")
    print(f"Coût moyen prédit: {y_pred.mean():.2f} €")
    print(f"Ratio prédit/observé: {y_pred.mean() / y_true.mean():.4f}")

    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'deviance': deviance,
        'obs_mean': y_true.mean(),
        'pred_mean': y_pred.mean()
    }

metrics_train = calculate_metrics(y_train, y_pred_train, "ENSEMBLE D'ENTRAÎNEMENT")
metrics_test = calculate_metrics(y_test, y_pred_test, "ENSEMBLE DE TEST")

# ============================================================================
# ÉTAPE 6: Interpréter les coefficients
# ============================================================================
print("\n[ÉTAPE 6] Interprétation des coefficients")
print("-" * 80)

# Extraire les coefficients
coefficients = pd.DataFrame({
    'Variable': X_train_const.columns,
    'Coefficient': gamma_results.params,
    'Std_Err': gamma_results.bse,
    'z_value': gamma_results.tvalues,
    'p_value': gamma_results.pvalues,
    'Exp_Coeff': np.exp(gamma_results.params)  # Multiplicateur de coût
})

# Filtrer pour afficher les variables significatives
sig_coeff = coefficients[coefficients['p_value'] < 0.05].sort_values('Coefficient', ascending=False)

print(f"\nVariables significatives (p < 0.05): {len(sig_coeff)}")
print("\nTop 10 variables par effet sur le coût:")
print(sig_coeff.head(10).to_string(index=False))

print("\nInterprétation des coefficients:")
print("- Coefficient positif: augmente le coût moyen des sinistres")
print("- Coefficient négatif: réduit le coût moyen des sinistres")
print("- Exp(Coeff) > 1: multiplie le coût par ce facteur")
print("- Exp(Coeff) < 1: divise le coût par ce facteur")

# ============================================================================
# ÉTAPE 7: Sauvegarder le modèle et les artefacts
# ============================================================================
print("\n[ÉTAPE 7] Sauvegarde du modèle et des artefacts")
print("-" * 80)

# Sauvegarder le modèle
model_path = ARTIFACTS_DIR / "gamma_severity_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(gamma_results, f)
print(f"[OK] Modèle sauvegardé: {model_path}")

# Sauvegarder l'encoder
encoder_path = ARTIFACTS_DIR / "feature_encoder.pkl"
with open(encoder_path, 'wb') as f:
    pickle.dump(encoder, f)
print(f"[OK] Encoder sauvegardé: {encoder_path}")

# Sauvegarder les métadonnées
metadata = {
    'model_type': 'GLM Gamma',
    'target': 'AvgClaimAmount (coût moyen par sinistre)',
    'features': X_train_const.columns.tolist(),
    'numeric_features': numeric_features,
    'categorical_features': categorical_cols,
    'n_observations_train': len(X_train),
    'n_observations_test': len(X_test),
    'metrics_train': metrics_train,
    'metrics_test': metrics_test,
    'coefficients': coefficients.to_dict(),
    'aic': gamma_results.aic,
    'bic': gamma_results.bic
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
print(f"  - Type: GLM Gamma")
print(f"  - Observations entraînement: {len(X_train):,}")
print(f"  - Observations test: {len(X_test):,}")
print(f"  - Variables explicatives: {X_train_const.shape[1]}")
print(f"  - AIC: {gamma_results.aic:.2f}")
print(f"  - BIC: {gamma_results.bic:.2f}")

print(f"\n[PERFORMANCE (TEST)]")
print(f"  - MAE: {metrics_test['mae']:.2f} €")
print(f"  - RMSE: {metrics_test['rmse']:.2f} €")
print(f"  - MAPE: {metrics_test['mape']:.2f}%")
print(f"  - Gamma Deviance: {metrics_test['deviance']:.2f}")
print(f"  - Coût moyen observé: {metrics_test['obs_mean']:.2f} €")
print(f"  - Coût moyen prédit: {metrics_test['pred_mean']:.2f} €")
print(f"  - Ratio prédit/observé: {metrics_test['pred_mean'] / metrics_test['obs_mean']:.4f}")

print(f"\n[FACTEURS DE COÛT PRINCIPAUX]")
print(f"  - Variables significatives: {len(sig_coeff)}")
print(f"  - Top variable: {sig_coeff.iloc[0]['Variable']} (Exp(Coeff) = {sig_coeff.iloc[0]['Exp_Coeff']:.4f})")

print(f"\n[ARTEFACTS SAUVEGARDÉS]")
print(f"  - {model_path}")
print(f"  - {encoder_path}")
print(f"  - {metadata_path}")

print("\n" + "=" * 80)
print("[OK] ENTRAINEMENT TERMINE AVEC SUCCES")
print("=" * 80)
