"""
MedIntel AI — Base ML Model Wrapper.

Phase 7: Abstract base class for disease risk models ensuring uniform
validation, prediction signatures, and non-diagnostic probability formatting.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from ml.common.schemas import ModelRiskResult


class BaseRiskModel(ABC):
    """Abstract interface for all MedIntel AI disease risk estimation models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Unique model identifier."""
        pass

    @property
    @abstractmethod
    def condition(self) -> str:
        """Target condition (diabetes, heart_disease, kidney_disease)."""
        pass

    @property
    @abstractmethod
    def feature_names(self) -> List[str]:
        """Ordered list of required predictor feature names."""
        pass

    @abstractmethod
    def predict_risk(
        self,
        features: Union[Dict[str, Any], pd.DataFrame, pd.Series],
        threshold: float = 0.50,
    ) -> ModelRiskResult:
        """
        Estimate disease risk probability from patient input features.

        Enforces missing-feature validation and returns structured risk results.
        """
        pass
