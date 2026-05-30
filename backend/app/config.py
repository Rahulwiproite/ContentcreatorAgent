from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MIN: int = 60 * 24 * 30
    TOKEN_ENCRYPTION_KEY: str = ""

    DATABASE_URL: str = "sqlite:///./comedy_agent.db"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    AI_PROVIDER: str = ""  # "gemini" | "claude" | "" (auto)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL_IDEATION: str = "claude-sonnet-4-20250514"
    CLAUDE_MODEL_FAST: str = "claude-haiku-4-20250514"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_IDEATION: str = "gemini-2.0-flash"
    GEMINI_MODEL_FAST: str = "gemini-2.0-flash-lite"

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_REDIRECT_URI: str = "http://localhost:8000/social/instagram/callback"

    X_CLIENT_ID: str = ""
    X_CLIENT_SECRET: str = ""
    X_BEARER_TOKEN: str = ""
    X_REDIRECT_URI: str = "http://localhost:8000/social/twitter/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
