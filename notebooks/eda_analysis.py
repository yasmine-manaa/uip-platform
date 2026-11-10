"""
Analyse Exploratoire des Données - freMTPL2 Dataset
Étape 1 à 6 du plan d'analyse
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration pour les visualisations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# Chemins des données
DATA_DIR = Path("../datasets/raw")
PROCESSED_DIR = Path("../datasets/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("ANALYSE EXPLORATOIRE DES DONNÉES - freMTPL2")
print("=" * 80)

# ============================================================================
# ÉTAPE 1: Charger les fichiers CSV avec Python et Pandas
# ============================================================================
print("\n[ÉTAPE 1] Chargement des fichiers CSV")
print("-" * 80)

df_freq = pd.read_csv(DATA_DIR / "freMTPL2freq.csv")
df_sev = pd.read_csv(DATA_DIR / "freMTPL2sev.csv")

print(f"[OK] Données de fréquence chargées: {df_freq.shape[0]:,} lignes, {df_freq.shape[1]} colonnes")
print(f"[OK] Données de sévérité chargées: {df_sev.shape[0]:,} lignes, {df_sev.shape[1]} colonnes")

# ============================================================================
# ÉTAPE 2: Vérifier la structure (lignes, colonnes, types)
# ============================================================================
print("\n[ÉTAPE 2] Vérification de la structure")
print("-" * 80)

print("\n--- DONNÉES DE FRÉQUENCE ---")
print(f"Dimensions: {df_freq.shape}")
print(f"\nColonnes: {df_freq.columns.tolist()}")
print(f"\nTypes de données:")
print(df_freq.dtypes)

print("\n--- DONNÉES DE SÉVÉRITÉ ---")
print(f"Dimensions: {df_sev.shape}")
print(f"\nColonnes: {df_sev.columns.tolist()}")
print(f"\nTypes de données:")
print(df_sev.dtypes)

print("\n--- STATISTIQUES DESCRIPTIVES (FRÉQUENCE) ---")
print(df_freq.describe())

print("\n--- STATISTIQUES DESCRIPTIVES (SÉVÉRITÉ) ---")
print(df_sev.describe())

# ============================================================================
# ÉTAPE 3: Rechercher les valeurs manquantes et les doublons
# ============================================================================
print("\n[ÉTAPE 3] Valeurs manquantes et doublons")
print("-" * 80)

print("\n--- VALEURS MANQUANTES (FRÉQUENCE) ---")
missing_freq = df_freq.isnull().sum()
if missing_freq.sum() > 0:
    print(missing_freq[missing_freq > 0])
else:
    print("[OK] Aucune valeur manquante")

print("\n--- VALEURS MANQUANTES (SÉVÉRITÉ) ---")
missing_sev = df_sev.isnull().sum()
if missing_sev.sum() > 0:
    print(missing_sev[missing_sev > 0])
else:
    print("[OK] Aucune valeur manquante")

print("\n--- DOUBLONS (FRÉQUENCE) ---")
duplicates_freq = df_freq.duplicated().sum()
print(f"Nombre de doublons: {duplicates_freq:,}")
if duplicates_freq > 0:
    print(f"Pourcentage: {duplicates_freq / len(df_freq) * 100:.2f}%")

print("\n--- DOUBLONS (SÉVÉRITÉ) ---")
duplicates_sev = df_sev.duplicated().sum()
print(f"Nombre de doublons: {duplicates_sev:,}")
if duplicates_sev > 0:
    print(f"Pourcentage: {duplicates_sev / len(df_sev) * 100:.2f}%")

# ============================================================================
# ÉTAPE 4: Étudier les variables importantes
# ============================================================================
print("\n[ÉTAPE 4] Étude des variables importantes")
print("-" * 80)

# Variables clés pour la fréquence
freq_vars = ['ClaimNb', 'Exposure', 'DrivAge', 'BonusMalus', 'VehPower', 'VehAge', 'Density']
print("\n--- VARIABLES CLÉS (FRÉQUENCE) ---")
for var in freq_vars:
    if var in df_freq.columns:
        print(f"\n{var}:")
        print(f"  - Moyenne: {df_freq[var].mean():.2f}")
        print(f"  - Médiane: {df_freq[var].median():.2f}")
        print(f"  - Min: {df_freq[var].min():.2f}")
        print(f"  - Max: {df_freq[var].max():.2f}")
        print(f"  - Écart-type: {df_freq[var].std():.2f}")

# Variables catégorielles
cat_vars = ['Area', 'VehBrand', 'VehGas', 'Region']
print("\n--- VARIABLES CATÉGORIELLES ---")
for var in cat_vars:
    if var in df_freq.columns:
        print(f"\n{var}:")
        print(f"  - Nombre de catégories: {df_freq[var].nunique()}")
        print(f"  - Catégories: {df_freq[var].unique()[:10]}")

# Variable clé pour la sévérité
print("\n--- VARIABLE CLÉ (SÉVÉRITÉ) ---")
print("\nClaimAmount:")
print(f"  - Moyenne: {df_sev['ClaimAmount'].mean():.2f} €")
print(f"  - Médiane: {df_sev['ClaimAmount'].median():.2f} €")
print(f"  - Min: {df_sev['ClaimAmount'].min():.2f} €")
print(f"  - Max: {df_sev['ClaimAmount'].max():.2f} €")
print(f"  - Écart-type: {df_sev['ClaimAmount'].std():.2f} €")

# ============================================================================
# ÉTAPE 5: Visualiser la distribution du nombre de sinistres et des montants
# ============================================================================
print("\n[ÉTAPE 5] Visualisation des distributions")
print("-" * 80)

# Distribution du nombre de sinistres
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Histogramme des sinistres
sns.histplot(df_freq['ClaimNb'], bins=50, ax=axes[0, 0])
axes[0, 0].set_title('Distribution du nombre de sinistres')
axes[0, 0].set_xlabel('Nombre de sinistres')
axes[0, 0].set_ylabel('Fréquence')
axes[0, 0].set_xlim(0, df_freq['ClaimNb'].quantile(0.99))

# Boxplot des sinistres
sns.boxplot(x=df_freq['ClaimNb'], ax=axes[0, 1])
axes[0, 1].set_title('Boxplot du nombre de sinistres')
axes[0, 1].set_xlabel('Nombre de sinistres')
axes[0, 1].set_xlim(0, df_freq['ClaimNb'].quantile(0.99))

# Histogramme des montants de sinistres
sns.histplot(df_sev['ClaimAmount'], bins=50, ax=axes[1, 0])
axes[1, 0].set_title('Distribution des montants de sinistres')
axes[1, 0].set_xlabel('Montant (€)')
axes[1, 0].set_ylabel('Fréquence')
axes[1, 0].set_xlim(0, df_sev['ClaimAmount'].quantile(0.95))

# Boxplot des montants
sns.boxplot(x=df_sev['ClaimAmount'], ax=axes[1, 1])
axes[1, 1].set_title('Boxplot des montants de sinistres')
axes[1, 1].set_xlabel('Montant (€)')
axes[1, 1].set_xlim(0, df_sev['ClaimAmount'].quantile(0.95))

plt.tight_layout()
plt.savefig(PROCESSED_DIR / '01_distributions.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: datasets/processed/01_distributions.png")
plt.close()

# Distribution de l'exposition
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.histplot(df_freq['Exposure'], bins=50, ax=axes[0])
axes[0].set_title('Distribution de l\'exposition (durée de police)')
axes[0].set_xlabel('Exposition (années)')
axes[0].set_ylabel('Fréquence')

sns.boxplot(x=df_freq['Exposure'], ax=axes[1])
axes[1].set_title('Boxplot de l\'exposition')
axes[1].set_xlabel('Exposition (années)')

plt.tight_layout()
plt.savefig(PROCESSED_DIR / '02_exposure.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: datasets/processed/02_exposure.png")
plt.close()

# ============================================================================
# ÉTAPE 6: Analyser les relations entre caractéristiques et risque
# ============================================================================
print("\n[ÉTAPE 6] Analyse des relations caractéristiques/risque")
print("-" * 80)

# Calculer le taux de sinistres
df_freq['ClaimRate'] = df_freq['ClaimNb'] / df_freq['Exposure']

# Relation par zone géographique
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Taux de sinistres par zone
sns.barplot(data=df_freq, x='Area', y='ClaimRate', ax=axes[0, 0])
axes[0, 0].set_title('Taux de sinistres par zone')
axes[0, 0].set_ylabel('Taux de sinistres (sinistres/an)')

# Taux de sinistres par puissance véhicule
sns.barplot(data=df_freq, x='VehPower', y='ClaimRate', ax=axes[0, 1])
axes[0, 1].set_title('Taux de sinistres par puissance véhicule')
axes[0, 1].set_ylabel('Taux de sinistres (sinistres/an)')
axes[0, 1].tick_params(axis='x', rotation=45)

# Taux de sinistres par âge du conducteur (binned)
df_freq['DrivAgeBin'] = pd.cut(df_freq['DrivAge'], bins=[18, 25, 35, 50, 65, 100],
                              labels=['18-25', '25-35', '35-50', '50-65', '65+'])
sns.barplot(data=df_freq, x='DrivAgeBin', y='ClaimRate', ax=axes[0, 2])
axes[0, 2].set_title('Taux de sinistres par âge du conducteur')
axes[0, 2].set_ylabel('Taux de sinistres (sinistres/an)')

# Bonus-Malus vs Taux de sinistres
sns.scatterplot(data=df_freq, x='BonusMalus', y='ClaimRate', alpha=0.3, ax=axes[1, 0])
axes[1, 0].set_title('Taux de sinistres vs Bonus-Malus')
axes[1, 0].set_xlabel('Bonus-Malus')
axes[1, 0].set_ylabel('Taux de sinistres (sinistres/an)')

# Âge du véhicule vs Taux de sinistres
df_freq['VehAgeBin'] = pd.cut(df_freq['VehAge'], bins=[0, 1, 3, 5, 10, 30],
                              labels=['0-1', '1-3', '3-5', '5-10', '10+'])
sns.barplot(data=df_freq, x='VehAgeBin', y='ClaimRate', ax=axes[1, 1])
axes[1, 1].set_title('Taux de sinistres par âge du véhicule')
axes[1, 1].set_ylabel('Taux de sinistres (sinistres/an)')

# Densité vs Taux de sinistres
df_freq['DensityBin'] = pd.qcut(df_freq['Density'], q=5, labels=['Très faible', 'Faible', 'Moyen', 'Élevé', 'Très élevé'])
sns.barplot(data=df_freq, x='DensityBin', y='ClaimRate', ax=axes[1, 2])
axes[1, 2].set_title('Taux de sinistres par densité')
axes[1, 2].set_ylabel('Taux de sinistres (sinistres/an)')
axes[1, 2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(PROCESSED_DIR / '03_relations_risque.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: datasets/processed/03_relations_risque.png")
plt.close()

# Matrice de corrélation
numeric_cols = ['ClaimNb', 'Exposure', 'DrivAge', 'BonusMalus', 'Density', 'VehAge']
correlation_matrix = df_freq[numeric_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f',
            square=True, linewidths=1)
plt.title('Matrice de corrélation des variables numériques')
plt.tight_layout()
plt.savefig(PROCESSED_DIR / '04_correlation_matrix.png', dpi=150, bbox_inches='tight')
print("[OK] Graphique sauvegardé: datasets/processed/04_correlation_matrix.png")
plt.close()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RÉSUMÉ DE L'ANALYSE")
print("=" * 80)

print(f"\n[STATISTIQUES GLOBALES]")
print(f"  - Total de polices: {len(df_freq):,}")
print(f"  - Total d'exposition: {df_freq['Exposure'].sum():.2f} années")
print(f"  - Total de sinistres: {df_freq['ClaimNb'].sum():,}")
print(f"  - Fréquence globale: {df_freq['ClaimNb'].sum() / df_freq['Exposure'].sum():.4f} sinistres/an")
print(f"  - Polices avec sinistres: {(df_freq['ClaimNb'] > 0).sum():,} ({(df_freq['ClaimNb'] > 0).sum() / len(df_freq) * 100:.2f}%)")
print(f"  - Polices sans sinistres: {(df_freq['ClaimNb'] == 0).sum():,} ({(df_freq['ClaimNb'] == 0).sum() / len(df_freq) * 100:.2f}%)")

print(f"\n[STATISTIQUES DE SÉVÉRITÉ]")
print(f"  - Montant moyen des sinistres: {df_sev['ClaimAmount'].mean():.2f} €")
print(f"  - Montant médian des sinistres: {df_sev['ClaimAmount'].median():.2f} €")
print(f"  - Montant max des sinistres: {df_sev['ClaimAmount'].max():.2f} €")

print(f"\n[VARIABLES LES PLUS INFLUENTES]")
print(f"  - Bonus-Malus (moyenne: {df_freq['BonusMalus'].mean():.2f})")
print(f"  - Zone géographique (Area)")
print(f"  - Âge du conducteur (DrivAge, moyenne: {df_freq['DrivAge'].mean():.2f} ans)")
print(f"  - Puissance du véhicule (VehPower, moyenne: {df_freq['VehPower'].mean():.2f})")
print(f"  - Densité de population (Density, moyenne: {df_freq['Density'].mean():.2f})")

print(f"\n[PROCHAINES ÉTAPES]")
print(f"  1. Fusionner les données de fréquence et sévérité")
print(f"  2. Ingénierie des features pour la modélisation")
print(f"  3. Construction du modèle de prédiction de fréquence (GLM Poisson)")
print(f"  4. Construction du modèle de prédiction de sévérité (GLM Gamma)")

print("\n" + "=" * 80)
print("[OK] ANALYSE TERMINÉE")
print("=" * 80)
