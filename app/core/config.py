"""
Configuration settings for the application.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator, computed_field
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

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
    
    # Store as string, parse via property
    CORS_ORIGINS_STR: str = '["http://localhost:3000"]'

    @computed_field
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or comma-separated values."""
        v = self.CORS_ORIGINS_STR
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        # Fall back to comma-separated
        return [origin.strip() for origin in v.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
