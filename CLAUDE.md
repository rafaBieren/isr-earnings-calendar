# CLAUDE.md

## Project
ISR Earnings Calendar — automated ICS feed generator for Israeli earnings events scraped from Maya (TASE corporate actions platform). Aggregates earnings reports, conference calls, and public offerings; exposes them as a calendar feed at `GET /calendar`. Also supports a Telegram webhook that uses Gemini to extract IR meeting details from messages/images.

## Stack
- Python 3.11+, FastAPI, Uvicorn
- SQLite (built-in, file at `ISR_EARNINGS_DB_PATH`)
- APScheduler (cron-style jobs in `Asia/Jerusalem` timezone)
- icalendar (RFC 5545 output)
- google-genai (Gemini `gemini-2.5-flash`, structured JSON output)
- requests + beautifulsoup4 (Maya scraping + URL context extraction)
- resend (email alerts on scraper failure)
- pytest, black (line length 88), flake8

## Architecture (one-liner per module)
- [src/isr_earnings_calendar/main.py](src/isr_earnings_calendar/main.py) — Uvicorn entry point; ensures DB dir, loads settings, runs on `$PORT` (default 8000)
- [src/isr_earnings_calendar/config.py](src/isr_earnings_calendar/config.py) — fail-fast env var loading via frozen dataclass; raises `MissingEnvironmentVariableError`
- [src/isr_earnings_calendar/db.py](src/isr_earnings_calendar/db.py) — SQLite schema bootstrap, idempotent `UPSERT`, `smart_merge_event()` for merging IR events
- [src/isr_earnings_calendar/scraper.py](src/isr_earnings_calendar/scraper.py) — Maya API client: `fetch_maya_reports()`, `fetch_open_offerings()`; handles pagination + AM/PM → ISO time normalization
- [src/isr_earnings_calendar/sync.py](src/isr_earnings_calendar/sync.py) — orchestrates sync jobs; called from scheduler and on app startup
- [src/isr_earnings_calendar/api.py](src/isr_earnings_calendar/api.py) — FastAPI app: `GET /calendar` (ICS), `POST /telegram/webhook` (real-time IR events); APScheduler lifespan hooks
- [src/isr_earnings_calendar/agent.py](src/isr_earnings_calendar/agent.py) — Gemini agent that extracts structured event details from Telegram text/images + URL scraping
- [src/isr_earnings_calendar/notifier.py](src/isr_earnings_calendar/notifier.py) — Resend email alert on sync failure (no-op if `RESEND_API_KEY`/`ALERT_EMAIL` missing)

## Environment variables
Required (fail-fast):
- `ISR_EARNINGS_DB_PATH` — e.g. `./tmp/isr_earnings.db`
- `ISR_EARNINGS_MAYA_BASE_URL` — e.g. `https://maya.tase.co.il`

Optional:
- `TELEGRAM_BOT_TOKEN` — Telegram bot webhook replies
- `GEMINI_API_KEY` — required if Telegram agent is in use
- `RESEND_API_KEY` + `ALERT_EMAIL` — error notifications
- `PORT` — server port (default 8000)

## Operating rules
@AGENTS.md

Additional Claude-specific rules:
- **Hebrew strings**: event type labels (`פרסום דוחות`, `שיחת ועידה`, etc.) and user-facing text are in Hebrew. Always preserve UTF-8. Never normalize or romanize.
- **Timezone**: all scheduling logic uses `Asia/Jerusalem` via `pytz`. Never use naive datetimes for cron triggers.
- **DB UNIQUE invariant**: `(security_id, event_date, event_type)` is the dedup key. Do not break it without explicit migration.
- **Exploration scripts**: `tmp/recon_*.py` and `tmp/agent_lab.py` are scratch — **not** production code. Don't refactor them into the package.

## Quality gates (must pass before commit)
```
python -m black .
python -m flake8
python -m pytest
```

## Run locally
```
python src/isr_earnings_calendar/main.py
```
Server: http://localhost:8000 — calendar feed at `/calendar`.

## Gotchas
- Cloud deploy (Railway) uses `PYTHONPATH=src` in [Procfile](Procfile) to bypass a build cache issue with editable installs. Don't remove it.
- Known fixed bug: ICS `DTEND` was being duplicated (commit c9ffdd9). If you touch `api.py` event formatting, run the [ics-feed-tester](.claude/agents/ics-feed-tester.md) sub-agent.
- When the Maya API shape changes, run the [maya-scraper-validator](.claude/agents/maya-scraper-validator.md) sub-agent before pushing.
