"""
Non-Linear ML Benchmark Model using XGBoost.
Serves as an empirical baseline against the classical GLM frequency/severity models.
Evaluated via RMSE, MAE, and deviance.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error


class XGBoostBenchmarkModel:
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.is_fitted = False
        self.metrics: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y_loss: pd.Series):
        """
        Fits an XGBoost regressor predicting total claim loss.
        """
        self.feature_names = list(X.columns)
        
        self.model = xgb.XGBRegressor(
            n_estimators=30,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=1
        )
        self.model.fit(X, y_loss)
        self.is_fitted = True

        preds = self.model.predict(X)
        rmse = float(np.sqrt(mean_squared_error(y_loss, preds)))
        mae = float(mean_absolute_error(y_loss, preds))

        importances = dict(zip(self.feature_names, [float(x) for x in self.model.feature_importances_]))
        sorted_imp = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

        self.metrics = {
            "model_type": "XGBoost Regressor (Benchmark)",
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "feature_importances": sorted_imp,
            "n_observations": int(len(X))
        }
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted or self.model is None:
            raise RuntimeError("XGBoost model must be fitted before predict.")
        X_aligned = X.reindex(columns=self.feature_names, fill_value=0.0)
        return self.model.predict(X_aligned)

    def get_summary(self) -> Dict[str, Any]:
        return self.metrics
