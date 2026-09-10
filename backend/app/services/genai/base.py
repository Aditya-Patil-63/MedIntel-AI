"""
MedIntel AI — Phase 8: Base GenAI Provider Interface.

Defines the abstract interface for Generative AI explanation and translation
providers. Enforces provider decoupling, data contracts, and safety invariants.

Safety & Prompt-Injection Boundary:
    - All clinical inputs (analytes, measurements, classifications, risk scores)
      must be treated strictly as PASSIVE DATA.
    - Providers MUST NOT accept or execute arbitrary caller-supplied prompts,
      system prompts, or instructions embedded inside OCR extraction strings.
    - Providers MUST NOT formulate clinical diagnoses or prescribe treatments.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from app.schemas.genai import (
    GenAIExplainRequest,
    GenAIExplanationPayload,
    SupportedLanguage,
)


class BaseGenAIProvider(ABC):
    """Abstract base class for all GenAI explanation and translation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique provider identifier (e.g. 'mock', 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name/version used by this provider."""
        pass

    @abstractmethod
    async def generate_explanation(
        self,
        request: GenAIExplainRequest,
    ) -> GenAIExplanationPayload:
        """Generate a structured, non-diagnostic patient explanation from verified inputs.

        Args:
            request: Validated GenAIExplainRequest containing verified findings.

        Returns:
            GenAIExplanationPayload structured educational explanation.

        Raises:
            RuntimeError: If provider execution fails.
        """
        pass

    @abstractmethod
    async def translate_explanation(
        self,
        payload: GenAIExplanationPayload,
        target_language: SupportedLanguage,
    ) -> Tuple[GenAIExplanationPayload, Optional[str]]:
        """Translate a structured explanation while strictly preserving numerical and clinical invariance.

        Invariance Guarantees:
            - Numeric values, units, and ranges MUST remain identical.
            - Deterministic classifications (LOW/NORMAL/HIGH/CRITICAL) MUST remain identical.
            - ML risk probabilities and risk bands MUST remain identical.

        Args:
            payload: Source GenAIExplanationPayload (typically in English).
            target_language: Target SupportedLanguage (en, hi, mr, gu).

        Returns:
            Tuple of (translated_payload, translated_summary_text).
        """
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check provider operational status, connectivity, and configuration."""
        pass
