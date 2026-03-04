from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from isr_earnings_calendar.scraper import (
    MAYA_OPEN_OFFERINGS_URL,
    MAYA_OFFERINGS_URL,
    MAYA_REPORTS_URL,
    REQUEST_TIMEOUT_SECONDS,
    fetch_maya_reports,
    fetch_open_offerings,
    parse_maya_reports,
)


@patch("isr_earnings_calendar.scraper.requests.post")
def test_fetch_and_parse_success(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "id": 114,
            "scheduledDate": "2026-03-01T00:00:00",
            "eventName": "Earnings Report",
            "companyId": 1266,
            "companyName": "Dummy",
            "scheduledTime": None,
            "reportId": None,
        },
        {
            "id": 115,
            "scheduledDate": "2026-03-02T00:00:00",
            "eventName": "Conference Call",
            "companyId": 1267,
            "companyName": "Dummy Two",
            "scheduledTime": "04:30 PM",
            "reportId": 12345,
        },
    ]
    mock_post.return_value = mock_response

    raw = fetch_maya_reports("2026-03-01")
    parsed = parse_maya_reports(raw)

    mock_post.assert_called_once_with(
        MAYA_REPORTS_URL,
        headers={
            "accept": "application/json",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        },
        json={"pageSize": 20, "pageNumber": 1},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    assert len(parsed) == 2
    assert parsed[0]["security_id"] == "1266"
    assert parsed[0]["company_name"] == "Dummy"
    assert parsed[0]["event_date"] == "2026-03-01T00:00:00"
    assert parsed[0]["event_type"] == "Earnings Report"
    assert parsed[0]["report_url"] == ""
    assert (
        parsed[0]["source_url"]
        == "https://maya.tase.co.il/he/corporate-actions/financial-scheduled"
    )
    assert parsed[1]["security_id"] == "1267"
    assert parsed[1]["company_name"] == "Dummy Two"
    assert parsed[1]["event_date"] == "2026-03-02T16:30:00"
    assert parsed[1]["event_type"] == "Conference Call"
    assert parsed[1]["report_url"] == "https://maya.tase.co.il/reports/details/12345"


@patch("isr_earnings_calendar.scraper.requests.get")
def test_fetch_open_offerings_success(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "offerNumber": 6660039,
            "reportId": 1725506,
            "beginAt": "2026-03-04T08:30:00",
            "endAt": "2026-03-04T15:30:00",
            "companyName": "לוזון אשראי",
            "offerType": "מחיר",
            "minOfferedUnits": 2250000,
            "pricePerUnit": 57,
        }
    ]
    mock_get.return_value = mock_response

    parsed = fetch_open_offerings()

    mock_get.assert_called_once_with(
        MAYA_OPEN_OFFERINGS_URL,
        headers={
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0",
            "referer": MAYA_OFFERINGS_URL,
            "x-maya-with": "Bursa",
        },
        timeout=15,
    )
    assert parsed == [
        {
            "security_id": "6660039",
            "company_name": "הנפקה ציבורית - לוזון אשראי",
            "event_date": "2026-03-04T08:30:00",
            "end_date": "2026-03-04T15:30:00",
            "event_type": "הנפקה ציבורית",
            "description": (
                "סוג מכרז: מחיר\n\nמחיר ליחידה: 57\n\nכמות יחידות מוצעות: "
                '2250000\n\nקישור לדו"ח ההצעה: '
                "https://maya.tase.co.il/reports/details/1725506"
            ),
            "source_url": "https://maya.tase.co.il/he/offerings",
            "report_url": "https://maya.tase.co.il/reports/details/1725506",
        }
    ]


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.Timeout("timeout"),
        requests.exceptions.HTTPError("server error"),
    ],
)
@patch("isr_earnings_calendar.scraper.requests.post")
def test_fetch_handles_request_errors_gracefully(
    mock_post: MagicMock, error: requests.exceptions.RequestException
) -> None:
    mock_post.side_effect = error

    raw = fetch_maya_reports("2026-03-01")
    parsed = parse_maya_reports(raw)

    assert raw == []
    assert parsed == []
