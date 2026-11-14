"""Validated settings. Secret values are never included in repr or logs."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Cosmos Intelligence"
    log_level: str = "INFO"
    public_base_url: str = "http://localhost:8080"
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://cosmos:cosmos_local_only@localhost:5432/cosmos"
    )
    database_url_file: str | None = None
    db_pool_size: int = 5
    worker_poll_interval_seconds: float = 2.0
    worker_lease_seconds: int = 300
    worker_schedules_enabled: bool = False

    apod_base_url: str = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    neows_base_url: str = "https://api.nasa.gov/neo/rest/v1"
    donki_base_url: str = "https://ccmc.gsfc.nasa.gov/DONKI-API/get"
    eonet_base_url: str = "https://eonet.gsfc.nasa.gov/api/v3"
    nasa_media_base_url: str = "https://images-api.nasa.gov"
    jpl_ssd_base_url: str = "https://ssd-api.jpl.nasa.gov"
    jpl_horizons_base_url: str = "https://ssd.jpl.nasa.gov"
    nasa_api_key: SecretStr = SecretStr("DEMO_KEY")
    nasa_api_key_file: str | None = None
    nasa_api_timeout_seconds: float = 15.0
    nasa_max_concurrency: int = 4
    nasa_max_retries: int = 3
    nasa_max_response_bytes: int = 8_000_000

    openrouter_enabled: bool = False
    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_api_key_file: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = ""
    openrouter_timeout_seconds: float = 30.0
    ai_max_output_tokens: int = 1200
    ai_daily_token_budget: int = 20_000
    nasa_ai_policy_approved: bool = False

    oidc_issuer_url: str = ""
    oidc_audience: str = ""
    oidc_client_id: str = ""
    dev_auth_enabled: bool = False

    cors_allowed_origins: str = ""
    public_rate_limit_per_minute: int = 120
    ai_rate_limit_per_minute: int = 5
    ai_rate_limit_per_day: int = 30
    report_rate_limit_per_hour: int = 3
    caddy_address: str = ":80"

    @model_validator(mode="after")
    def validate_security_settings(self) -> Settings:
        official_hosts = {
            "apod_base_url": "science.nasa.gov",
            "neows_base_url": "api.nasa.gov",
            "donki_base_url": "ccmc.gsfc.nasa.gov",
            "eonet_base_url": "eonet.gsfc.nasa.gov",
            "nasa_media_base_url": "images-api.nasa.gov",
            "jpl_ssd_base_url": "ssd-api.jpl.nasa.gov",
            "jpl_horizons_base_url": "ssd.jpl.nasa.gov",
        }
        for setting_name, expected_host in official_hosts.items():
            parsed = urlsplit(getattr(self, setting_name))
            if (
                parsed.scheme != "https"
                or parsed.hostname != expected_host
                or parsed.port is not None
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(f"{setting_name} must use the official HTTPS service host.")

        openrouter_url = urlsplit(self.openrouter_base_url)
        if (
            openrouter_url.scheme != "https"
            or openrouter_url.hostname != "openrouter.ai"
            or openrouter_url.port is not None
            or openrouter_url.username
            or openrouter_url.password
            or openrouter_url.query
            or openrouter_url.fragment
        ):
            raise ValueError("OPENROUTER_BASE_URL must use the official HTTPS service host.")

        if self.app_env == "production":
            if self.dev_auth_enabled:
                raise ValueError("Development authentication cannot be enabled in production.")
            if not self.database_url_value:
                raise ValueError("Production requires a database URL.")
            if not self.database_url_value.startswith("postgresql+asyncpg://"):
                raise ValueError("Production database URL must use the async PostgreSQL driver.")
            if not self.oidc_issuer_url or not self.oidc_audience:
                raise ValueError("Production requires an OIDC issuer URL and audience.")
            if not self.oidc_issuer_url.startswith("https://"):
                raise ValueError("Production OIDC issuer must use HTTPS.")
            if not self.nasa_api_key_value or self.nasa_api_key_value == "DEMO_KEY":
                raise ValueError("Production requires a privately configured NASA API key.")
        if self.oidc_audience and not self.oidc_issuer_url:
            raise ValueError("OIDC audience cannot be set without an issuer URL.")
        if self.db_pool_size < 1:
            raise ValueError("DB_POOL_SIZE must be positive.")
        if not 0.25 <= self.worker_poll_interval_seconds <= 60:
            raise ValueError("WORKER_POLL_INTERVAL_SECONDS must be between 0.25 and 60.")
        if not 30 <= self.worker_lease_seconds <= 3600:
            raise ValueError("WORKER_LEASE_SECONDS must be between 30 and 3600.")
        if self.nasa_max_concurrency < 1 or self.nasa_max_concurrency > 64:
            raise ValueError("NASA_MAX_CONCURRENCY must be between 1 and 64.")
        if self.nasa_max_response_bytes < 1024:
            raise ValueError("NASA_MAX_RESPONSE_BYTES must be at least 1024.")
        if self.nasa_api_timeout_seconds <= 0:
            raise ValueError("NASA_API_TIMEOUT_SECONDS must be positive.")
        if self.openrouter_timeout_seconds <= 0:
            raise ValueError("OPENROUTER_TIMEOUT_SECONDS must be positive.")
        if self.nasa_max_retries < 0 or self.nasa_max_retries > 5:
            raise ValueError("NASA_MAX_RETRIES must be between 0 and 5.")
        return self

    @property
    def nasa_api_key_value(self) -> str:
        return _read_configured_secret(self.nasa_api_key_file, self.nasa_api_key)

    @property
    def database_url_value(self) -> str:
        return _read_configured_secret(self.database_url_file, self.database_url)

    @property
    def openrouter_api_key_value(self) -> str:
        return _read_configured_secret(self.openrouter_api_key_file, self.openrouter_api_key)

    @property
    def assistant_available(self) -> bool:
        return bool(
            self.openrouter_enabled
            and self.openrouter_api_key_value
            and self.openrouter_model
            and self.nasa_ai_policy_approved
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


def _read_configured_secret(file_path: str | None, value: SecretStr) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return value.get_secret_value().strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if os.environ.get("COSMOS_TEST_MODE", "").casefold() == "true":
        return Settings(_env_file=None)  # type: ignore[call-arg]
    return Settings()
