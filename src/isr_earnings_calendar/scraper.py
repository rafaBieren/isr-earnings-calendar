from __future__ import annotations

from typing import Any

import requests

MAYA_REPORTS_URL = "https://maya.tase.co.il/api/reports"
REQUEST_TIMEOUT_SECONDS = 10


def fetch_maya_reports(report_date: str) -> dict[str, Any]:
    try:
        response = requests.get(
            MAYA_REPORTS_URL,
            params={"date": report_date},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {"reports": []}
    except requests.exceptions.RequestException:
        return {"reports": []}
    except ValueError:
        return {"reports": []}


def parse_maya_reports(raw_data: Any) -> list[dict[str, str | None]]:
    reports: list[Any]
    if isinstance(raw_data, dict):
        reports = raw_data.get("reports", [])
    elif isinstance(raw_data, list):
        reports = raw_data
    else:
        reports = []

    parsed_events: list[dict[str, str | None]] = []
    for report in reports:
        if not isinstance(report, dict):
            continue

        security_id = str(report.get("security_id") or report.get("securityId") or "")
        company_name = str(
            report.get("company_name") or report.get("companyName") or ""
        )
        event_date = str(report.get("event_date") or report.get("eventDate") or "")
        event_type = str(report.get("event_type") or report.get("eventType") or "")
        source_url = report.get("source_url") or report.get("sourceUrl")

        if not security_id or not company_name or not event_date or not event_type:
            continue

        parsed_events.append(
            {
                "security_id": security_id,
                "company_name": company_name,
                "event_date": event_date,
                "event_type": event_type,
                "source_url": source_url,
            }
        )

    return parsed_events
