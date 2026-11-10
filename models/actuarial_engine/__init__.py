"""
Moteur Actuariel UIP
Module de calcul actuariel combinant fréquence et sévérité.
"""

from .actuarial_engine import actuarial_engine, ActuarialEngine
from .prediction import predict_single_contract, predict_batch_contracts
from .uncertainty import calculate_premium_uncertainty, calculate_premium_uncertainty_safe
from .explainability import explain_prediction, get_model_coefficients

__all__ = [
    "actuarial_engine",
    "ActuarialEngine",
    "predict_single_contract",
    "predict_batch_contracts",
    "calculate_premium_uncertainty",
    "calculate_premium_uncertainty_safe",
    "explain_prediction",
    "get_model_coefficients"
]
