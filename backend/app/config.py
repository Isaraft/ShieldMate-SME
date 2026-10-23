from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator
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

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./storage/shieldmate.db"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "backend"]
    cors_origins: list[str] = []

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

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            origin = urlsplit(value)
            if (
                origin.scheme not in {"http", "https"}
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
