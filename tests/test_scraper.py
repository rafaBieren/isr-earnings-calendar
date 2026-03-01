from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from isr_earnings_calendar.scraper import (
    MAYA_REPORTS_URL,
    REQUEST_TIMEOUT_SECONDS,
    fetch_maya_reports,
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
    assert (
        parsed[0]["source_url"]
        == "https://maya.tase.co.il/he/corporate-actions/financial-scheduled"
    )
    assert parsed[1]["security_id"] == "1267"
    assert parsed[1]["company_name"] == "Dummy Two"
    assert parsed[1]["event_date"] == "2026-03-02T16:30:00"
    assert parsed[1]["event_type"] == "Conference Call"


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
