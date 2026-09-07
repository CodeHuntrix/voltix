from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    app_name: str = "Voltix API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+asyncpg://voltix:voltix@localhost:5432/voltix"
    )
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-change-me-voltix-jwt-secret-32chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    cors_origins: str = "http://localhost:5173,http://localhost:8081,http://127.0.0.1:5173"
    edge_ingest_api_key: str = "voltix-edge-dev-key"
    tariff_default_inr_per_kwh: float = 8.5
    model_version: str = "rules-v1"
    pulse_waste_seconds: int | None = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
