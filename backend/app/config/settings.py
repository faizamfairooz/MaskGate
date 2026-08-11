import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database Configuration (set in .env for local development)
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "maskgate_test"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.3

    # Security (optional for MVP; no auth enabled)
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
