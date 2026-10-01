"""
MedIntel AI — Phase 8: GenAI Services Package.

Provides Generative AI provider abstraction, mock implementations,
and translation services.
"""

from app.services.genai.base import BaseGenAIProvider
from app.services.genai.mock_provider import MockGenAIProvider

try:
    from app.services.genai.gemini_provider import GeminiProvider
    __all__ = ["BaseGenAIProvider", "MockGenAIProvider", "GeminiProvider"]
except ImportError:
    GeminiProvider = None  # type: ignore
    __all__ = ["BaseGenAIProvider", "MockGenAIProvider"]
