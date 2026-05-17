from __future__ import annotations

import sys
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

sys.modules.setdefault("resend", Mock())

from isr_earnings_calendar.api import app  # noqa: E402


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


def test_view_returns_html() -> None:
    with (
        patch("isr_earnings_calendar.api.BackgroundScheduler.add_job"),
        patch("isr_earnings_calendar.api.sync_reports_job"),
        patch("isr_earnings_calendar.api.sync_offerings_job"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.start"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.shutdown"),
    ):
        with TestClient(app) as client:
            response = client.get("/view")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="calendar"' in response.text
    assert "webcal://" in response.text
    assert "calendar.google.com" in response.text


@patch("isr_earnings_calendar.api.get_all_events")
def test_events_json_shape(mock_get_all_events) -> None:
    call_type = "שיחת ועידה"
    mock_get_all_events.return_value = [
        {
            "id": 1,
            "security_id": "100001",
            "company_name": "Corp A",
            "event_date": "2026-05-02T10:00:00",
            "end_date": "",
            "event_type": call_type,
            "source_url": "http://example.com/1",
            "report_url": "",
            "description": "",
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
            response = client.get("/api/events")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list) and len(payload) == 1
    event = payload[0]
    assert event["title"] == f"Corp A - {call_type}"
    assert event["start"] == "2026-05-02T10:00:00"
    assert event["end"] == "2026-05-02T10:30:00"
    assert event["allDay"] is False
    assert event["extendedProps"]["event_type"] == call_type
    assert event["extendedProps"]["company_name"] == "Corp A"
    assert event["extendedProps"]["source_url"] == "http://example.com/1"


@patch("isr_earnings_calendar.api.get_all_events")
def test_events_json_matches_ics_grouping(mock_get_all_events) -> None:
    earnings_type = "פרסום דוחות"
    mock_get_all_events.return_value = [
        {
            "id": i,
            "security_id": f"10000{i}",
            "company_name": name,
            "event_date": "2026-05-01",
            "event_type": earnings_type,
            "source_url": "",
            "report_url": "",
            "description": "",
        }
        for i, name in enumerate(["Corp A", "Corp B", "Corp C"], start=1)
    ]

    with (
        patch("isr_earnings_calendar.api.BackgroundScheduler.add_job"),
        patch("isr_earnings_calendar.api.sync_reports_job"),
        patch("isr_earnings_calendar.api.sync_offerings_job"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.start"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.shutdown"),
    ):
        with TestClient(app) as client:
            response = client.get("/api/events")

    payload = response.json()
    assert len(payload) == 1
    grouped = payload[0]
    assert grouped["allDay"] is True
    assert grouped["start"] == "2026-05-01"
    assert "Corp A" in grouped["title"]
    assert "Corp B" in grouped["title"]
    assert "Corp C" in grouped["title"]
    assert "(3)" in grouped["title"]


@patch("isr_earnings_calendar.api.process_telegram_update")
def test_telegram_webhook_accepts_update(mock_process_telegram_update) -> None:
    update_payload = {"message": {"chat": {"id": 123}, "text": "hello"}}

    with (
        patch("isr_earnings_calendar.api.BackgroundScheduler.add_job"),
        patch("isr_earnings_calendar.api.sync_reports_job"),
        patch("isr_earnings_calendar.api.sync_offerings_job"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.start"),
        patch("isr_earnings_calendar.api.BackgroundScheduler.shutdown"),
    ):
        with TestClient(app) as client:
            response = client.post("/telegram/webhook", json=update_payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_process_telegram_update.assert_called_once_with(update_payload)
