from __future__ import annotations

from typing import Any

import requests

MAYA_REPORTS_URL = (
    "https://maya.tase.co.il/api/v1/corporate-actions/financial-reports-schedule"
)
MAYA_FINANCIAL_SCHEDULED_URL = (
    "https://maya.tase.co.il/he/corporate-actions/financial-scheduled"
)
REQUEST_TIMEOUT_SECONDS = 10


def fetch_maya_reports(report_date: str) -> list[dict[str, Any]]:
    _ = report_date
    try:
        response = requests.post(
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
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return payload
        return []
    except requests.exceptions.RequestException:
        return []
    except ValueError:
        return []


def parse_maya_reports(raw_data: Any) -> list[dict[str, str | None]]:
    if not isinstance(raw_data, list):
        return []

    parsed_events: list[dict[str, str | None]] = []
    for report in raw_data:
        if not isinstance(report, dict):
            continue

        company_id = report.get("companyId")
        company_name = str(report.get("companyName") or "")
        event_type = str(report.get("eventName") or "")

        scheduled_date = report.get("scheduledDate")
        if not scheduled_date:
            continue
        date_str = str(scheduled_date)
        date_part = date_str.split("T")[0]

        scheduled_time = report.get("scheduledTime")
        if scheduled_time:
            time_str = str(scheduled_time)
            if len(time_str) == 5:
                time_str = f"{time_str}:00"
            event_date = f"{date_part}T{time_str}"
        else:
            event_date = date_str

        if company_id is None or not company_name or not event_type:
            continue

        parsed_events.append(
            {
                "security_id": str(company_id),
                "company_name": company_name,
                "event_date": event_date,
                "event_type": event_type,
                "source_url": MAYA_FINANCIAL_SCHEDULED_URL,
            }
        )

    return parsed_events
