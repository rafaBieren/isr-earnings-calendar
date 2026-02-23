from __future__ import annotations

import os
from dataclasses import dataclass

REQUIRED_ENV_VARS = (
    "ISR_EARNINGS_DB_PATH",
    "ISR_EARNINGS_MAYA_BASE_URL",
)


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when a required environment variable is missing or empty."""


def _read_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise MissingEnvironmentVariableError(f"Missing required env var: {name}")
    return value.strip()


@dataclass(frozen=True, slots=True)
class Settings:
    db_path: str
    maya_base_url: str


def load_settings() -> Settings:
    return Settings(
        db_path=_read_required_env("ISR_EARNINGS_DB_PATH"),
        maya_base_url=_read_required_env("ISR_EARNINGS_MAYA_BASE_URL"),
    )
