from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq API
    GROQ_API_KEY: str = ""
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.3

    # Scoring weights (must sum to 1.0)
    WEIGHT_RELEVANCE: float = 0.25
    WEIGHT_ACCURACY: float = 0.30
    WEIGHT_HALLUCINATION: float = 0.25
    WEIGHT_COMPLETENESS: float = 0.20

    # Rate limiting for batch processing
    BATCH_DELAY_SECONDS: float = 2.0
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 5.0

    # Database
    DATABASE_URL: str = "evaluations.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
