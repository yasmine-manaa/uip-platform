"""
freMTPL2 Dataset Loader and Processor
Loads and processes the real freMTPL2 frequency and severity datasets.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional
import os


class FreMTPL2Loader:
    """Loads and processes the real freMTPL2 datasets."""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Use absolute path to datasets directory
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.data_dir = os.path.join(base_dir, "datasets", "raw")
        else:
            self.data_dir = data_dir
        self.freq_df = None
        self.sev_df = None
        self.merged_df = None

    def load_frequency(self) -> pd.DataFrame:
        """Load freMTPL2freq.csv"""
        freq_path = os.path.join(self.data_dir, "freMTPL2freq.csv")
        if not os.path.exists(freq_path):
            raise FileNotFoundError(f"freMTPL2freq.csv not found at {freq_path}")

        self.freq_df = pd.read_csv(freq_path)
        return self.freq_df

    def load_severity(self) -> pd.DataFrame:
        """Load freMTPL2sev.csv"""
        sev_path = os.path.join(self.data_dir, "freMTPL2sev.csv")
        if not os.path.exists(sev_path):
            raise FileNotFoundError(f"freMTPL2sev.csv not found at {sev_path}")

        self.sev_df = pd.read_csv(sev_path)
        return self.sev_df

    def merge_datasets(self) -> pd.DataFrame:
        """Merge frequency and severity datasets on IDpol"""
        if self.freq_df is None:
            self.load_frequency()
        if self.sev_df is None:
            self.load_severity()

        # Merge on IDpol - keep all frequency records, add severity where available
        self.merged_df = self.freq_df.merge(
            self.sev_df, on='IDpol', how='left'
        )

        # Fill missing ClaimAmount with 0 (no claims)
        self.merged_df['ClaimAmount'] = self.merged_df['ClaimAmount'].fillna(0)

        return self.merged_df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare features for ML models.
        Returns: (X, y_freq, y_sev)
        """
        # Map columns to our standard names
        features = pd.DataFrame({
            'driver_age': df['DrivAge'].astype(float),
            'vehicle_power': df['VehPower'].astype(float),
            'vehicle_age': df['VehAge'].astype(float),
            'bonus_malus': df['BonusMalus'].astype(float),
            'area_density': df['Density'].astype(float),
            'licence_years': (df['DrivAge'] - 18).clip(lower=0).astype(float),  # Approximate
            'prior_claims_count': df['ClaimNb'].astype(float),
            'annual_mileage_10k': 1.5,  # Default - not available in freMTPL2
        })

        # One-hot encode usage (freMTPL2 doesn't have usage, so we use defaults)
        features['usage_Commuting'] = 0.0
        features['usage_Private'] = 1.0
        features['usage_Professional'] = 0.0
        features['usage_Taxi_VTC'] = 0.0

        # Target variables
        y_freq = df['ClaimNb'].astype(int)
        y_sev = df['ClaimAmount'].astype(float)

        return features, y_freq, y_sev

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if self.merged_df is None:
            self.merge_datasets()

        return {
            'total_policies': len(self.merged_df),
            'total_claims': self.merged_df['ClaimNb'].sum(),
            'avg_claims_per_policy': self.merged_df['ClaimNb'].mean(),
            'avg_claim_amount': self.merged_df['ClaimAmount'].mean(),
            'max_claim_amount': self.merged_df['ClaimAmount'].max(),
            'min_claim_amount': self.merged_df['ClaimAmount'].min(),
            'driver_age_range': (self.merged_df['DrivAge'].min(), self.merged_df['DrivAge'].max()),
            'vehicle_power_range': (self.merged_df['VehPower'].min(), self.merged_df['VehPower'].max()),
            'bonus_malus_range': (self.merged_df['BonusMalus'].min(), self.merged_df['BonusMalus'].max()),
            'regions': self.merged_df['Region'].nunique(),
            'brands': self.merged_df['VehBrand'].nunique(),
        }

    def get_sample(self, n: int = 5) -> pd.DataFrame:
        """Get a sample of the dataset"""
        if self.merged_df is None:
            self.merge_datasets()
        return self.merged_df.head(n)


# Global instance
fre_mtpl2_loader = FreMTPL2Loader()
