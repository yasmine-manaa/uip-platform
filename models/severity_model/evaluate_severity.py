"""
Évaluation du modèle de sévérité - GLM Gamma
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
print("ÉVALUATION DU MODÈLE DE SÉVÉRITÉ - GLM GAMMA")
print("=" * 80)

# ============================================================================
# Charger le modèle et les artefacts
# ============================================================================
print("\n[CHARGEMENT] Modèle et artefacts")
print("-" * 80)

with open(ARTIFACTS_DIR / "gamma_severity_model.pkl", 'rb') as f:
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

df_freq = pd.read_csv(DATA_DIR / "freMTPL2freq.csv")
df_freq = df_freq[df_freq['Exposure'] > 0].copy()
df_sev = pd.read_csv(DATA_DIR / "freMTPL2sev.csv")

# Agréger les sinistres par contrat
df_sev_agg = df_sev.groupby('IDpol')['ClaimAmount'].agg(['sum', 'count', 'mean']).reset_index()
df_sev_agg.columns = ['IDpol', 'TotalClaimAmount', 'ClaimCount', 'AvgClaimAmount']

# Jointure
df = df_freq.merge(df_sev_agg, on='IDpol', how='left')
df['TotalClaimAmount'] = df['TotalClaimAmount'].fillna(0)
df['ClaimCount'] = df['ClaimCount'].fillna(0)
df['AvgClaimAmount'] = df['AvgClaimAmount'].fillna(0)

# Filtrer uniquement les contrats avec sinistres
df_with_claims = df[df['ClaimCount'] > 0].copy()
print(f"Contrats avec sinistres: {len(df_with_claims):,}")

# ============================================================================
# Préparer les features
# ============================================================================
print("\n[PRÉPARATION] Features")
print("-" * 80)

categorical_cols = metadata['categorical_features']
numeric_features = metadata['numeric_features']

# Encoder les variables catégorielles
encoded_features = encoder.transform(df_with_claims[categorical_cols])
encoded_feature_names = encoder.get_feature_names_out(categorical_cols)
df_encoded = pd.DataFrame(encoded_features, columns=encoded_feature_names, index=df_with_claims.index)

# Combiner features
X = pd.concat([df_with_claims[numeric_features], df_encoded], axis=1)
X_const = sm.add_constant(X)

# Variable cible
y = df_with_claims['AvgClaimAmount'].values

print(f"Features préparées: {X_const.shape[1]}")

# ============================================================================
# Prédictions
# ============================================================================
print("\n[PRÉDICTION] Prédictions sur l'ensemble des données")
print("-" * 80)

y_pred = model.predict(X_const)

print(f"Coût moyen observé total: {y.mean():.2f} €")
print(f"Coût moyen prédit total: {y_pred.mean():.2f} €")
print(f"Coût total observé: {y.sum():,.2f} €")
print(f"Coût total prédit: {y_pred.sum():,.2f} €")
print(f"Ratio prédit/observé: {y_pred.sum() / y.sum():.4f}")

# ============================================================================
# Visualisations
# ============================================================================
print("\n[VISUALISATION] Création des graphiques")
print("-" * 80)

# 1. Distribution des coûts observés vs prédits
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Histogramme des coûts observés
axes[0, 0].hist(y, bins=50, alpha=0.7, label='Observés', color='blue')
axes[0, 0].set_title('Distribution des coûts observés')
axes[0, 0].set_xlabel('Coût moyen par sinistre (€)')
axes[0, 0].set_ylabel('Fréquence')
axes[0, 0].set_xlim(0, y.max())
axes[0, 0].legend()

# Histogramme des coûts prédits
axes[0, 1].hist(y_pred, bins=50, alpha=0.7, label='Prédits', color='orange')
axes[0, 1].set_title('Distribution des coûts prédits')
axes[0, 1].set_xlabel('Coût moyen par sinistre (€)')
axes[0, 1].set_ylabel('Fréquence')
axes[0, 1].set_xlim(0, y_pred.max())
axes[0, 1].legend()

# Scatter plot observés vs prédits
axes[1, 0].scatter(y, y_pred, alpha=0.3, s=1)
axes[1, 0].plot([0, y.max()], [0, y.max()], 'r--', label='y = x')
axes[1, 0].set_title('Coûts observés vs prédits')
axes[1, 0].set_xlabel('Coûts observés (€)')
axes[1, 0].set_ylabel('Coûts prédits (€)')
axes[1, 0].set_xlim(0, min(y.max(), y.max()))
axes[1, 0].set_ylim(0, min(y_pred.max(), y_pred.max()))
axes[1, 0].legend()

# Résidus
residuals = y - y_pred
axes[1, 1].scatter(y_pred, residuals, alpha=0.3, s=1)
axes[1, 1].axhline(y=0, color='r', linestyle='--')
axes[1, 1].set_title('Résidus vs Valeurs prédites')
axes[1, 1].set_xlabel('Coûts prédits (€)')
axes[1, 1].set_ylabel('Résidus (observés - prédits)')
axes[1, 1].set_xlim(0, min(y_pred.max(), y_pred.max()))
axes[1, 1].set_ylim(-20000, 20000)

plt.tight_layout()
plt.savefig(RESULTS_DIR / '01_distributions_comparison.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: results/01_distributions_comparison.png")
plt.close()

# 2. Coût par groupe
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Coût par zone
df_with_claims['ClaimRate'] = df_with_claims['ClaimCount'] / df_with_claims['Exposure']
df_with_claims['PredictedCost'] = y_pred

sns.barplot(data=df_with_claims, x='Area', y='AvgClaimAmount', ax=axes[0, 0])
axes[0, 0].set_title('Coût observé par zone')
axes[0, 0].set_ylabel('Coût moyen (€)')

sns.barplot(data=df_with_claims, x='Area', y='PredictedCost', ax=axes[0, 1])
axes[0, 1].set_title('Coût prédit par zone')
axes[0, 1].set_ylabel('Coût moyen (€)')

# Coût par Bonus-Malus (binned)
df_with_claims['BonusMalusBin'] = pd.cut(df_with_claims['BonusMalus'], bins=[50, 60, 70, 80, 100, 230],
                              labels=['50-60', '60-70', '70-80', '80-100', '100+'])
sns.barplot(data=df_with_claims, x='BonusMalusBin', y='AvgClaimAmount', ax=axes[1, 0])
axes[1, 0].set_title('Coût observé par Bonus-Malus')
axes[1, 0].set_ylabel('Coût moyen (€)')

sns.barplot(data=df_with_claims, x='BonusMalusBin', y='PredictedCost', ax=axes[1, 1])
axes[1, 1].set_title('Coût prédit par Bonus-Malus')
axes[1, 1].set_ylabel('Coût moyen (€)')

plt.tight_layout()
plt.savefig(RESULTS_DIR / '02_cost_by_group.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: results/02_cost_by_group.png")
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
ax.set_title('Top 15 coefficients (par effet sur le coût)')
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
print(f"  - Contrats analysés: {len(df_with_claims):,}")
print(f"  - Coût moyen observé: {y.mean():.2f} €")
print(f"  - Coût moyen prédit: {y_pred.mean():.2f} €")
print(f"  - Coût total observé: {y.sum():,.2f} €")
print(f"  - Coût total prédit: {y_pred.sum():,.2f} €")

print(f"\n[PERFORMANCE]")
print(f"  - MAE: {np.mean(np.abs(y - y_pred)):.2f} €")
print(f"  - RMSE: {np.sqrt(np.mean((y - y_pred) ** 2)):.2f} €")
print(f"  - MAPE: {np.mean(np.abs((y - y_pred) / y)) * 100:.2f}%")
print(f"  - Ratio prédit/observé: {(y_pred.sum() / y.sum()):.4f}")

print(f"\n[INTERPRÉTATION]")
print(f"  - AIC: {metadata['aic']:.2f}")
print(f"  - BIC: {metadata['bic']:.2f}")
print(f"  - Variables dans le modèle: {len(coefficients)}")
print(f"  - Top variables: {coeff_simple.tail(3).index.tolist()}")

print("\n" + "=" * 80)
print("[OK] EVALUATION TERMINEE")
print("=" * 80)
