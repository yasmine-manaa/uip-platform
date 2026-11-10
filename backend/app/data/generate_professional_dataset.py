"""
Generate Professional Car Insurance Dataset
Creates a large, realistic dataset with 50,000+ records and 20+ features
Based on industry standards for insurance underwriting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
N_RECORDS = 50000  # 50,000 records
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2024, 12, 31)

# Feature categories
CAR_MAKES = ['Renault', 'Peugeot', 'Citroën', 'Volkswagen', 'Toyota', 'Ford', 'BMW', 'Mercedes', 'Audi', 'Opel', 'Fiat', 'Hyundai', 'Kia', 'Nissan', 'Honda']
CAR_MODELS = {
    'Renault': ['Clio', 'Megane', 'Captur', 'Talisman', 'Kadjar', 'Austral'],
    'Peugeot': ['208', '308', '3008', '508', '2008', '5008'],
    'Citroën': ['C3', 'C4', 'C5 Aircross', 'C3 Aircross', 'Berlingo'],
    'Volkswagen': ['Polo', 'Golf', 'Tiguan', 'Passat', 'T-Roc', 'ID.3'],
    'Toyota': ['Yaris', 'Corolla', 'RAV4', 'C-HR', 'Aygo'],
    'Ford': ['Fiesta', 'Focus', 'Puma', 'Kuga', 'Mondeo'],
    'BMW': ['Série 1', 'Série 3', 'Série 5', 'X1', 'X3', 'X5'],
    'Mercedes': ['Classe A', 'Classe C', 'Classe E', 'GLA', 'GLC', 'GLE'],
    'Audi': ['A1', 'A3', 'A4', 'A6', 'Q3', 'Q5'],
    'Opel': ['Corsa', 'Astra', 'Mokka', 'Insignia', 'Grandland'],
    'Fiat': ['500', 'Panda', 'Tipo', '500X', 'Doblo'],
    'Hyundai': ['i20', 'i30', 'Tucson', 'Santa Fe', 'Kona'],
    'Kia': ['Picanto', 'Ceed', 'Sportage', 'Sorento', 'Stonic'],
    'Nissan': ['Micra', 'Juke', 'Qashqai', 'X-Trail', 'Leaf'],
    'Honda': ['Jazz', 'Civic', 'CR-V', 'HR-V', 'e:Ny1']
}

FUEL_TYPES = ['Essence', 'Diesel', 'Hybride', 'Électrique', 'GPL']
USAGE_TYPES = ['Privé', 'Professionnel', 'VTC', 'Taxi', 'Agricole']
REGIONS = ['Île-de-France', 'Auvergne-Rhône-Alpes', 'Hauts-de-France', 'Nouvelle-Aquitaine', 'Occitanie',
           'Grand Est', 'Pays de la Loire', 'Bretagne', 'Normandie', 'Centre-Val de Loire',
           'Bourgogne-Franche-Comté', 'Provence-Alpes-Côte d\'Azur', 'Corse']
PROFESSIONS = ['Salarié', 'Cadre', 'Indépendant', 'Retraité', 'Étudiant', 'Sans emploi', 'Profession libérale', 'Agriculteur']
MARITAL_STATUS = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Veuf/Veuve']
COVERAGE_TYPES = ['RC_Tiers', 'RC_Tiers_Complet', 'Tous_Risques', 'Tous_Risques_Premium']

# Generate data
data = []

for i in range(N_RECORDS):
    # Policy ID
    policy_id = f"POL-{2020 + (i // 5000):04d}-{i % 5000:05d}"

    # Policy dates
    policy_start = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
    policy_end = policy_start + timedelta(days=365)

    # Applicant demographics
    age = np.random.randint(18, 85)
    gender = random.choice(['M', 'F'])
    marital_status = random.choice(MARITAL_STATUS)
    profession = random.choice(PROFESSIONS)
    region = random.choice(REGIONS)

    # Driver info
    licence_years = max(0, age - 18 - random.randint(0, 10))
    has_licence = 1 if licence_years > 0 else 0

    # Vehicle info
    make = random.choice(CAR_MAKES)
    model = random.choice(CAR_MODELS[make])
    year = random.randint(2010, 2024)
    fuel_type = random.choice(FUEL_TYPES)
    vehicle_age = 2024 - year

    # Vehicle power (CV) - based on model size
    if model in ['Série 5', 'Série 7', 'X5', 'X7', 'Classe E', 'Classe S', 'GLC', 'GLE', 'Q7', 'A6', 'A8']:
        power_cv = random.randint(10, 20)
    elif model in ['Série 3', 'X3', 'Classe C', 'GLA', 'Q5', 'A4', 'Tiguan', 'Passat']:
        power_cv = random.randint(7, 12)
    else:
        power_cv = random.randint(4, 9)

    # Usage
    usage = random.choice(USAGE_TYPES)

    # Mileage
    annual_mileage = np.random.randint(5000, 50000)

    # Claims history
    bonus_malus = np.random.choice([0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.25, 1.50, 2.00],
                                 p=[0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.08, 0.04, 0.02, 0.01])
    prior_claims = np.random.poisson(0.3)
    prior_claims = min(prior_claims, 5)  # Cap at 5
    total_claim_amount = np.random.exponential(1500) if prior_claims > 0 else 0

    # Coverage
    coverage = random.choice(COVERAGE_TYPES)

    # Premium calculation (simplified actuarial model)
    base_premium = 100 + (age * 2) + (power_cv * 15) + (annual_mileage * 0.01)
    premium_multiplier = bonus_malus
    if coverage == 'Tous_Risques':
        premium_multiplier *= 1.8
    elif coverage == 'Tous_Risques_Premium':
        premium_multiplier *= 2.2
    elif coverage == 'RC_Tiers_Complet':
        premium_multiplier *= 1.3

    annual_premium = base_premium * premium_multiplier

    # Region risk factor
    region_risk = {
        'Île-de-France': 1.3,
        'Auvergne-Rhône-Alpes': 1.1,
        'Hauts-de-France': 1.2,
        'Provence-Alpes-Côte d\'Azur': 1.25,
        'Grand Est': 1.15
    }
    annual_premium *= region_risk.get(region, 1.0)

    # Payment method
    payment_method = random.choice(['Mensuel', 'Trimestriel', 'Semestriel', 'Annuel'])

    # Risk score (calculated)
    risk_score = 0.3 * (bonus_malus - 0.5) + 0.2 * (prior_claims / 5) + 0.2 * (power_cv / 20) + 0.15 * (age / 85) + 0.15 * (annual_mileage / 50000)

    # Claim in current year (target variable)
    claim_current_year = 1 if (np.random.random() < risk_score * 0.5) else 0

    data.append({
        'policy_id': policy_id,
        'policy_start_date': policy_start.strftime('%Y-%m-%d'),
        'policy_end_date': policy_end.strftime('%Y-%m-%d'),
        'age': age,
        'gender': gender,
        'marital_status': marital_status,
        'profession': profession,
        'region': region,
        'licence_years': licence_years,
        'has_driving_licence': has_licence,
        'car_make': make,
        'car_model': model,
        'car_year': year,
        'car_age': vehicle_age,
        'fuel_type': fuel_type,
        'power_cv': power_cv,
        'usage': usage,
        'annual_mileage': annual_mileage,
        'bonus_malus': bonus_malus,
        'prior_claims_5y': prior_claims,
        'total_claim_amount_5y': total_claim_amount,
        'coverage_type': coverage,
        'annual_premium_eur': round(annual_premium, 2),
        'payment_method': payment_method,
        'risk_score': round(risk_score, 3),
        'claim_current_year': claim_current_year
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
import os
output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, 'professional_car_insurance_dataset.csv')
df.to_csv(output_path, index=False)

print(f"✅ Dataset generated successfully!")
print(f"📊 Total records: {len(df):,}")
print(f"📁 File saved to: {output_path}")
print(f"📂 Directory: {output_dir}")
print(f"\n📈 Dataset statistics:")
print(f"   - Average annual premium: €{df['annual_premium_eur'].mean():.2f}")
print(f"   - Average risk score: {df['risk_score'].mean():.3f}")
print(f"   - Claim rate: {df['claim_current_year'].mean() * 100:.2f}%")
print(f"   - Unique car makes: {df['car_make'].nunique()}")
print(f"   - Unique regions: {df['region'].nunique()}")

print(f"\n📋 Dataset columns ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:2d}. {col}")
