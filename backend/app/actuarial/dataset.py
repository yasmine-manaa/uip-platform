"""
Actuarial Dataset Generator for French Automobile Insurance.
Inspired by standard actuarial benchmarks (freMTPL2freq / freMTPL2sev).
Simulates realistic distributions for risk factors, claim frequencies (Poisson),
and claim severities (Gamma) with realistic correlations.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


def generate_synthetic_actuarial_dataset(
    n_samples: int = 5000,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic portfolio of auto insurance policies with observable risk variables.
    """
    rng = np.random.default_rng(random_seed)

    driver_age = rng.integers(18, 82, size=n_samples)
    licence_years = np.clip(driver_age - 18 - rng.integers(0, 5, size=n_samples), 0, 60)
    
    base_crm = np.where(licence_years > 10, 0.50 + rng.exponential(0.15, size=n_samples), 1.00 - (licence_years * 0.05))
    bonus_malus = np.clip(np.round(base_crm, 2), 0.50, 1.80)

    prior_claims_count = rng.choice([0, 1, 2, 3], size=n_samples, p=[0.82, 0.13, 0.04, 0.01])

    vehicle_power_values = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 25]
    vehicle_power_probs = np.array([0.05, 0.15, 0.25, 0.25, 0.15, 0.08, 0.05, 0.03, 0.02, 0.01, 0.01, 0.005, 0.005])
    vehicle_power_probs = vehicle_power_probs / vehicle_power_probs.sum()
    vehicle_power = rng.choice(vehicle_power_values, size=n_samples, p=vehicle_power_probs)
    vehicle_age = rng.integers(0, 18, size=n_samples)

    usage_categories = ["Private", "Commuting", "Professional", "Taxi_VTC"]
    usage = rng.choice(usage_categories, size=n_samples, p=[0.35, 0.45, 0.17, 0.03])
    area_density = rng.choice([1, 2, 3, 4, 5, 6], size=n_samples, p=[0.15, 0.20, 0.25, 0.20, 0.12, 0.08])

    annual_mileage = np.clip(
        rng.normal(14000, 4000, size=n_samples) + (area_density * -400) + np.where(usage == "Taxi_VTC", 25000, 0),
        4000, 70000
    ).astype(int)

    exposure = np.clip(rng.beta(8, 1, size=n_samples), 0.1, 1.0)

    # Frequency log rate
    log_lambda = (
        -2.3
        + np.where(driver_age < 25, 0.55, 0.0)
        + np.where(driver_age > 75, 0.30, 0.0)
        + (bonus_malus - 1.0) * 0.70
        + prior_claims_count * 0.35
        + (vehicle_power - 6) * 0.05
        + (area_density - 3) * 0.10
        + np.where(usage == "Taxi_VTC", 0.80, 0.0)
        + np.where(usage == "Professional", 0.20, 0.0)
        + ((annual_mileage - 14000) / 10000.0) * 0.15
    )
    
    expected_claims = np.exp(log_lambda) * exposure
    claim_count = rng.poisson(expected_claims)

    claim_severity = np.zeros(n_samples)
    for i in range(n_samples):
        if claim_count[i] > 0:
            mean_sev = (
                1800.0
                + (vehicle_power[i] * 80.0)
                + (area_density[i] * 100.0)
                + (200.0 if usage[i] in ["Professional", "Taxi_VTC"] else 0.0)
                - (vehicle_age[i] * 20.0)
            )
            k_shape = 1.8
            scale = mean_sev / k_shape
            claim_severity[i] = float(np.sum(rng.gamma(k_shape, scale, size=claim_count[i])))

    df = pd.DataFrame({
        "driver_age": driver_age,
        "licence_years": licence_years,
        "bonus_malus": bonus_malus,
        "prior_claims_count": prior_claims_count,
        "vehicle_power": vehicle_power,
        "vehicle_age": vehicle_age,
        "usage": usage,
        "area_density": area_density,
        "annual_mileage": annual_mileage,
        "exposure": np.round(exposure, 3),
        "claim_count": claim_count,
        "claim_severity": np.round(claim_severity, 2)
    })

    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Standardizes features for stable numerical GLM convergence.
    """
    df_encoded = df.copy()
    
    # Scale annual mileage to units of 10,000 km
    mileage_scaled = df_encoded["annual_mileage"].astype(float) / 10000.0
    
    features = pd.DataFrame({
        "driver_age": df_encoded["driver_age"].astype(float) / 10.0,
        "licence_years": df_encoded["licence_years"].astype(float) / 10.0,
        "bonus_malus": df_encoded["bonus_malus"].astype(float),
        "prior_claims_count": df_encoded["prior_claims_count"].astype(float),
        "vehicle_power": df_encoded["vehicle_power"].astype(float),
        "vehicle_age": df_encoded["vehicle_age"].astype(float) / 10.0,
        "area_density": df_encoded["area_density"].astype(float),
        "annual_mileage_10k": mileage_scaled,
        "usage_Commuting": (df_encoded["usage"] == "Commuting").astype(float),
        "usage_Private": (df_encoded["usage"] == "Private").astype(float),
        "usage_Professional": (df_encoded["usage"] == "Professional").astype(float),
        "usage_Taxi_VTC": (df_encoded["usage"] == "Taxi_VTC").astype(float),
    })
    
    exposure = df_encoded["exposure"].astype(float)
    y_freq = df_encoded["claim_count"].astype(int)
    y_sev = df_encoded["claim_severity"].astype(float)
    
    return features, exposure, y_freq, y_sev
