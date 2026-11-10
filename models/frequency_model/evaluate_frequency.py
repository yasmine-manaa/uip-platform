"""
Évaluation du modèle de fréquence - GLM Poisson
Charge le modèle entraîné et effectue une évaluation détaillée
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from pathlib import Path

# Configuration
DATA_DIR = Path("../../datasets/raw")
ARTIFACTS_DIR = Path("./artifacts")
RESULTS_DIR = Path("./results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("ÉVALUATION DU MODÈLE DE FRÉQUENCE - GLM POISSON")
print("=" * 80)

# ============================================================================
# Charger le modèle et les artefacts
# ============================================================================
print("\n[CHARGEMENT] Modèle et artefacts")
print("-" * 80)

with open(ARTIFACTS_DIR / "poisson_frequency_model.pkl", 'rb') as f:
    model = pickle.load(f)
print("[OK] Modèle chargé")

with open(ARTIFACTS_DIR / "feature_encoder.pkl", 'rb') as f:
    encoder = pickle.load(f)
print("[OK] Encoder chargé")

with open(ARTIFACTS_DIR / "model_metadata.pkl", 'rb') as f:
    metadata = pickle.load(f)
print("[OK] Métadonnées chargées")

# ============================================================================
# Charger les données
# ============================================================================
print("\n[CHARGEMENT] Données")
print("-" * 80)

df = pd.read_csv(DATA_DIR / "freMTPL2freq.csv")
df = df[df['Exposure'] > 0].copy()
print(f"Données chargées: {len(df):,} contrats")

# ============================================================================
# Préparer les features
# ============================================================================
print("\n[PRÉPARATION] Features")
print("-" * 80)

categorical_cols = metadata['categorical_features']
numeric_features = metadata['numeric_features']

# Encoder les variables catégorielles
encoded_features = encoder.transform(df[categorical_cols])
encoded_feature_names = encoder.get_feature_names_out(categorical_cols)
df_encoded = pd.DataFrame(encoded_features, columns=encoded_feature_names, index=df.index)

# Combiner features
X = pd.concat([df[numeric_features], df_encoded], axis=1)
X_const = sm.add_constant(X)

# Variable cible et exposition
y = df['ClaimNb'].values
exposure = df['Exposure'].values
log_exposure = np.log(exposure)

print(f"Features préparées: {X_const.shape[1]}")

# ============================================================================
# Prédictions
# ============================================================================
print("\n[PRÉDICTION] Prédictions sur l'ensemble des données")
print("-" * 80)

y_pred = model.predict(X_const, offset=log_exposure)

print(f"Nombre total de sinistres observés: {y.sum():,}")
print(f"Nombre total de sinistres prédits: {y_pred.sum():,.0f}")
print(f"Fréquence observée: {y.sum() / exposure.sum():.4f} sinistres/an")
print(f"Fréquence prédite: {y_pred.sum() / exposure.sum():.4f} sinistres/an")

# ============================================================================
# Visualisations
# ============================================================================
print("\n[VISUALISATION] Création des graphiques")
print("-" * 80)

# 1. Distribution des sinistres observés vs prédits
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Histogramme des sinistres observés
axes[0, 0].hist(y, bins=50, alpha=0.7, label='Observés', color='blue')
axes[0, 0].set_title('Distribution des sinistres observés')
axes[0, 0].set_xlabel('Nombre de sinistres')
axes[0, 0].set_ylabel('Fréquence')
axes[0, 0].set_xlim(0, y.max())
axes[0, 0].legend()

# Histogramme des sinistres prédits
axes[0, 1].hist(y_pred, bins=50, alpha=0.7, label='Prédits', color='orange')
axes[0, 1].set_title('Distribution des sinistres prédits')
axes[0, 1].set_xlabel('Nombre de sinistres')
axes[0, 1].set_ylabel('Fréquence')
axes[0, 1].set_xlim(0, y_pred.max())
axes[0, 1].legend()

# Scatter plot observés vs prédits
axes[1, 0].scatter(y, y_pred, alpha=0.3, s=1)
axes[1, 0].plot([0, y.max()], [0, y.max()], 'r--', label='y = x')
axes[1, 0].set_title('Sinistres observés vs prédits')
axes[1, 0].set_xlabel('Sinistres observés')
axes[1, 0].set_ylabel('Sinistres prédits')
axes[1, 0].set_xlim(0, min(y.max(), 5))
axes[1, 0].set_ylim(0, min(y_pred.max(), 5))
axes[1, 0].legend()

# Résidus
residuals = y - y_pred
axes[1, 1].scatter(y_pred, residuals, alpha=0.3, s=1)
axes[1, 1].axhline(y=0, color='r', linestyle='--')
axes[1, 1].set_title('Résidus vs Valeurs prédites')
axes[1, 1].set_xlabel('Sinistres prédits')
axes[1, 1].set_ylabel('Résidus (observés - prédits)')
axes[1, 1].set_xlim(0, min(y_pred.max(), 5))
axes[1, 1].set_ylim(-2, 2)

plt.tight_layout()
plt.savefig(RESULTS_DIR / '01_distributions_comparison.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: results/01_distributions_comparison.png")
plt.close()

# 2. Fréquence par groupe
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Fréquence par zone
df['ClaimRate'] = y / exposure
df['PredictedRate'] = y_pred / exposure

sns.barplot(data=df, x='Area', y='ClaimRate', ax=axes[0, 0])
axes[0, 0].set_title('Fréquence observée par zone')
axes[0, 0].set_ylabel('Fréquence (sinistres/an)')

sns.barplot(data=df, x='Area', y='PredictedRate', ax=axes[0, 1])
axes[0, 1].set_title('Fréquence prédite par zone')
axes[0, 1].set_ylabel('Fréquence (sinistres/an)')

# Fréquence par Bonus-Malus (binned)
df['BonusMalusBin'] = pd.cut(df['BonusMalus'], bins=[50, 60, 70, 80, 100, 230],
                              labels=['50-60', '60-70', '70-80', '80-100', '100+'])
sns.barplot(data=df, x='BonusMalusBin', y='ClaimRate', ax=axes[1, 0])
axes[1, 0].set_title('Fréquence observée par Bonus-Malus')
axes[1, 0].set_ylabel('Fréquence (sinistres/an)')

sns.barplot(data=df, x='BonusMalusBin', y='PredictedRate', ax=axes[1, 1])
axes[1, 1].set_title('Fréquence prédite par Bonus-Malus')
axes[1, 1].set_ylabel('Fréquence (sinistres/an)')

plt.tight_layout()
plt.savefig(RESULTS_DIR / '02_frequency_by_group.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: results/02_frequency_by_group.png")
plt.close()

# 3. Coefficients du modèle (simplifié)
coefficients_dict = metadata['coefficients']
coefficients = pd.DataFrame(coefficients_dict)
coefficients.index.name = 'Variable'

# Créer une version simple pour le graphique
coeff_simple = coefficients[['Coefficient']].copy()
coeff_simple = coeff_simple.sort_values('Coefficient')

fig, ax = plt.subplots(figsize=(12, 8))
coeff_simple.tail(15).plot.barh(ax=ax)
ax.set_title('Top 15 coefficients (par effet sur le risque)')
ax.set_xlabel('Coefficient')
ax.set_ylabel('Variable')
plt.tight_layout()
plt.savefig(RESULTS_DIR / '03_coefficients.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: results/03_coefficients.png")
plt.close()

# ============================================================================
# Rapport d'évaluation
# ============================================================================
print("\n" + "=" * 80)
print("RAPPORT D'ÉVALUATION")
print("=" * 80)

print(f"\n[STATISTIQUES GLOBALES]")
print(f"  - Contrats analysés: {len(df):,}")
print(f"  - Exposition totale: {exposure.sum():.2f} années")
print(f"  - Sinistres observés: {y.sum():,}")
print(f"  - Sinistres prédits: {y_pred.sum():,.0f}")

print(f"\n[PERFORMANCE]")
print(f"  - MAE: {np.mean(np.abs(y - y_pred)):.4f}")
print(f"  - RMSE: {np.sqrt(np.mean((y - y_pred) ** 2)):.4f}")
print(f"  - Fréquence observée: {y.sum() / exposure.sum():.4f} sinistres/an")
print(f"  - Fréquence prédite: {y_pred.sum() / exposure.sum():.4f} sinistres/an")
print(f"  - Ratio prédit/observé: {(y_pred.sum() / exposure.sum()) / (y.sum() / exposure.sum()):.4f}")

print(f"\n[INTERPRÉTATION]")
print(f"  - AIC: {metadata['aic']:.2f}")
print(f"  - BIC: {metadata['bic']:.2f}")
print(f"  - Variables dans le modèle: {len(coefficients)}")
print(f"  - Top variables: {coeff_simple.tail(3).index.tolist()}")

print("\n" + "=" * 80)
print("[OK] EVALUATION TERMINEE")
print("=" * 80)
