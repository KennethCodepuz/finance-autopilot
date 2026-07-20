from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

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
