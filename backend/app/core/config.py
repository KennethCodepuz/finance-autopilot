import re
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

    @field_validator("database_url", mode="after")
    @classmethod
    def sanitize_database_url(cls, v: str) -> str:
        """Fixes Neon / PostgreSQL URL query parameters for asyncpg compatibility."""
        if "sslmode=" in v:
            v = v.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer").replace("sslmode=disable", "ssl=disable")
        if "channel_binding=" in v:
            v = re.sub(r"[?&]channel_binding=[^&]+", "", v)
        return v

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Plaid
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str = "sandbox"

    # LLM
    openai_api_key: str

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # App
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
