from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from isr_earnings_calendar.api import app


@patch("isr_earnings_calendar.api.get_all_events")
def test_get_calendar_returns_ics(mock_get_all_events) -> None:
    earnings_type = "\u05e4\u05e8\u05e1\u05d5\u05dd \u05d3\u05d5\u05d7\u05d5\u05ea"
    call_type = "\u05e9\u05d9\u05d7\u05ea \u05d5\u05e2\u05d9\u05d3\u05d4"
    mock_get_all_events.return_value = [
        {
            "id": 1,
            "security_id": "100001",
            "company_name": "Corp A",
            "event_date": "2026-05-01",
            "event_type": earnings_type,
            "source_url": "http://example.com/1",
            "report_url": "",
        },
        {
            "id": 2,
            "security_id": "100002",
            "company_name": "Corp B",
            "event_date": "2026-05-01",
            "event_type": earnings_type,
            "source_url": "http://example.com/2",
            "report_url": "",
        },
        {
            "id": 3,
            "security_id": "100003",
            "company_name": "Corp C",
            "event_date": "2026-05-02T10:00:00",
            "end_date": "",
            "event_type": call_type,
            "source_url": "http://example.com/3",
            "report_url": "https://maya.tase.co.il/reports/details/12345",
        },
        {
            "id": 4,
            "security_id": "100004",
            "company_name": "Corp D",
            "event_date": "2026-05-02T11:00:00",
            "end_date": "2026-05-02T12:00:00",
            "event_type": call_type,
            "source_url": "http://example.com/4",
            "report_url": "",
        },
    ]

    with (
        patch("isr_earnings_calendar.api.BackgroundScheduler.add_job"),
        patch("isr_earnings_calendar.api.sync_reports_job"),
        patch("isr_earnings_calendar.api.sync_offerings_job"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.start"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.shutdown"),
    ):
        with TestClient(app) as client:
            response = client.get("/calendar")

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in response.text
    unfolded_text = response.text.replace("\r\n ", "").replace("\\,", ",")
    summary_expected = (
        "SUMMARY:\u05d3\u05d5\u05d7\u05d5\u05ea \u05dc\u05d4\u05d9\u05d5\u05dd "
        "(2): Corp A, Corp B"
    )
    assert summary_expected in unfolded_text
    assert "Corp A" in unfolded_text
    assert "Corp B" in unfolded_text
    assert "DTEND:20260502T103000" in unfolded_text
    assert "DTEND:20260502T120000" in unfolded_text
    assert "https://maya.tase.co.il/reports/details/12345" in unfolded_text
