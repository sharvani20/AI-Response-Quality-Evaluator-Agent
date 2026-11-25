from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API — supports both Groq and OpenAI
    # For Groq: set GROQ_API_KEY
    # For OpenAI: set OPENAI_API_KEY
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # LLM Provider: "groq" or "openai"
    LLM_PROVIDER: str = "groq"

    # Model names
    # Groq options:  "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"
    # OpenAI options: "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"
    MODEL_NAME: str = "llama3-70b-8192"

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
