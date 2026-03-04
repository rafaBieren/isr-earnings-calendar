from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

MAYA_REPORTS_URL = (
    "https://maya.tase.co.il/api/v1/corporate-actions/financial-reports-schedule"
)
MAYA_FINANCIAL_SCHEDULED_URL = (
    "https://maya.tase.co.il/he/corporate-actions/financial-scheduled"
)
MAYA_OPEN_OFFERINGS_URL = "https://maya.tase.co.il/api/v1/offerings/open"
MAYA_OFFERINGS_URL = "https://maya.tase.co.il/he/offerings"
REQUEST_TIMEOUT_SECONDS = 10


def _normalize_time(time_str: str) -> str:
    stripped = time_str.strip()
    try:
        upper_value = stripped.upper()
        if "AM" in upper_value or "PM" in upper_value:
            return datetime.strptime(upper_value, "%I:%M %p").strftime("%H:%M:%S")
        if len(stripped) == 5:
            return f"{stripped}:00"
        return stripped
    except ValueError:
        return time_str


def fetch_maya_reports(report_date: str | None = None) -> list[dict[str, Any]]:
    _ = report_date
    try:
        all_raw_events: list[dict[str, Any]] = []
        page = 1
        while True:
            payload = {"pageSize": 20, "pageNumber": page}
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
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or not data:
                break

            all_raw_events.extend(data)
            if len(data) < 20:
                break

            page += 1

        return all_raw_events
    except requests.exceptions.RequestException:
        return []
    except ValueError:
        return []


def fetch_open_offerings() -> list:
    scheme = "https://"
    domain = "maya.tase.co.il"
    api_url = scheme + domain + "/api/v1/offerings/open"
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0",
        "referer": scheme + domain + "/he/offerings",
        "x-maya-with": "Bursa",
    }

    parsed_offerings = []
    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                company_name = item.get("companyName", "")
                offer_type = item.get("offerType", "")
                price = item.get("pricePerUnit", "")
                qty = item.get("minOfferedUnits", "")
                report_id = item.get("reportId", "")

                desc_lines = [
                    f"סוג מכרז: {offer_type}",
                    f"מחיר ליחידה: {price}",
                    f"כמות יחידות מוצעות: {qty}",
                ]

                parsed_offerings.append(
                    {
                        "security_id": str(item.get("offerNumber", "")),
                        "company_name": f"הנפקה ציבורית - {company_name}",
                        "event_date": item.get("beginAt", ""),
                        "end_date": item.get("endAt", ""),
                        "event_type": "הנפקה ציבורית",
                        "description": "\n\n".join(desc_lines),
                        "report_url": (
                            f"{scheme}{domain}/reports/details/{report_id}"
                            if report_id
                            else ""
                        ),
                        "source_url": f"{scheme}{domain}/he/offerings",
                    }
                )
    except Exception as e:
        print(f"Error fetching offerings: {e}")

    return parsed_offerings


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
        report_id_raw = report.get("reportId")
        try:
            report_id_val = int(report_id_raw) if report_id_raw else None
        except (ValueError, TypeError):
            report_id_val = None

        scheduled_date = report.get("scheduledDate")
        if not scheduled_date:
            continue
        date_str = str(scheduled_date)
        date_part = date_str.split("T")[0]

        scheduled_time = report.get("scheduledTime")
        if scheduled_time:
            time_str = _normalize_time(str(scheduled_time))
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
                "report_url": (
                    f"https://maya.tase.co.il/reports/details/{report_id_val}"
                    if report_id_val
                    else ""
                ),
            }
        )

    return parsed_events
