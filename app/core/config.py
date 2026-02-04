"""
Configuration settings for the application.
"""
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_schema(cls, v: str) -> str:
        """Ensure DATABASE_URL uses the asyncpg driver and fix common cloud prefixes."""
        if v and (v.startswith("postgres://") or v.startswith("postgresql://")):
            if "+asyncpg" not in v:
                return v.replace("://", "+asyncpg://", 1)
        return v

    # JWT Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Application
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
