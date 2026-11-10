"""
Moteur Actuariel UIP - Combinaison Fréquence × Sévérité
Charge les modèles GLM Poisson et GLM Gamma, effectue les prédictions
et calcule la prime pure pour un contrat donné.
"""

import pandas as pd
import numpy as np
import pickle
import statsmodels.api as sm
from pathlib import Path
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Configuration des chemins
MODELS_DIR = Path(__file__).parent.parent
FREQ_MODEL_PATH = MODELS_DIR / "frequency_model" / "artifacts" / "poisson_frequency_model.pkl"
FREQ_ENCODER_PATH = MODELS_DIR / "frequency_model" / "artifacts" / "feature_encoder.pkl"
FREQ_METADATA_PATH = MODELS_DIR / "frequency_model" / "artifacts" / "model_metadata.pkl"

SEV_MODEL_PATH = MODELS_DIR / "severity_model" / "artifacts" / "gamma_severity_model.pkl"
SEV_ENCODER_PATH = MODELS_DIR / "severity_model" / "artifacts" / "feature_encoder.pkl"
SEV_METADATA_PATH = MODELS_DIR / "severity_model" / "artifacts" / "model_metadata.pkl"


class ActuarialEngine:
    """
    Moteur actuariel qui combine les modèles de fréquence et sévérité
    pour calculer la prime pure d'un contrat d'assurance auto.
    """

    def __init__(self):
        """Initialise le moteur et charge les modèles"""
        self.freq_model = None
        self.sev_model = None
        self.freq_encoder = None
        self.sev_encoder = None
        self.freq_metadata = None
        self.sev_metadata = None
        self.is_loaded = False

        self.load_models()

    def load_models(self):
        """Charge les modèles et les encodeurs depuis les fichiers .pkl"""
        try:
            # Charger le modèle de fréquence
            with open(FREQ_MODEL_PATH, 'rb') as f:
                self.freq_model = pickle.load(f)

            with open(FREQ_ENCODER_PATH, 'rb') as f:
                self.freq_encoder = pickle.load(f)

            with open(FREQ_METADATA_PATH, 'rb') as f:
                self.freq_metadata = pickle.load(f)

            # Charger le modèle de sévérité
            with open(SEV_MODEL_PATH, 'rb') as f:
                self.sev_model = pickle.load(f)

            with open(SEV_ENCODER_PATH, 'rb') as f:
                self.sev_encoder = pickle.load(f)

            with open(SEV_METADATA_PATH, 'rb') as f:
                self.sev_metadata = pickle.load(f)

            self.is_loaded = True
            print("[OK] Modèles actuariaux chargés avec succès")
            print(f"  - Modèle fréquence: {FREQ_MODEL_PATH}")
            print(f"  - Modèle sévérité: {SEV_MODEL_PATH}")

        except Exception as e:
            print(f"[ERROR] Erreur lors du chargement des modèles: {e}")
            self.is_loaded = False

    def prepare_features(self, contract_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prépare les features pour un contrat donné.

        Args:
            contract_data: Dictionnaire contenant les caractéristiques du contrat
                          (VehPower, VehAge, DrivAge, BonusMalus, Density, Area, VehBrand, VehGas)

        Returns:
            DataFrame avec les features encodées prêtes pour la prédiction
        """
        # Extraire les données du contrat
        data = {
            'VehPower': contract_data.get('VehPower', 6),
            'VehAge': contract_data.get('VehAge', 4),
            'DrivAge': contract_data.get('DrivAge', 45),
            'BonusMalus': contract_data.get('BonusMalus', 50),
            'Density': contract_data.get('Density', 1000),
            'Area': contract_data.get('Area', 'B'),
            'VehBrand': contract_data.get('VehBrand', 'B6'),
            'VehGas': contract_data.get('VehGas', 'Regular')
        }

        # Créer un DataFrame
        df = pd.DataFrame([data])

        # Encoder les variables catégorielles
        categorical_cols = ['Area', 'VehBrand', 'VehGas']
        encoded_features = self.freq_encoder.transform(df[categorical_cols])
        encoded_feature_names = self.freq_encoder.get_feature_names_out(categorical_cols)

        df_encoded = pd.DataFrame(encoded_features, columns=encoded_feature_names)

        # Combiner avec les variables numériques
        numeric_features = ['VehPower', 'VehAge', 'DrivAge', 'BonusMalus', 'Density']
        X = pd.concat([df[numeric_features], df_encoded], axis=1)

        # Ajouter la constante pour l'intercept
        # IMPORTANT: L'ordre des colonnes doit correspondre exactement aux features du modèle
        X_const = sm.add_constant(X)

        # Réordonner les colonnes pour correspondre aux features du modèle
        model_features = self.freq_metadata['features']
        # Vérifier si 'const' est déjà dans les colonnes
        if 'const' in X_const.columns:
            # Si 'const' est déjà là, ne pas le rajouter
            X_const = X_const[model_features]
        else:
            # Sinon, ajouter 'const' manuellement
            X_const['const'] = 1.0
            X_const = X_const[model_features]

        return X_const

    def predict_frequency(self, contract_data: Dict[str, Any], exposure: float = 1.0) -> Dict[str, Any]:
        """
        Prédit la fréquence des sinistres pour un contrat.

        Args:
            contract_data: Caractéristiques du contrat
            exposure: Exposition en années (durée de la police)

        Returns:
            Dictionnaire avec les prédictions de fréquence
        """
        if not self.is_loaded:
            return {'error': 'Modèles non chargés'}

        try:
            X = self.prepare_features(contract_data)
            log_exposure = np.log(exposure)

            # Calcul manuel de la prédiction GLM Poisson
            # Pour GLM Poisson avec lien log et offset:
            # log(μ) = X·β + offset
            # μ = exp(X·β + offset)
            # offset = log(exposure)
            # Donc μ = exp(X·β) * exposure

            # Extraire les coefficients du modèle
            params = self.freq_model.params

            # Aligner les colonnes X avec les paramètres
            X_aligned = X[params.index]

            # Calculer le produit scalaire X·β
            linear_predictor = np.dot(X_aligned.values.flatten(), params.values)

            # Calculer la prédiction: μ = exp(X·β) * exposure
            freq_value = np.exp(linear_predictor) * exposure

            # Fréquence annuelle
            annual_freq = freq_value / exposure

            return {
                'expected_claims': float(freq_value),
                'annual_frequency': float(annual_freq),
                'exposure': float(exposure),
                'expected_claims_per_year': float(annual_freq)
            }

        except Exception as e:
            return {'error': f'Erreur prédiction fréquence: {e}'}

    def predict_severity(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prédit la sévérité (coût moyen par sinistre) pour un contrat.

        Args:
            contract_data: Caractéristiques du contrat

        Returns:
            Dictionnaire avec les prédictions de sévérité
        """
        if not self.is_loaded:
            return {'error': 'Modèles non chargés'}

        try:
            X = self.prepare_features(contract_data)

            # Calcul manuel de la prédiction GLM Gamma
            # Le modèle utilise une fonction de lien InversePower
            # 1/μ = X·β, donc μ = 1/(X·β)

            params = self.sev_model.params

            # Aligner les colonnes X avec les paramètres
            X_aligned = X[params.index]

            # Calculer le produit scalaire X·β
            linear_predictor = np.dot(X_aligned.values.flatten(), params.values)

            # Pour GLM Gamma avec lien inverse puissance:
            # 1/μ = X·β
            # μ = 1/(X·β)
            # Vérifier que linear_predictor n'est pas nul ou négatif
            if linear_predictor <= 0:
                sev_value = 2000.0  # Valeur par défaut si prédiction invalide
            else:
                sev_value = 1.0 / linear_predictor

            return {
                'expected_severity': float(sev_value),
                'severity_per_claim': float(sev_value)
            }

        except Exception as e:
            return {'error': f'Erreur prédiction sévérité: {e}'}

    def calculate_pure_premium(self, contract_data: Dict[str, Any], exposure: float = 1.0) -> Dict[str, Any]:
        """
        Calcule la prime pure pour un contrat.

        Formule: Prime Pure = Fréquence × Sévérité × Exposition

        Args:
            contract_data: Caractéristiques du contrat
            exposure: Exposition en années

        Returns:
            Dictionnaire avec tous les résultats actuariaux
        """
        if not self.is_loaded:
            return {'error': 'Modèles non chargés'}

        # Prédire la fréquence
        freq_result = self.predict_frequency(contract_data, exposure)
        if 'error' in freq_result:
            return freq_result

        # Prédire la sévérité
        sev_result = self.predict_severity(contract_data)
        if 'error' in sev_result:
            return sev_result

        # Calculer la prime pure
        annual_freq = freq_result['annual_frequency']
        severity = sev_result['expected_severity']
        pure_premium = annual_freq * severity * exposure

        return {
            'pure_premium': float(pure_premium),
            'annual_pure_premium': float(annual_freq * severity),
            'frequency': freq_result,
            'severity': sev_result,
            'exposure': float(exposure),
            'calculation': {
                'formula': 'Pure Premium = Annual Frequency × Severity × Exposure',
                'annual_frequency': float(annual_freq),
                'severity': float(severity),
                'exposure': float(exposure)
            }
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur les modèles chargés"""
        if not self.is_loaded:
            return {'error': 'Modèles non chargés'}

        return {
            'is_loaded': True,
            'frequency_model': {
                'path': str(FREQ_MODEL_PATH),
                'metadata': self.freq_metadata.get('model_type', 'Unknown'),
                'features': self.freq_metadata.get('features', []),
                'aic': self.freq_metadata.get('aic', 0),
                'bic': self.freq_metadata.get('bic', 0)
            },
            'severity_model': {
                'path': str(SEV_MODEL_PATH),
                'metadata': self.sev_metadata.get('model_type', 'Unknown'),
                'features': self.sev_metadata.get('features', []),
                'aic': self.sev_metadata.get('aic', 0),
                'bic': self.sev_metadata.get('bic', 0)
            }
        }


# Instance globale du moteur
actuarial_engine = ActuarialEngine()
