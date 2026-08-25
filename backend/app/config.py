from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/embedded"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()