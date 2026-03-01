from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from isr_earnings_calendar.api import app


@patch("isr_earnings_calendar.api.get_all_events")
def test_get_calendar_returns_ics(mock_get_all_events) -> None:
    mock_get_all_events.return_value = [
        {
            "id": 1,
            "security_id": "100001",
            "company_name": "Corp A",
            "event_date": "2026-05-01",
            "event_type": "פרסום דוחות",
            "source_url": "http://example.com/1",
        },
        {
            "id": 2,
            "security_id": "100002",
            "company_name": "Corp B",
            "event_date": "2026-05-01",
            "event_type": "פרסום דוחות",
            "source_url": "http://example.com/2",
        },
        {
            "id": 3,
            "security_id": "100003",
            "company_name": "Corp C",
            "event_date": "2026-05-02T10:00:00",
            "event_type": "שיחת ועידה",
            "source_url": "http://example.com/3",
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
    unfolded_text = response.text.replace("\r\n ", "").replace("\\,", ",")
    assert "SUMMARY:דוחות להיום (2): Corp A, Corp B" in unfolded_text
    assert "Corp A" in unfolded_text
    assert "Corp B" in unfolded_text
    assert "DTEND:20260502T103000" in unfolded_text
