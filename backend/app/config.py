from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHIELDMATE_",
        env_file=BACKEND_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    environment: Literal["development", "test", "production", "local_release"] = "development"
    database_url: str = "sqlite:///./storage/shieldmate.db"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "backend"]
    cors_origins: list[str] = []

    cookie_secure: bool = False
    trusted_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    session_seconds: int = 28800
    auth_rate_limit: int = 10
    domain_quota: int = 5
    challenge_seconds: int = 172800
    verification_seconds: int = 2592000
    dns_timeout: float = 3.0
    domain_rate_limit: int = 20
    domain_ip_rate_limit: int = 100
    scan_user_hourly: int = 6
    scan_org_hourly: int = 6
    scan_domain_hourly: int = 2
    scan_queue_limit: int = 20
    scan_history_limit: int = 100
    scan_timeout: float = 45.0
    scan_io_timeout: float = 3.0
    finding_stale_seconds: int = 604800

    @model_validator(mode="after")
    def secure_production(self) -> "Settings":
        if self.environment == "production" and (
            not self.trusted_origins
            or not self.cookie_secure
            or any(not x.startswith("https://") for x in self.trusted_origins)
        ):
            raise ValueError("Production requires Secure cookies and HTTPS trusted origins")
        if self.environment == "local_release":
            if (
                self.cookie_secure
                or self.cors_origins
                or not self.trusted_origins
                or self.database_url.endswith(":memory:")
                or any(
                    host not in {"localhost", "127.0.0.1", "backend"} for host in self.allowed_hosts
                )
                or any(
                    urlsplit(origin).scheme != "http"
                    or urlsplit(origin).hostname not in {"localhost", "127.0.0.1"}
                    or urlsplit(origin).port is None
                    for origin in self.trusted_origins
                )
            ):
                raise ValueError(
                    "Local release requires loopback HTTP origins, file storage and no CORS"
                )
        if not 60 <= self.session_seconds <= 604800 or not 1 <= self.auth_rate_limit <= 100:
            raise ValueError("Invalid authentication limits")
        if not (
            1 <= self.domain_quota <= 100
            and 60 <= self.challenge_seconds <= 604800
            and 60 <= self.verification_seconds <= 7776000
            and 0.1 <= self.dns_timeout <= 5
            and 1 <= self.domain_rate_limit <= 100
            and 1 <= self.domain_ip_rate_limit <= 1000
        ):
            raise ValueError("Invalid domain limits")
        if not (
            1 <= self.scan_user_hourly <= 100
            and 1 <= self.scan_org_hourly <= 100
            and 1 <= self.scan_domain_hourly <= 20
            and 1 <= self.scan_queue_limit <= 100
            and 1 <= self.scan_history_limit <= 1000
            and 5 <= self.scan_timeout <= 60
            and 0.1 <= self.scan_io_timeout <= 5
        ):
            raise ValueError("Invalid scan limits")
        if not 60 <= self.finding_stale_seconds <= 7776000:
            raise ValueError("Invalid finding freshness policy")
        return self

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: str) -> str:
        url = make_url(value)
        if url.drivername != "sqlite" or url.host or not url.database:
            raise ValueError("Phase 00 requires a local SQLite database")
        if url.database != ":memory:" and not Path(url.database).is_absolute():
            url = url.set(database=str((BACKEND_ROOT / url.database).resolve()))
        return url.render_as_string(hide_password=False)

    @field_validator("allowed_hosts")
    @classmethod
    def validate_hosts(cls, values: list[str]) -> list[str]:
        if not values or any(not host or any(char in host for char in "*/:@ ") for host in values):
            raise ValueError("Supply explicit hostnames without wildcards, ports or schemes")
        return values

    @field_validator("cors_origins", "trusted_origins")
    @classmethod
    def validate_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            origin = urlsplit(value)
            port = origin.port  # Parse/range-check ports rather than accepting malformed origins.
            if (
                any(ord(c) < 33 or ord(c) > 126 for c in value)
                or (port is not None and port == 0)
                or origin.scheme not in {"http", "https"}
                or not origin.hostname
                or origin.username
                or origin.password
                or origin.path
                or origin.query
                or origin.fragment
                or "*" in value
            ):
                raise ValueError("CORS requires explicit HTTP(S) origins without paths")
        return values
