from __future__ import annotations

import logging
from datetime import date as datetime_date

from .config import load_settings
from .db import Event, connect, initialize_schema, save_events_to_db, upsert_event
from .notifier import send_error_email
from .scraper import fetch_maya_reports, parse_maya_reports, fetch_open_offerings

logger = logging.getLogger(__name__)


def sync_reports_job() -> None:
    print("Running reports sync job...")
    try:
        raw_reports = fetch_maya_reports()
        parsed_reports = parse_maya_reports(raw_reports)
        save_events_to_db(parsed_reports)
        print(f"Successfully synced {len(parsed_reports)} reports.")
    except Exception as e:
        error_str = str(e)
        print(f"Error in reports sync job: {error_str}")
        send_error_email("Reports Sync", error_str)


def sync_offerings_job() -> None:
    print("Running offerings sync job...")
    try:
        offerings = fetch_open_offerings()
        save_events_to_db(offerings)
        print(f"Successfully synced {len(offerings)} offerings.")
    except Exception as e:
        error_str = str(e)
        print(f"Error in offerings sync job: {error_str}")
        send_error_email("Offerings Sync", error_str)


def sync_maya_events(date: str | None = None) -> int:
    target_date = date or datetime_date.today().isoformat()
    settings = load_settings()

    try:
        raw_data = fetch_maya_reports(target_date)
        parsed_events = parse_maya_reports(raw_data)
        offerings = fetch_open_offerings()
    except Exception:
        logger.exception(
            "Failed to fetch or parse Maya reports for date=%s", target_date
        )
        return 0

    connection = connect(settings.db_path)
    processed_events = 0
    try:
        initialize_schema(connection)

        all_events = [*parsed_events, *offerings]
        for parsed_event in all_events:
            try:
                upsert_event(
                    connection,
                    Event(
                        security_id=str(parsed_event["security_id"]),
                        company_name=str(parsed_event["company_name"]),
                        event_date=str(parsed_event["event_date"]),
                        event_type=str(parsed_event["event_type"]),
                        description=(
                            str(parsed_event["description"])
                            if parsed_event.get("description") is not None
                            else None
                        ),
                        end_date=(
                            str(parsed_event["end_date"])
                            if parsed_event.get("end_date")
                            else None
                        ),
                        source_url=parsed_event.get("source_url"),
                        report_url=parsed_event.get("report_url"),
                    ),
                )
                processed_events += 1
            except Exception:
                logger.exception("Failed to upsert event: %s", parsed_event)
                continue
    finally:
        connection.close()

    return processed_events


if __name__ == "__main__":
    sync_reports_job()
    sync_offerings_job()
