from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Response
from icalendar import Calendar, Event as IcsEvent

from .db import get_all_events
from .sync import sync_maya_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_maya_events, "cron", hour=8, minute=0)
    sync_maya_events()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title="ISR Earnings Calendar API", lifespan=lifespan)


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

    calendar = Calendar()
    calendar.add("prodid", "-//ISR Earnings Calendar//")
    calendar.add("version", "2.0")

    for event in events:
        company_name = str(event.get("company_name", "Unknown Company"))
        event_type = str(event.get("event_type", "event"))
        event_date = str(event.get("event_date", ""))
        security_id = str(event.get("security_id", "unknown"))
        source_url = event.get("source_url")

        calendar_event = IcsEvent()
        calendar_event.add("summary", f"{company_name} - {event_type}")
        calendar_event.add("dtstart", _parse_event_date(event_date))
        calendar_event.add(
            "uid", f"{security_id}-{event_date}-{event_type}@isr-earnings"
        )
        if source_url:
            calendar_event.add("description", str(source_url))

        calendar.add_component(calendar_event)

    return Response(content=calendar.to_ical(), media_type="text/calendar")
