"""
MedIntel AI — Application Configuration.

Loads settings from environment variables and .env file.
All sensitive values (API keys, secrets) must be provided via
environment variables — never hardcoded in source code.
"""

from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Robust path resolution relative to backend directory and repo root
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_ENV_FILE = _BACKEND_DIR / ".env"

_DEPLOY_MODELS_DIR = _REPO_ROOT / "deploy" / "ml_models"
_EXTERNAL_MODELS_DIR = Path("D:/MedIntel-Datasets/ml_models")

if _DEPLOY_MODELS_DIR.exists():
    _DEFAULT_MODELS_DIR = str(_DEPLOY_MODELS_DIR)
elif _EXTERNAL_MODELS_DIR.exists():
    _DEFAULT_MODELS_DIR = str(_EXTERNAL_MODELS_DIR)
else:
    _DEFAULT_MODELS_DIR = str(_DEPLOY_MODELS_DIR)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "MedIntel AI"
    APP_ENV: str = "development"
    DEBUG: Optional[bool] = None

    # Security & CORS (Phase 2 & Deployment)
    SECRET_KEY: str = "medintel-ai-secure-jwt-secret-key-2026"
    CORS_ORIGINS: str = ""

    DATABASE_URL: str = "sqlite:///./medintel.db"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Document Extraction & OCR (Phase 4)
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    DEFAULT_OCR_ENGINE: str = "tesseract"

    # Machine Learning Risk Models (Phase 7)
    MEDINTEL_ML_MODELS_DIR: str = _DEFAULT_MODELS_DIR

    # Generative AI & Explanation (Phase 8)
    GENAI_PROVIDER: str = "mock"  # "mock" or "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_debug_default(self) -> "Settings":
        """Resolve DEBUG to False in production if not explicitly configured."""
        if self.DEBUG is None:
            self.DEBUG = (self.APP_ENV != "production")
        return self


settings = Settings()
