from __future__ import annotations

import os
import urllib.parse
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from icalendar import Calendar, Event as IcsEvent

from .agent import process_ir_message
from .db import get_all_events, smart_merge_event
from .sync import sync_offerings_job, sync_reports_job

_PACKAGE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _PACKAGE_DIR / "templates"
_STATIC_DIR = _PACKAGE_DIR / "static"

EARNINGS_EVENT_TYPE = "\u05e4\u05e8\u05e1\u05d5\u05dd \u05d3\u05d5\u05d7\u05d5\u05ea"
EARNINGS_SUMMARY = "\u05d3\u05d5\u05d7\u05d5\u05ea \u05dc\u05d4\u05d9\u05d5\u05dd"
REPORT_URL_LABEL = (
    "\u05e7\u05d9\u05e9\u05d5\u05e8 "
    "\u05dc\u05d3\u05d9\u05d5\u05d5\u05d7 \u05d1\u05de\u05d0\u05d9\u05d4"
)
SOURCE_URL_LABEL = "\u05de\u05e7\u05d5\u05e8"
DEFAULT_IR_EVENT_TYPE = (
    "\u05d0\u05d9\u05e8\u05d5\u05e2 \u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd"
)
PHOTO_PROCESSING_MESSAGE = (
    "\u23f3 \u05de\u05d5\u05e8\u05d9\u05d3 \u05ea\u05de\u05d5\u05e0\u05d4 "
    "\u05d5\u05de\u05e2\u05d1\u05d3 \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd..."
)
NO_CONTENT_MESSAGE = (
    "\u274c \u05dc\u05d0 \u05d6\u05d5\u05d4\u05d4 \u05d8\u05e7\u05e1\u05d8 "
    "\u05d0\u05d5 \u05ea\u05de\u05d5\u05e0\u05d4 "
    "\u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9\u05d9\u05dd."
)
TEXT_PROCESSING_MESSAGE = (
    "\u23f3 \u05de\u05e2\u05d1\u05d3 \u05d0\u05ea \u05d4\u05d4\u05d5\u05d3\u05e2\u05d4 "
    "\u05de\u05d5\u05dc \u05d4-AI..."
)
AI_FAILURE_MESSAGE = (
    "\u274c \u05e9\u05d2\u05d9\u05d0\u05d4: "
    "\u05dc\u05d0 \u05d4\u05e6\u05dc\u05d7\u05ea\u05d9 "
    "\u05dc\u05e2\u05d1\u05d3 \u05d0\u05ea \u05d4\u05d4\u05d5\u05d3\u05e2\u05d4 "
    "\u05de\u05d5\u05dc \u05d4-AI."
)
IRRELEVANT_MESSAGE = (
    "\u2139\ufe0f \u05d4\u05d4\u05d5\u05d3\u05e2\u05d4 "
    "\u05dc\u05d0 \u05d6\u05d5\u05d4\u05ea\u05d4 "
    "\u05db\u05d4\u05d6\u05de\u05e0\u05d4 "
    "\u05dc\u05d0\u05d9\u05e8\u05d5\u05e2 \u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd "
    "("
    "\u05d4\u05d9\u05d0 \u05e1\u05d5\u05e0\u05e0\u05d4 \u05d4\u05d7\u05d5\u05e6\u05d4)."
)
MISSING_REQUIRED_MESSAGE = (
    "\u26a0\ufe0f \u05d6\u05d9\u05d4\u05d9\u05ea\u05d9 \u05d0\u05d9\u05e8\u05d5\u05e2, "
    "\u05d0\u05d1\u05dc \u05d7\u05e1\u05e8\u05d9\u05dd "
    "\u05dc\u05d9 \u05e4\u05e8\u05d8\u05d9 \u05d7\u05d5\u05d1\u05d4 "
    "("
    "\u05e9\u05dd \u05d7\u05d1\u05e8\u05d4 "
    "\u05d0\u05d5 \u05ea\u05d0\u05e8\u05d9\u05da)."
)
ZOOM_LINK_LABEL = (
    "\u05e7\u05d9\u05e9\u05d5\u05e8 "
    "\u05dc\u05d6\u05d5\u05dd/\u05e4\u05d2\u05d9\u05e9\u05d4"
)
PASSWORD_LABEL = "\u05e1\u05d9\u05e1\u05de\u05d4"
LOCATION_LABEL = "\u05de\u05d9\u05e7\u05d5\u05dd"
SUCCESS_MESSAGE_PREFIX = (
    "\u2705 \u05de\u05e2\u05d5\u05dc\u05d4! \u05d4\u05d0\u05d9\u05e8\u05d5\u05e2 "
    "\u05e9\u05dc "
)
SUCCESS_MESSAGE_SUFFIX = (
    "\u05e2\u05d5\u05d3\u05db\u05df/\u05e0\u05d5\u05e1\u05e3 "
    "\u05dc\u05d9\u05d5\u05de\u05df \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4."
)
DB_SAVE_ERROR_PREFIX = (
    "\u274c \u05e9\u05d2\u05d9\u05d0\u05d4 "
    "\u05d1\u05e9\u05de\u05d9\u05e8\u05d4 "
    "\u05dc\u05de\u05e1\u05d3 \u05d4\u05e0\u05ea\u05d5\u05e0\u05d9\u05dd: "
)


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


def send_telegram_reply(chat_id: int, text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as exc:
        print(f"Failed to send Telegram reply: {exc}")


def download_telegram_file(file_id: str) -> bytes | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return None

    try:
        file_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
        response = requests.get(file_url, timeout=10).json()
        if not response.get("ok"):
            return None

        file_path = response["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        file_response = requests.get(download_url, timeout=15)
        return file_response.content if file_response.status_code == 200 else None
    except Exception:
        return None


def process_telegram_update(update_data: dict[str, object]) -> None:
    message = update_data.get("message", {})
    if not isinstance(message, dict):
        return

    chat = message.get("chat", {})
    if not isinstance(chat, dict):
        return

    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    text = message.get("text") or message.get("caption") or ""

    image_bytes = None
    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        largest_photo = photos[-1]
        if isinstance(largest_photo, dict):
            file_id = largest_photo.get("file_id")
            if isinstance(file_id, str) and file_id:
                send_telegram_reply(chat_id, PHOTO_PROCESSING_MESSAGE)
                image_bytes = download_telegram_file(file_id)

    if not text and not image_bytes:
        send_telegram_reply(chat_id, NO_CONTENT_MESSAGE)
        return

    if not image_bytes:
        send_telegram_reply(chat_id, TEXT_PROCESSING_MESSAGE)

    try:
        ir_event = process_ir_message(str(text), image_bytes)
    except Exception as exc:
        send_telegram_reply(chat_id, AI_FAILURE_MESSAGE)
        print(f"Telegram AI processing failed: {exc}")
        return

    if not ir_event:
        send_telegram_reply(chat_id, AI_FAILURE_MESSAGE)
        return

    if not ir_event.is_relevant:
        send_telegram_reply(chat_id, IRRELEVANT_MESSAGE)
        return

    if not ir_event.company_name or not ir_event.start_datetime:
        send_telegram_reply(chat_id, MISSING_REQUIRED_MESSAGE)
        return

    description_lines: list[str] = []
    if ir_event.zoom_link:
        description_lines.append(f"{ZOOM_LINK_LABEL}: {ir_event.zoom_link}")
    if ir_event.password:
        description_lines.append(f"{PASSWORD_LABEL}: {ir_event.password}")
    if ir_event.location:
        description_lines.append(f"{LOCATION_LABEL}: {ir_event.location}")

    event_payload = {
        "company_name": ir_event.company_name,
        "event_type": ir_event.event_type or DEFAULT_IR_EVENT_TYPE,
        "event_date": ir_event.start_datetime,
        "end_date": ir_event.end_datetime,
        "description": "\n".join(description_lines),
    }

    try:
        smart_merge_event(event_payload)
        send_telegram_reply(
            chat_id,
            f"{SUCCESS_MESSAGE_PREFIX}'{ir_event.company_name}' "
            f"\u05d1-{ir_event.start_datetime[:10]} {SUCCESS_MESSAGE_SUFFIX}",
        )
    except Exception as exc:
        send_telegram_reply(chat_id, f"{DB_SAVE_ERROR_PREFIX}{exc}")


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Receives updates from Telegram and processes them in the background."""
    try:
        update_data = await request.json()
        background_tasks.add_task(process_telegram_update, update_data)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _parse_event_date(value: str) -> date | datetime:
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        return date.fromisoformat(value)
    except ValueError:
        return date.today()


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    uid: str
    summary: str
    start: date | datetime
    end: date | datetime | None
    all_day: bool
    description: str
    event_type: str
    company_name: str
    source_url: str
    report_url: str


def _build_calendar_events(
    rows: list[dict[str, object]],
) -> list[CalendarEvent]:
    """Canonical event list shared by /calendar (ICS) and /api/events (JSON).

    Same-day earnings reports are grouped into one all-day event so the web
    view stays in sync with what subscribers see in Outlook/Google.
    """
    earnings_by_date: dict[str, list[str]] = {}
    other_rows: list[dict[str, object]] = []

    for event in rows:
        event_type = str(event.get("event_type", ""))
        event_date = str(event.get("event_date", ""))
        date_key = event_date.split("T")[0] if event_date else ""

        if event_type == EARNINGS_EVENT_TYPE and date_key:
            company_name = str(event.get("company_name", "Unknown Company"))
            earnings_by_date.setdefault(date_key, []).append(company_name)
            continue

        other_rows.append(event)

    result: list[CalendarEvent] = []

    for date_str, companies in earnings_by_date.items():
        result.append(
            CalendarEvent(
                uid=f"earnings-{date_str}@isr-earnings",
                summary=(
                    f"{EARNINGS_SUMMARY} ({len(companies)}): " f"{', '.join(companies)}"
                ),
                start=date.fromisoformat(date_str),
                end=None,
                all_day=True,
                description="\n".join(companies),
                event_type=EARNINGS_EVENT_TYPE,
                company_name=", ".join(companies),
                source_url="",
                report_url="",
            )
        )

    for event in other_rows:
        company_name = str(event.get("company_name", "Unknown Company"))
        event_type = str(event.get("event_type", "event"))
        event_date = str(event.get("event_date", ""))
        end_date_str = str(event.get("end_date") or "")
        security_id = str(event.get("security_id", "unknown"))
        report_url = str(event.get("report_url") or "").strip()
        source_url = str(event.get("source_url") or "")

        dtstart_val = _parse_event_date(event_date)
        all_day = not isinstance(dtstart_val, datetime)

        end_val: date | datetime | None
        if end_date_str:
            end_val = _parse_event_date(end_date_str)
        elif isinstance(dtstart_val, datetime):
            end_val = dtstart_val + timedelta(minutes=30)
        else:
            end_val = None

        description_lines: list[str] = []
        db_description = str(event.get("description") or "").strip()
        if db_description:
            description_lines.append(db_description)
        if report_url:
            description_lines.append(f"{REPORT_URL_LABEL}: {report_url}")
        if source_url:
            description_lines.append(f"{SOURCE_URL_LABEL}: {source_url}")

        result.append(
            CalendarEvent(
                uid=f"{security_id}-{event_date}-{event_type}@isr-earnings",
                summary=f"{company_name} - {event_type}",
                start=dtstart_val,
                end=end_val,
                all_day=all_day,
                description="\n\n".join(description_lines),
                event_type=event_type,
                company_name=company_name,
                source_url=source_url,
                report_url=report_url,
            )
        )

    return result


@app.get("/calendar")
def get_calendar() -> Response:
    events = _build_calendar_events(get_all_events())

    calendar = Calendar()
    calendar.add("prodid", "-//ISR Earnings Calendar//")
    calendar.add("version", "2.0")

    for ev in events:
        ics_event = IcsEvent()
        ics_event.add("summary", ev.summary)
        ics_event.add("dtstart", ev.start)
        if ev.end is not None:
            ics_event.add("dtend", ev.end)
        ics_event.add("uid", ev.uid)
        ics_event.add("description", ev.description)
        calendar.add_component(ics_event)

    return Response(content=calendar.to_ical(), media_type="text/calendar")


def _event_to_fullcalendar(ev: CalendarEvent) -> dict[str, object]:
    return {
        "id": ev.uid,
        "title": ev.summary,
        "start": ev.start.isoformat(),
        "end": ev.end.isoformat() if ev.end is not None else None,
        "allDay": ev.all_day,
        "extendedProps": {
            "event_type": ev.event_type,
            "company_name": ev.company_name,
            "description": ev.description,
            "source_url": ev.source_url,
            "report_url": ev.report_url,
        },
    }


@app.get("/api/events")
def get_events_json() -> list[dict[str, object]]:
    events = _build_calendar_events(get_all_events())
    return [_event_to_fullcalendar(ev) for ev in events]


def _build_subscribe_urls(request: Request) -> dict[str, str]:
    base = str(request.base_url).rstrip("/")
    ics_url = f"{base}/calendar"
    webcal_url = ics_url
    for scheme in ("https://", "http://"):
        if webcal_url.startswith(scheme):
            webcal_url = "webcal://" + webcal_url[len(scheme) :]
            break
    google_url = "https://calendar.google.com/calendar/r?cid=" + urllib.parse.quote(
        webcal_url, safe=""
    )
    return {
        "ics_url": ics_url,
        "webcal_url": webcal_url,
        "google_url": google_url,
    }


@app.get("/view", response_class=HTMLResponse)
def calendar_view(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="calendar.html",
        context=_build_subscribe_urls(request),
    )
