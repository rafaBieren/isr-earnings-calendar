from __future__ import annotations

from unittest.mock import patch

from isr_earnings_calendar.db import connect, count_events
from isr_earnings_calendar.sync import sync_maya_events


@patch("isr_earnings_calendar.sync.fetch_maya_reports")
def test_sync_inserts_and_is_idempotent(mock_fetch, tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "sync_events.db"
    monkeypatch.setenv("ISR_EARNINGS_DB_PATH", str(db_path))
    monkeypatch.setenv("ISR_EARNINGS_MAYA_BASE_URL", "https://maya.tase.co.il")

    dummy_raw_data = {
        "reports": [
            {
                "security_id": "11111",
                "company_name": "Alpha Ltd",
                "event_date": "2026-03-01",
                "event_type": "earnings",
                "source_url": "https://maya.tase.co.il/company/11111",
            },
            {
                "security_id": "22222",
                "company_name": "Beta Ltd",
                "event_date": "2026-03-01",
                "event_type": "conference_call",
                "source_url": "https://maya.tase.co.il/company/22222",
            },
        ]
    }
    mock_fetch.return_value = dummy_raw_data

    sync_maya_events("2026-03-01")

    connection = connect(str(db_path))
    try:
        assert count_events(connection) == 2
    finally:
        connection.close()

    sync_maya_events("2026-03-01")

    connection = connect(str(db_path))
    try:
        assert count_events(connection) == 2
    finally:
        connection.close()
