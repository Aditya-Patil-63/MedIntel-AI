"""
MedIntel AI — Application Configuration.

Loads settings from environment variables and .env file.
All sensitive values (API keys, secrets) must be provided via
environment variables — never hardcoded in source code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        APP_NAME: Display name for the application.
        APP_ENV: Current environment (development, staging, production).
        DEBUG: Enable debug mode.
        DATABASE_URL: SQLAlchemy database connection string.
        HOST: Server bind host.
        PORT: Server bind port.
    """

    APP_NAME: str = "MedIntel AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./medintel.db"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Document Extraction & OCR (Phase 4)
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    DEFAULT_OCR_ENGINE: str = "tesseract"

    # Machine Learning Risk Models (Phase 7)
    MEDINTEL_ML_MODELS_DIR: str = "D:\\MedIntel-Datasets\\ml_models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
