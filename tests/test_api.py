from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from isr_earnings_calendar.api import app


@patch("isr_earnings_calendar.api.get_all_events")
def test_get_calendar_returns_ics(mock_get_all_events) -> None:
    mock_get_all_events.return_value = [
        {
            "id": 1,
            "security_id": "111111",
            "company_name": "Dummy Corp A",
            "event_date": "2026-04-01",
            "event_type": "Earnings",
            "source_url": "http://example.com/1",
        },
        {
            "id": 2,
            "security_id": "222222",
            "company_name": "Dummy Corp B",
            "event_date": "2026-04-02",
            "event_type": "Conference Call",
            "source_url": "http://example.com/2",
        },
    ]

    with (
        patch("isr_earnings_calendar.api.BackgroundScheduler.add_job"),
        patch("isr_earnings_calendar.api.sync_maya_events"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.start"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.shutdown"),
    ):
        with TestClient(app) as client:
            response = client.get("/calendar")

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in response.text
    assert "Dummy Corp A" in response.text
