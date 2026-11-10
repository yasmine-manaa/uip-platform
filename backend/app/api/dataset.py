"""
Dataset statistics API endpoints for freMTPL2 real data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import pandas as pd

from app.database import get_db
from app.actuarial.fre_mtpl2_loader import fre_mtpl2_loader

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/stats", response_model=dict)
def get_dataset_stats(db: Session = Depends(get_db)):
    """
    Returns real statistics from the freMTPL2 dataset.
    """
    try:
        stats = fre_mtpl2_loader.get_statistics()
        
        # Convert numpy types to Python native types
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_native(v) for v in obj]
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            else:
                return obj
        
        stats = convert_to_native(stats)
        
        # Add more detailed statistics
        if fre_mtpl2_loader.merged_df is not None:
            df = fre_mtpl2_loader.merged_df
            
            # Feature statistics
            feature_stats = {
                'driver_age': {
                    'mean': float(df['DrivAge'].mean()),
                    'std': float(df['DrivAge'].std()),
                    'min': int(df['DrivAge'].min()),
                    'max': int(df['DrivAge'].max()),
                },
                'vehicle_power': {
                    'mean': float(df['VehPower'].mean()),
                    'std': float(df['VehPower'].std()),
                    'min': int(df['VehPower'].min()),
                    'max': int(df['VehPower'].max()),
                },
                'vehicle_age': {
                    'mean': float(df['VehAge'].mean()),
                    'std': float(df['VehAge'].std()),
                    'min': int(df['VehAge'].min()),
                    'max': int(df['VehAge'].max()),
                },
                'bonus_malus': {
                    'mean': float(df['BonusMalus'].mean()),
                    'std': float(df['BonusMalus'].std()),
                    'min': int(df['BonusMalus'].min()),
                    'max': int(df['BonusMalus'].max()),
                },
                'area_density': {
                    'mean': float(df['Density'].mean()),
                    'std': float(df['Density'].std()),
                    'min': int(df['Density'].min()),
                    'max': int(df['Density'].max()),
                },
            }
            
            # Claim statistics
            claim_stats = {
                'total_claims': int(df['ClaimNb'].sum()),
                'avg_claims_per_policy': float(df['ClaimNb'].mean()),
                'claim_frequency': float((df['ClaimNb'] > 0).mean()),
                'total_claim_amount': float(df['ClaimAmount'].sum()),
                'avg_claim_amount': float(df['ClaimAmount'].mean()),
                'max_claim_amount': float(df['ClaimAmount'].max()),
            }
            
            # Top regions
            top_regions = {str(k): int(v) for k, v in df['Region'].value_counts().head(10).items()}
            
            # Top brands
            top_brands = {str(k): int(v) for k, v in df['VehBrand'].value_counts().head(10).items()}
            
            return convert_to_native({
                **stats,
                'feature_stats': feature_stats,
                'claim_stats': claim_stats,
                'top_regions': top_regions,
                'top_brands': top_brands,
                'dataset_source': 'freMTPL2 (real data)',
                'total_records': len(df),
            })
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset stats: {str(e)}")


@router.get("/sample", response_model=dict)
def get_dataset_sample(n: int = 10, db: Session = Depends(get_db)):
    """
    Returns a sample of the freMTPL2 dataset.
    """
    try:
        sample = fre_mtpl2_loader.get_sample(n)
        
        # Convert to native types
        sample_data = sample.to_dict('records')
        
        return {
            "sample_size": len(sample_data),
            "columns": list(sample.columns),
            "data": sample_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset sample: {str(e)}")
