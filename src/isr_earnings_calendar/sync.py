from __future__ import annotations

import logging
from datetime import date as datetime_date

from .config import load_settings
from .db import Event, connect, initialize_schema, upsert_event
from .scraper import fetch_maya_reports, parse_maya_reports

logger = logging.getLogger(__name__)


def sync_maya_events(date: str | None = None) -> int:
    target_date = date or datetime_date.today().isoformat()
    settings = load_settings()

    try:
        raw_data = fetch_maya_reports(target_date)
        parsed_events = parse_maya_reports(raw_data)
    except Exception:
        logger.exception(
            "Failed to fetch or parse Maya reports for date=%s", target_date
        )
        return 0

    connection = connect(settings.db_path)
    processed_events = 0
    try:
        initialize_schema(connection)

        for parsed_event in parsed_events:
            try:
                upsert_event(
                    connection,
                    Event(
                        security_id=str(parsed_event["security_id"]),
                        company_name=str(parsed_event["company_name"]),
                        event_date=str(parsed_event["event_date"]),
                        event_type=str(parsed_event["event_type"]),
                        source_url=parsed_event.get("source_url"),
                    ),
                )
                processed_events += 1
            except Exception:
                logger.exception("Failed to upsert event: %s", parsed_event)
                continue
    finally:
        connection.close()

    return processed_events
