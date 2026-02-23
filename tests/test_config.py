from __future__ import annotations

import pytest

from isr_earnings_calendar.config import MissingEnvironmentVariableError, load_settings


def test_load_settings_fails_fast_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ISR_EARNINGS_DB_PATH", raising=False)
    monkeypatch.delenv("ISR_EARNINGS_MAYA_BASE_URL", raising=False)

    with pytest.raises(MissingEnvironmentVariableError):
        load_settings()


def test_load_settings_reads_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ISR_EARNINGS_DB_PATH", "./tmp/test.db")
    monkeypatch.setenv("ISR_EARNINGS_MAYA_BASE_URL", "https://maya.tase.co.il")

    settings = load_settings()

    assert settings.db_path == "./tmp/test.db"
    assert settings.maya_base_url == "https://maya.tase.co.il"
