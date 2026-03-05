from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Response
from icalendar import Calendar, Event as IcsEvent
import pytz

from .db import get_all_events
from .sync import sync_offerings_job, sync_reports_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Jerusalem"))
    scheduler.add_job(sync_reports_job, "cron", hour=7, minute=0)
    scheduler.add_job(sync_offerings_job, "cron", hour=20, minute=0)
    scheduler.start()

    sync_reports_job()
    sync_offerings_job()

    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


def _parse_event_date(value: str) -> date | datetime:
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        return date.fromisoformat(value)
    except ValueError:
        return date.today()


@app.get("/calendar")
def get_calendar() -> Response:
    events = get_all_events()
    earnings_by_date: dict[str, list[str]] = {}
    other_events: list[dict[str, object]] = []

    for event in events:
        event_type = str(event.get("event_type", ""))
        event_date = str(event.get("event_date", ""))
        date_key = event_date.split("T")[0] if event_date else ""

        if event_type == "פרסום דוחות" and date_key:
            company_name = str(event.get("company_name", "Unknown Company"))
            earnings_by_date.setdefault(date_key, []).append(company_name)
            continue

        other_events.append(event)

    calendar = Calendar()
    calendar.add("prodid", "-//ISR Earnings Calendar//")
    calendar.add("version", "2.0")

    for date_str, companies in earnings_by_date.items():
        calendar_event = IcsEvent()
        calendar_event.add(
            "summary", f"דוחות להיום ({len(companies)}): {', '.join(companies)}"
        )
        calendar_event.add("dtstart", date.fromisoformat(date_str))
        calendar_event.add("description", "\n".join(companies))
        calendar_event.add("uid", f"earnings-{date_str}@isr-earnings")
        calendar.add_component(calendar_event)

    for event in other_events:
        company_name = str(event.get("company_name", "Unknown Company"))
        event_type = str(event.get("event_type", "event"))
        event_date = str(event.get("event_date", ""))
        end_date = str(event.get("end_date") or "")
        security_id = str(event.get("security_id", "unknown"))
        report_url = str(event.get("report_url") or "").strip()
        source_url = str(event.get("source_url") or "")

        dtstart_val = _parse_event_date(event_date)
        calendar_event = IcsEvent()
        calendar_event.add("summary", f"{company_name} - {event_type}")
        calendar_event.add("dtstart", dtstart_val)
        if end_date:
            calendar_event.add("dtend", _parse_event_date(end_date))
        elif isinstance(dtstart_val, datetime):
            calendar_event.add("dtend", dtstart_val + timedelta(minutes=30))
        calendar_event.add(
            "uid", f"{security_id}-{event_date}-{event_type}@isr-earnings"
        )
        desc_lines = []
        if report_url:
            desc_lines.append(f"קישור לדיווח במאיה: {report_url}")
        if source_url:
            desc_lines.append(f"מקור: {source_url}")
        description = "\n\n".join(desc_lines)
        calendar_event.add("description", description)

        calendar.add_component(calendar_event)

    return Response(content=calendar.to_ical(), media_type="text/calendar")
