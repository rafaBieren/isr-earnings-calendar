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


@patch("isr_earnings_calendar.scraper.requests.get")
def test_fetch_and_parse_success(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "reports": [
            {
                "security_id": "12345",
                "company_name": "Example Co",
                "event_date": "2026-03-01",
                "event_type": "earnings",
                "source_url": "https://maya.tase.co.il/company/12345",
            }
        ]
    }
    mock_get.return_value = mock_response

    raw = fetch_maya_reports("2026-03-01")
    parsed = parse_maya_reports(raw)

    mock_get.assert_called_once_with(
        MAYA_REPORTS_URL,
        params={"date": "2026-03-01"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    assert len(parsed) == 1
    assert parsed[0]["security_id"] == "12345"
    assert parsed[0]["company_name"] == "Example Co"
    assert parsed[0]["event_date"] == "2026-03-01"
    assert parsed[0]["event_type"] == "earnings"
    assert parsed[0]["source_url"] == "https://maya.tase.co.il/company/12345"


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.Timeout("timeout"),
        requests.exceptions.HTTPError("server error"),
    ],
)
@patch("isr_earnings_calendar.scraper.requests.get")
def test_fetch_handles_request_errors_gracefully(
    mock_get: MagicMock, error: requests.exceptions.RequestException
) -> None:
    mock_get.side_effect = error

    raw = fetch_maya_reports("2026-03-01")
    parsed = parse_maya_reports(raw)

    assert raw == {"reports": []}
    assert parsed == []
